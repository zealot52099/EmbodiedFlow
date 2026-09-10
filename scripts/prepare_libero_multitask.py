"""Prepare a diverse LIBERO episode subset for multi-task grasp/place training."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


def stable_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else Path.cwd() / path


def classify_task(text: str) -> str:
    lowered = text.lower()
    if "drawer" in lowered:
        return "drawer_manipulation"
    if "microwave" in lowered:
        return "microwave_manipulation"
    if "stove" in lowered:
        return "stove_or_appliance"
    if "basket" in lowered:
        return "pick_place_basket"
    if "plate" in lowered:
        return "pick_place_plate"
    if "rack" in lowered or "cabinet" in lowered:
        return "pick_place_furniture"
    return "other"


def read_tasks(dataset_root: Path) -> dict[int, str]:
    rows = pq.read_table(dataset_root / "meta/tasks.parquet").to_pylist()
    return {
        int(row["task_index"]): str(row.get("__index_level_0__", ""))
        for row in rows
    }


def collect_episodes_by_task(dataset_root: Path) -> dict[int, set[int]]:
    by_task: dict[int, set[int]] = defaultdict(set)
    for parquet_file in sorted((dataset_root / "data").glob("**/*.parquet")):
        table = pq.read_table(parquet_file, columns=["episode_index", "task_index"])
        for row in table.to_pylist():
            by_task[int(row["task_index"])].add(int(row["episode_index"]))
    return by_task


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="data/lerobot_libero")
    parser.add_argument("--output-dir", default="artifacts/libero_multitask_diverse")
    parser.add_argument("--max-episodes-per-task", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument(
        "--task-indices",
        default="all",
        help="Comma-separated task indices, or 'all'.",
    )
    args = parser.parse_args()

    dataset_root = stable_path(args.dataset_root)
    output_dir = stable_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = read_tasks(dataset_root)
    by_task = collect_episodes_by_task(dataset_root)
    if args.task_indices == "all":
        selected_task_indices = sorted(tasks)
    else:
        selected_task_indices = sorted(int(value.strip()) for value in args.task_indices.split(",") if value.strip())

    rng = random.Random(args.seed)
    selected_episodes: list[int] = []
    per_task: list[dict[str, Any]] = []
    category_counts: dict[str, int] = defaultdict(int)
    for task_index in selected_task_indices:
        episodes = sorted(by_task.get(task_index, []))
        if not episodes:
            continue
        sampled = episodes[:]
        rng.shuffle(sampled)
        sampled = sorted(sampled[: args.max_episodes_per_task])
        task_text = tasks.get(task_index, "")
        category = classify_task(task_text)
        category_counts[category] += len(sampled)
        selected_episodes.extend(sampled)
        per_task.append(
            {
                "task_index": task_index,
                "task_text": task_text,
                "category": category,
                "available_episodes": len(episodes),
                "selected_episodes": sampled,
                "selected_count": len(sampled),
            }
        )

    selected_episodes = sorted(set(selected_episodes))
    summary = {
        "dataset_root": str(dataset_root),
        "seed": args.seed,
        "max_episodes_per_task": args.max_episodes_per_task,
        "selected_task_count": len(per_task),
        "selected_episode_count": len(selected_episodes),
        "selected_episodes": selected_episodes,
        "category_episode_counts": dict(sorted(category_counts.items())),
        "per_task": per_task,
        "training_role": "Diverse LIBERO subset for pi0.5 BC/SFT smoke and short-run training.",
        "evaluation_role": "Use matching LIBERO suites with task-level success rate; start with broader suite eval before RL.",
    }

    (output_dir / "episodes.txt").write_text(
        ",".join(str(ep) for ep in selected_episodes), encoding="utf-8"
    )
    (output_dir / "episodes.json").write_text(
        json.dumps({"episodes": selected_episodes}, indent=2), encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# LIBERO Diverse Multi-task Subset",
        "",
        f"- Selected tasks: {len(per_task)}",
        f"- Selected episodes: {len(selected_episodes)}",
        f"- Max episodes per task: {args.max_episodes_per_task}",
        "",
        "| task_index | category | selected | available | task |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for item in per_task:
        lines.append(
            f"| {item['task_index']} | {item['category']} | {item['selected_count']} | "
            f"{item['available_episodes']} | {item['task_text']} |"
        )
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Prepared diverse LIBERO subset: {output_dir}")
    print(f"Tasks: {len(per_task)}")
    print(f"Episodes: {len(selected_episodes)}")


if __name__ == "__main__":
    main()
