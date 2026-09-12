"""Summarize current policy readiness for obstacle-avoidance training."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def failed_episode_indices(row: dict[str, Any]) -> list[int]:
    rewards = row.get("sum_rewards", [])
    return [index for index, reward in enumerate(rewards) if float(reward) <= 0.0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-summary", required=True)
    parser.add_argument("--curriculum", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    eval_summary_path = Path(args.eval_summary).resolve()
    curriculum_path = Path(args.curriculum).resolve()
    output_path = Path(args.output).resolve()

    eval_summary = json.loads(eval_summary_path.read_text(encoding="utf-8"))
    curriculum = json.loads(curriculum_path.read_text(encoding="utf-8"))

    weak_tasks = []
    all_failures = []
    for row in eval_summary.get("per_task", []):
        failures = failed_episode_indices(row)
        task_id = row.get("task_id")
        if failures:
            weak_tasks.append(
                {
                    "task_group": row.get("task_group"),
                    "task_id": task_id,
                    "baseline_success_rate_percent": row.get("success_rate_percent"),
                    "failed_episode_indices": failures,
                }
            )
            for episode_index in failures:
                all_failures.append({"task_id": task_id, "episode_index": episode_index})

    weak_task_ids = {item["task_id"] for item in weak_tasks}
    prioritized_scenarios = [
        scenario
        for scenario in curriculum.get("scenarios", [])
        if scenario.get("task_id") in weak_task_ids or scenario.get("difficulty") in {"easy", "medium"}
    ]

    report = {
        "status": "ready_for_obstacle_data_collection",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source_eval_summary": str(eval_summary_path),
        "source_curriculum": str(curriculum_path),
        "baseline": eval_summary.get("overall", {}),
        "weak_tasks": weak_tasks,
        "failed_episode_count": len(all_failures),
        "planned_obstacle_scenarios": curriculum.get("scenario_count"),
        "planned_obstacle_episodes": curriculum.get("episode_count"),
        "recommended_stage_1": {
            "name": "obstacle_bc_data_collection",
            "priority_task_ids": sorted(weak_task_ids),
            "scenario_count": len(prioritized_scenarios),
            "episode_count": sum(item.get("episodes", 0) for item in prioritized_scenarios),
            "expert_source": "motion_planner_first_then_teleop_cleanup",
        },
        "recommended_stage_2": {
            "name": "collision_aware_bc_finetune",
            "base_checkpoint": "outputs\\pi05_libero_multitask_4090\\checkpoints\\030000\\pretrained_model",
            "suggested_steps": 10000,
            "batch_size": 1,
            "mixing": {
                "obstacle_expert": 0.6,
                "original_multitask_subset": 0.4,
            },
        },
        "recommended_stage_3": {
            "name": "rlinf_safety_finetune",
            "start_after": "collision_aware_bc_finetune reaches >=90% avoidance_success on easy+medium scenarios",
            "reward_terms": curriculum.get("rl_targets", {}).get("reward_terms", {}),
        },
        "notes": [
            "Existing full multi-task checkpoint is strong on unmodified LIBERO; obstacle-specific data should focus first on safety generalization.",
            "Weak unmodified tasks are prioritized because they are more likely to regress under obstacle perturbations.",
            "This readiness report does not claim robot-obstacle collision measurements until an obstacle injector runner writes telemetry.",
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote obstacle readiness report: {output_path}")
    print(f"Weak tasks: {sorted(weak_task_ids)}")
    print(f"Prioritized obstacle episodes: {report['recommended_stage_1']['episode_count']}")


if __name__ == "__main__":
    main()
