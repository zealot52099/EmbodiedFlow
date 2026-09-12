"""Evaluate a pi0.5 policy in LIBERO with injected MuJoCo obstacles.

This runner is intentionally small and local to the project. It reuses the
existing LeRobot LIBERO wrapper and eval loop, but swaps in an environment
subclass that modifies the MuJoCo XML before rollout and reports simple
robot-obstacle contact telemetry.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import torch


LEROBOT_SRC = Path("E:/projects/lerobot_experiment/lerobot/src")
if str(LEROBOT_SRC) not in sys.path:
    sys.path.insert(0, str(LEROBOT_SRC))

from lerobot.configs.policies import PreTrainedConfig  # noqa: E402
from lerobot.envs.configs import LiberoEnv as LiberoEnvConfig  # noqa: E402
from lerobot.envs import preprocess_observation  # noqa: E402
from lerobot.envs.factory import make_env_pre_post_processors  # noqa: E402
from lerobot.envs.libero import LiberoEnv, _get_suite, get_libero_dummy_action  # noqa: E402
from lerobot.envs.utils import NEW_ROLLOUT_OPTION  # noqa: E402
from lerobot.policies import make_policy, make_pre_post_processors  # noqa: E402
from lerobot.utils.constants import ACTION  # noqa: E402
from lerobot.utils.device_utils import get_safe_torch_device  # noqa: E402
from lerobot.utils.io_utils import write_video  # noqa: E402
from lerobot.utils.random_utils import set_seed  # noqa: E402

from libero_obstacle_xml_injector import inject_obstacles_into_xml  # noqa: E402


LOGGER = logging.getLogger("eval_pi05_libero_obstacle")


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.item() if value.size == 1 else value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _model_xml(sim: Any) -> str:
    model = sim.model
    getter = getattr(model, "get_xml", None)
    if callable(getter):
        return getter()
    save = getattr(model, "save", None)
    if callable(save):
        raise RuntimeError("MuJoCo model exposes save(), but this runner needs in-memory XML export.")
    raise RuntimeError(f"Cannot export XML from sim model type {type(model)!r}.")


class ObstacleLiberoEnv(LiberoEnv):
    def __init__(self, *args: Any, obstacle_scenario: dict[str, Any], **kwargs: Any) -> None:
        self.obstacle_scenario = obstacle_scenario
        self.obstacle_geom_prefix = f"avoidance_{obstacle_scenario['scenario_id']}"
        self.obstacle_geom_names: list[str] = []
        self.robot_contact_geoms: set[str] = set()
        self._last_obstacle_contacts: list[dict[str, str]] = []
        self._last_min_clearance: dict[str, Any] | None = None
        self._base_xml_text: str | None = None
        super().__init__(*args, **kwargs)

    def _ensure_env(self) -> None:
        super()._ensure_env()
        if self._env is None or self._base_xml_text is not None:
            return
        self._base_xml_text = _model_xml(self._env.env.sim)

    def _inject_obstacles(self) -> None:
        assert self._env is not None
        if self._base_xml_text is None:
            self._base_xml_text = _model_xml(self._env.env.sim)
        injected = inject_obstacles_into_xml(self._base_xml_text, self.obstacle_scenario)
        self._env.reset_from_xml_string(injected)
        self.obstacle_geom_names = [
            name
            for name in self._env.env.sim.model.geom_names
            if str(name).startswith(self.obstacle_geom_prefix)
        ]
        robot_geoms = getattr(self._env.robots[0].robot_model, "contact_geoms", [])
        self.robot_contact_geoms = {str(name) for name in robot_geoms}
        self._env.env.sim.forward()

    def reset(self, seed=None, **kwargs):
        self._ensure_env()
        assert self._env is not None
        gym.Env.reset(self, seed=seed)
        self._env.seed(seed)
        self._env.reset()
        self._inject_obstacles()
        if self.init_states and self._init_states is not None:
            raw_obs = self._env.set_init_state(self._init_states[self.init_state_id % len(self._init_states)])
            self.init_state_id += self._reset_stride
        else:
            raw_obs = self._env.env._get_observations()

        for _ in range(self.num_steps_wait):
            raw_obs, _, _, _ = self._env.step(get_libero_dummy_action())

        if self.control_mode == "absolute":
            for robot in self._env.robots:
                robot.controller.use_delta = False
        elif self.control_mode == "relative":
            for robot in self._env.robots:
                robot.controller.use_delta = True
        else:
            raise ValueError(f"Invalid control mode: {self.control_mode}")

        observation = self._format_raw_obs(raw_obs)
        return observation, {"is_success": False, "obstacle_scenario_id": self.obstacle_scenario["scenario_id"]}

    def _collect_obstacle_contacts(self) -> list[dict[str, str]]:
        assert self._env is not None
        contacts: list[dict[str, str]] = []
        sim = self._env.env.sim
        obstacle_geoms = set(self.obstacle_geom_names)
        for contact in sim.data.contact[: sim.data.ncon]:
            g1 = str(sim.model.geom_id2name(contact.geom1))
            g2 = str(sim.model.geom_id2name(contact.geom2))
            robot_obstacle = (
                (g1 in self.robot_contact_geoms and g2 in obstacle_geoms)
                or (g2 in self.robot_contact_geoms and g1 in obstacle_geoms)
            )
            if robot_obstacle:
                contacts.append({"robot_geom": g1 if g1 in self.robot_contact_geoms else g2, "obstacle_geom": g2 if g2 in obstacle_geoms else g1})
        self._last_obstacle_contacts = contacts
        return contacts

    def _geom_id(self, name: str) -> int | None:
        assert self._env is not None
        try:
            return int(self._env.env.sim.model.geom_name2id(name))
        except Exception:
            return None

    def _collect_min_clearance(self) -> dict[str, Any] | None:
        """Return conservative robot-obstacle surface clearance from geom bounds.

        MuJoCo contact gives exact collision events, but for near misses this
        runner records a stable proxy: center distance minus each geom's
        bounding radius. Negative values indicate overlapping bounds, not
        necessarily penetrated collision geometry.
        """
        assert self._env is not None
        sim = self._env.env.sim
        geom_rbound = getattr(sim.model, "geom_rbound", None)
        geom_xpos = getattr(sim.data, "geom_xpos", None)
        if geom_rbound is None or geom_xpos is None:
            return None

        best: dict[str, Any] | None = None
        obstacle_names = list(self.obstacle_geom_names)
        robot_names = sorted(self.robot_contact_geoms)
        for robot_name in robot_names:
            robot_id = self._geom_id(robot_name)
            if robot_id is None:
                continue
            for obstacle_name in obstacle_names:
                obstacle_id = self._geom_id(obstacle_name)
                if obstacle_id is None:
                    continue
                center_distance = float(np.linalg.norm(geom_xpos[robot_id] - geom_xpos[obstacle_id]))
                clearance = center_distance - float(geom_rbound[robot_id]) - float(geom_rbound[obstacle_id])
                if best is None or clearance < best["clearance_m"]:
                    best = {
                        "clearance_m": clearance,
                        "center_distance_m": center_distance,
                        "robot_geom": robot_name,
                        "obstacle_geom": obstacle_name,
                    }

        self._last_min_clearance = best
        return best

    def step(self, action: np.ndarray):
        observation, reward, terminated, truncated, info = super().step(action)
        contacts = self._collect_obstacle_contacts()
        clearance = self._collect_min_clearance()
        info.update(
            {
                "obstacle_scenario_id": self.obstacle_scenario["scenario_id"],
                "obstacle_contact_count": len(contacts),
                "obstacle_contacts": contacts,
                "obstacle_geom_names": list(self.obstacle_geom_names),
                "obstacle_min_clearance_m": None if clearance is None else clearance["clearance_m"],
                "obstacle_min_clearance_pair": clearance,
            }
        )
        return observation, reward, terminated, truncated, info


def select_scenarios(curriculum: dict[str, Any], task_ids: set[int], difficulties: set[str], limit: int) -> list[dict[str, Any]]:
    scenarios = [
        scenario
        for scenario in curriculum.get("scenarios", [])
        if int(scenario.get("task_id")) in task_ids and str(scenario.get("difficulty")) in difficulties
    ]
    return scenarios[:limit] if limit > 0 else scenarios


def make_single_env(scenario: dict[str, Any], env_cfg: LiberoEnvConfig) -> gym.vector.SyncVectorEnv:
    suite = _get_suite(scenario["task_group"])
    task_id = int(scenario["task_id"])

    def _make() -> ObstacleLiberoEnv:
        return ObstacleLiberoEnv(
            task_suite=suite,
            task_id=task_id,
            task_suite_name=scenario["task_group"],
            camera_name=env_cfg.camera_name,
            obs_type=env_cfg.obs_type,
            render_mode=env_cfg.render_mode,
            init_states=env_cfg.init_states,
            episode_length=env_cfg.episode_length,
            episode_index=0,
            n_envs=1,
            control_mode=env_cfg.control_mode,
            camera_name_mapping=env_cfg.camera_name_mapping,
            observation_height=env_cfg.observation_height,
            observation_width=env_cfg.observation_width,
            hard_reset=env_cfg.hard_reset,
            obstacle_scenario=scenario,
        )

    return gym.vector.SyncVectorEnv([_make], autoreset_mode=gym.vector.AutoresetMode.NEXT_STEP)


def _first_info_value(info: dict[str, Any], key: str, default: Any = None) -> Any:
    value = info.get(key, default)
    if isinstance(value, dict):
        return {
            nested_key: _first_nested_value(nested_value)
            for nested_key, nested_value in value.items()
            if not str(nested_key).startswith("_")
        }
    if isinstance(value, np.ndarray):
        if not value.size:
            return default
        first = value[0]
        return first.item() if isinstance(first, np.generic) else first
    if isinstance(value, (list, tuple)):
        return value[0] if value else default
    return value


def _first_nested_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            nested_key: _first_nested_value(nested_value)
            for nested_key, nested_value in value.items()
            if not str(nested_key).startswith("_")
        }
    if isinstance(value, np.ndarray):
        if not value.size:
            return None
        first = value[0]
        return first.item() if isinstance(first, np.generic) else first
    if isinstance(value, np.generic):
        return value.item()
    return value


def _task_descriptions(env: gym.vector.SyncVectorEnv) -> list[str]:
    try:
        return list(env.call("task_description"))
    except (AttributeError, NotImplementedError):
        try:
            return list(env.call("task"))
        except (AttributeError, NotImplementedError):
            return [""] * env.num_envs


def run_obstacle_rollout(
    *,
    env: gym.vector.SyncVectorEnv,
    policy: Any,
    env_preprocessor: Any,
    env_postprocessor: Any,
    preprocessor: Any,
    postprocessor: Any,
    seed: int,
    video_path: Path,
) -> dict[str, Any]:
    policy.reset()
    observation, _ = env.reset(seed=[seed], options={NEW_ROLLOUT_OPTION: True})
    frames = [env.envs[0].render()]
    rewards: list[float] = []
    contact_counts: list[int] = []
    contact_events: list[dict[str, Any]] = []
    clearance_samples: list[float] = []
    min_clearance: dict[str, Any] | None = None
    success = False
    done = False
    max_steps = int(env.call("_max_episode_steps")[0])

    step = 0
    while not done and step < max_steps:
        policy_obs = preprocess_observation(observation)
        policy_obs["task"] = _task_descriptions(env)
        policy_obs = env_preprocessor(policy_obs)
        policy_obs = preprocessor(policy_obs)
        with torch.inference_mode():
            action = policy.select_action(policy_obs)
        action = postprocessor(action)
        action_transition = env_postprocessor({ACTION: action})
        action_numpy = action_transition[ACTION].to("cpu").numpy()

        observation, reward, terminated, truncated, info = env.step(action_numpy)
        frames.append(env.envs[0].render())
        rewards.append(float(reward[0]))

        contact_count = int(_first_info_value(info, "obstacle_contact_count", 0))
        contact_counts.append(contact_count)
        if contact_count:
            contact_events.append(
                {
                    "step": step,
                    "contacts": _first_info_value(info, "obstacle_contacts", []),
                }
            )
        clearance_value = _first_info_value(info, "obstacle_min_clearance_m", None)
        if clearance_value is not None:
            clearance_float = float(clearance_value)
            clearance_samples.append(clearance_float)
            if min_clearance is None or clearance_float < min_clearance["clearance_m"]:
                min_clearance = dict(_first_info_value(info, "obstacle_min_clearance_pair", {}) or {})
                min_clearance["step"] = step

        success = bool(_first_info_value(info, "is_success", success))
        if "final_info" in info:
            final_info = info["final_info"][0] if isinstance(info["final_info"], np.ndarray) else info["final_info"]
            if isinstance(final_info, dict) and "is_success" in final_info:
                success = bool(final_info["is_success"])

        done = bool(terminated[0] or truncated[0])
        step += 1

    video_path.parent.mkdir(parents=True, exist_ok=True)
    write_video(str(video_path), np.stack(frames), fps=int(env.envs[0].metadata.get("render_fps", 20)))
    return {
        "sum_reward": float(sum(rewards)),
        "max_reward": float(max(rewards) if rewards else 0.0),
        "success": success,
        "steps": step,
        "collision_count": int(sum(1 for value in contact_counts if value > 0)),
        "max_contacts_in_step": int(max(contact_counts) if contact_counts else 0),
        "min_clearance_m": None if min_clearance is None else float(min_clearance["clearance_m"]),
        "min_clearance_pair": min_clearance,
        "mean_clearance_m": float(np.mean(clearance_samples)) if clearance_samples else None,
        "contact_events": contact_events,
        "video_path": str(video_path),
    }


def clearance_margin_m(scenario: dict[str, Any]) -> float:
    margins = [
        float(obstacle.get("clearance_margin_m", 0.0))
        for obstacle in scenario.get("obstacles", [])
        if obstacle.get("shape") != "virtual_safety_zone"
    ]
    return max(margins) if margins else 0.0


def summarize_safety(episodes: list[dict[str, Any]], scenario: dict[str, Any]) -> dict[str, Any]:
    successes = [bool(item["success"]) for item in episodes]
    collision_counts = [int(item["collision_count"]) for item in episodes]
    margin = clearance_margin_m(scenario)
    clearances = [item["min_clearance_m"] for item in episodes if item.get("min_clearance_m") is not None]
    safety_successes = [
        int(item["collision_count"]) == 0
        and (item.get("min_clearance_m") is None or float(item["min_clearance_m"]) >= margin)
        for item in episodes
    ]
    avoidance_successes = [bool(item["success"]) and safety for item, safety in zip(episodes, safety_successes)]
    return {
        "scenario_id": scenario["scenario_id"],
        "task_group": scenario["task_group"],
        "task_id": scenario["task_id"],
        "difficulty": scenario["difficulty"],
        "clearance_margin_m": margin,
        "episodes": len(successes),
        "task_successes": sum(1 for value in successes if value),
        "task_success_rate_percent": 100.0 * sum(1 for value in successes if value) / max(len(successes), 1),
        "collision_counts": collision_counts,
        "min_clearance_m": float(min(clearances)) if clearances else None,
        "mean_episode_min_clearance_m": float(np.mean(clearances)) if clearances else None,
        "clearance_violation_count": sum(1 for value in clearances if float(value) < margin),
        "contact_event_count": sum(len(item["contact_events"]) for item in episodes),
        "safety_successes": safety_successes,
        "safety_success_rate_percent": 100.0
        * sum(1 for value in safety_successes if value)
        / max(len(safety_successes), 1),
        "avoidance_successes": avoidance_successes,
        "avoidance_success_rate_percent": 100.0
        * sum(1 for value in avoidance_successes if value)
        / max(len(avoidance_successes), 1),
        "episodes_detail": episodes,
        "video_paths": [item["video_path"] for item in episodes],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy-path", default="outputs/pi05_libero_multitask_4090/checkpoints/030000/pretrained_model")
    parser.add_argument("--curriculum", default="artifacts/grasp_pipeline/runs/obstacle_curriculum_20260911/obstacle_curriculum.json")
    parser.add_argument("--task-ids", default="0")
    parser.add_argument("--difficulties", default="easy")
    parser.add_argument("--scenario-limit", type=int, default=1)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--output-dir", default="eval_logs/pi05_libero_obstacle_smoke")
    parser.add_argument("--seed", type=int, default=3000)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(asctime)s %(name)s:%(lineno)d %(message)s")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    curriculum = json.loads(Path(args.curriculum).read_text(encoding="utf-8"))
    task_ids = {int(value.strip()) for value in args.task_ids.split(",") if value.strip()}
    difficulties = {value.strip() for value in args.difficulties.split(",") if value.strip()}
    scenarios = select_scenarios(curriculum, task_ids, difficulties, args.scenario_limit)
    if not scenarios:
        raise ValueError("No scenarios selected.")

    policy_path = Path(args.policy_path).resolve()
    policy_cfg = PreTrainedConfig.from_pretrained(policy_path)
    policy_cfg.pretrained_path = policy_path
    policy_cfg.device = "cuda"
    device = get_safe_torch_device(policy_cfg.device, log=True)
    set_seed(args.seed)

    env_cfg = LiberoEnvConfig(task="libero_goal", task_ids=sorted(task_ids))
    policy = make_policy(cfg=policy_cfg, env_cfg=env_cfg)
    policy.eval()

    preprocessor_overrides = {
        "device_processor": {"device": str(policy.config.device)},
        "rename_observations_processor": {"rename_map": {}},
    }
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy_cfg,
        pretrained_path=policy_cfg.pretrained_path,
        preprocessor_overrides=preprocessor_overrides,
    )
    env_preprocessor, env_postprocessor = make_env_pre_post_processors(env_cfg=env_cfg, policy_cfg=policy_cfg)

    start = time.time()
    rows = []
    with torch.no_grad(), torch.autocast(device_type=device.type) if policy_cfg.use_amp else nullcontext():
        for scenario in scenarios:
            LOGGER.info("Evaluating obstacle scenario %s", scenario["scenario_id"])
            env = make_single_env(scenario, env_cfg)
            try:
                episodes = []
                for episode_index in range(args.episodes):
                    episodes.append(
                        run_obstacle_rollout(
                            env=env,
                            policy=policy,
                            env_preprocessor=env_preprocessor,
                            env_postprocessor=env_postprocessor,
                            preprocessor=preprocessor,
                            postprocessor=postprocessor,
                            seed=args.seed + episode_index,
                            video_path=output_dir
                            / "videos"
                            / scenario["scenario_id"]
                            / f"eval_episode_{episode_index}.mp4",
                        )
                    )
            finally:
                env.close()
            rows.append(summarize_safety(episodes, scenario))

    total_episodes = sum(row["episodes"] for row in rows)
    total_successes = sum(row["task_successes"] for row in rows)
    all_clearances = [
        episode["min_clearance_m"]
        for row in rows
        for episode in row["episodes_detail"]
        if episode.get("min_clearance_m") is not None
    ]
    report = {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "policy_path": str(policy_path),
        "curriculum": str(Path(args.curriculum).resolve()),
        "overall": {
            "scenario_count": len(rows),
            "n_episodes": total_episodes,
            "task_success_rate_percent": 100.0 * total_successes / max(total_episodes, 1),
            "avoidance_success_rate_percent": 100.0
            * sum(sum(1 for value in row["avoidance_successes"] if value) for row in rows)
            / max(total_episodes, 1),
            "safety_success_rate_percent": 100.0
            * sum(sum(1 for value in row["safety_successes"] if value) for row in rows)
            / max(total_episodes, 1),
            "collision_episode_count": sum(
                sum(1 for value in row["collision_counts"] if value > 0) for row in rows
            ),
            "clearance_violation_count": sum(row["clearance_violation_count"] for row in rows),
            "min_clearance_m": float(min(all_clearances)) if all_clearances else None,
            "mean_episode_min_clearance_m": float(np.mean(all_clearances)) if all_clearances else None,
            "eval_seconds": time.time() - start,
        },
        "per_scenario": rows,
    }
    out = output_dir / "obstacle_eval_summary.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")
    print(f"Wrote obstacle eval summary: {out}")
    print(f"Task success: {report['overall']['task_success_rate_percent']}%")


if __name__ == "__main__":
    main()
