"""Summarize a LeRobot eval_info.json into a compact resumable artifact."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-info", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--command", default="")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    eval_info = Path(args.eval_info).resolve()
    payload = json.loads(eval_info.read_text(encoding="utf-8"))
    per_task = payload.get("per_task", [])
    overall = payload.get("overall", {})
    video_paths = overall.get("video_paths", [])

    task_rows: list[dict[str, Any]] = []
    for item in per_task:
        metrics = item.get("metrics", {})
        successes = metrics.get("successes", [])
        task_rows.append(
            {
                "task_group": item.get("task_group"),
                "task_id": item.get("task_id"),
                "episodes": len(successes),
                "successes": sum(1 for value in successes if value),
                "success_rate_percent": 100.0 * sum(1 for value in successes if value) / max(len(successes), 1),
                "sum_rewards": metrics.get("sum_rewards", []),
                "video_paths": metrics.get("video_paths", []),
            }
        )

    summary = {
        "status": "success",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "command": args.command,
        "source_eval_info": str(eval_info),
        "overall": {
            "success_rate_percent": overall.get("pc_success"),
            "avg_sum_reward": overall.get("avg_sum_reward"),
            "avg_max_reward": overall.get("avg_max_reward"),
            "n_episodes": overall.get("n_episodes"),
            "eval_seconds": overall.get("eval_s"),
            "eval_seconds_per_episode": overall.get("eval_ep_s"),
            "video_count": len(video_paths),
        },
        "per_task": task_rows,
        "note": args.note,
    }

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote eval summary: {output}")
    print(f"Overall success: {summary['overall']['success_rate_percent']}%")
    print(f"Videos: {len(video_paths)}")


if __name__ == "__main__":
    main()
