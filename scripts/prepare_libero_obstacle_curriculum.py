"""Create an obstacle-avoidance curriculum spec for LIBERO grasp/place training.

The first obstacle milestone is deliberately metadata-first: it defines
repeatable obstacle layouts, success/safety metrics, and BC/RL curriculum
weights without mutating the installed LIBERO package. A later runner can use
this JSON to inject MuJoCo fixtures or Isaac Sim props and to collect expert
avoidance trajectories.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_TASK_IDS = list(range(10))


OBSTACLE_LEVELS: dict[str, dict[str, Any]] = {
    "easy": {
        "episodes_per_task": 5,
        "obstacle_count": 1,
        "clearance_margin_m": 0.04,
        "layouts": [
            {
                "name": "side_block",
                "shape": "box",
                "size_m": [0.08, 0.08, 0.10],
                "placement": "lateral_to_nominal_pick_path",
                "description": "A small block near the nominal approach path, leaving a direct but narrower route.",
            }
        ],
    },
    "medium": {
        "episodes_per_task": 10,
        "obstacle_count": 2,
        "clearance_margin_m": 0.06,
        "layouts": [
            {
                "name": "corridor_pair",
                "shape": "box",
                "size_m": [0.07, 0.12, 0.12],
                "placement": "two_sides_of_nominal_transfer_path",
                "description": "Two obstacles form a corridor between pick and place regions.",
            },
            {
                "name": "target_guard",
                "shape": "cylinder",
                "size_m": [0.05, 0.12],
                "placement": "near_target_region_not_overlapping_goal",
                "description": "A narrow obstacle close to the placement target tests final approach clearance.",
            },
        ],
    },
    "hard": {
        "episodes_per_task": 10,
        "obstacle_count": 3,
        "clearance_margin_m": 0.08,
        "layouts": [
            {
                "name": "blocked_straight_line",
                "shape": "box",
                "size_m": [0.12, 0.08, 0.14],
                "placement": "center_of_nominal_pick_to_place_line",
                "description": "A central obstacle blocks the straight transfer line and requires an arcing route.",
            },
            {
                "name": "dynamic_reserved_band",
                "shape": "virtual_safety_zone",
                "size_m": [0.18, 0.08, 0.16],
                "placement": "sampled_between_eef_start_and_goal",
                "description": "A reserved no-go band for future dynamic obstacle or second-arm occupancy tests.",
            },
        ],
    },
}


def build_curriculum(task_ids: list[int], seed: int) -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    scenario_id = 0
    for task_id in task_ids:
        for level_name, level in OBSTACLE_LEVELS.items():
            for layout_index, layout in enumerate(level["layouts"]):
                scenarios.append(
                    {
                        "scenario_id": f"libero_goal_{task_id:02d}_{level_name}_{layout_index:02d}",
                        "task_group": "libero_goal",
                        "task_id": task_id,
                        "difficulty": level_name,
                        "seed": seed + scenario_id,
                        "episodes": level["episodes_per_task"],
                        "obstacles": [
                            {
                                "name": layout["name"],
                                "shape": layout["shape"],
                                "size_m": layout["size_m"],
                                "placement_rule": layout["placement"],
                                "clearance_margin_m": level["clearance_margin_m"],
                                "collision_policy": "forbidden_except_task_object_contact",
                                "description": layout["description"],
                            }
                        ],
                    }
                )
                scenario_id += 1

    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "task_group": "libero_goal",
        "task_ids": task_ids,
        "seed": seed,
        "scenario_count": len(scenarios),
        "episode_count": sum(item["episodes"] for item in scenarios),
        "metric_contract": {
            "task_success": "original LIBERO sparse success",
            "collision_count": "MuJoCo contacts between robot geoms and obstacle geoms",
            "min_clearance_m": "minimum robot-to-obstacle geom distance when available, else sampled proxy distance",
            "safety_success": "collision_count == 0 and min_clearance_m >= scenario clearance margin",
            "avoidance_success": "task_success and safety_success",
        },
        "bc_targets": {
            "expert_source_order": ["cuRobo/OMPL waypoints", "Isaac Sim motion generation", "human teleop cleanup"],
            "observation_additions": ["obstacle poses", "depth or segmentation mask", "signed distance/occupancy feature"],
            "losses": ["action_mse", "waypoint_mse", "clearance_margin_aux"],
        },
        "rl_targets": {
            "algorithm_candidates": ["PPO", "GRPO"],
            "reward_terms": {
                "task_success": 1.0,
                "collision": -1.0,
                "clearance_violation": -0.2,
                "path_length": -0.01,
                "action_jerk": -0.01,
            },
        },
        "scenarios": scenarios,
        "note": "This spec is the source of truth for obstacle injection, expert trajectory collection, and collision-aware evaluation.",
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# LIBERO Obstacle Curriculum",
        "",
        f"Updated: {payload['timestamp']}",
        "",
        f"- Task group: `{payload['task_group']}`",
        f"- Task ids: `{payload['task_ids']}`",
        f"- Scenario count: `{payload['scenario_count']}`",
        f"- Planned episodes: `{payload['episode_count']}`",
        "",
        "## Difficulty Mix",
        "",
    ]
    for difficulty in OBSTACLE_LEVELS:
        count = sum(1 for item in payload["scenarios"] if item["difficulty"] == difficulty)
        episodes = sum(item["episodes"] for item in payload["scenarios"] if item["difficulty"] == difficulty)
        lines.append(f"- `{difficulty}`: {count} scenarios, {episodes} episodes")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "- `task_success`: original LIBERO sparse success",
            "- `collision_count`: robot-obstacle contacts",
            "- `min_clearance_m`: minimum robot-obstacle clearance",
            "- `safety_success`: no collision and clearance above margin",
            "- `avoidance_success`: task success and safety success",
            "",
            "## Next Execution Hook",
            "",
            "Use this JSON as input for the MuJoCo/Isaac obstacle injector and expert trajectory collector.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-ids", default="0,1,2,3,4,5,6,7,8,9")
    parser.add_argument("--seed", type=int, default=2000)
    parser.add_argument("--output-dir", default="artifacts/grasp_pipeline/runs/obstacle_curriculum_20260911")
    args = parser.parse_args()

    task_ids = [int(value.strip()) for value in args.task_ids.split(",") if value.strip()]
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_curriculum(task_ids, args.seed)
    json_path = output_dir / "obstacle_curriculum.json"
    md_path = output_dir / "summary.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(md_path, payload)

    print(f"Wrote obstacle curriculum: {json_path}")
    print(f"Wrote summary: {md_path}")
    print(f"Scenarios: {payload['scenario_count']} | planned episodes: {payload['episode_count']}")


if __name__ == "__main__":
    main()
