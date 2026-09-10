"""Lightweight QC for a local LeRobot dataset snapshot.

The script is intentionally schema-tolerant because LeRobot metadata layouts
change between dataset versions. It reports missing metadata, episode counts,
task strings, numeric NaN/Inf counts, and very short parquet shards.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def read_parquet(path: Path) -> Any:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise SystemExit("Install pyarrow first: pip install pyarrow") from exc
    return pq.read_table(path)


def table_rows(table: Any) -> list[dict[str, Any]]:
    names = table.column_names
    cols = {name: table[name].to_pylist() for name in names}
    return [{name: cols[name][i] for name in names} for i in range(table.num_rows)]


def numeric_bad_counts(table: Any) -> dict[str, dict[str, int]]:
    report: dict[str, dict[str, int]] = {}
    for name in table.column_names:
        values = table[name].to_pylist()
        nan_count = 0
        inf_count = 0
        checked = 0
        stack = list(values)
        while stack:
            value = stack.pop()
            if isinstance(value, (list, tuple)):
                stack.extend(value)
                continue
            if isinstance(value, float):
                checked += 1
                if math.isnan(value):
                    nan_count += 1
                elif math.isinf(value):
                    inf_count += 1
        if checked:
            report[name] = {"checked": checked, "nan": nan_count, "inf": inf_count}
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True, help="Local LeRobot dataset root.")
    parser.add_argument("--task-filter", default="", help="Optional substring to count matching tasks.")
    parser.add_argument("--output", default="artifacts/lerobot_qc.json")
    parser.add_argument("--min-rows", type=int, default=10)
    args = parser.parse_args()

    root = Path(args.dataset_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Dataset root does not exist: {root}")

    meta_dir = root / "meta"
    data_files = sorted(root.glob("data/**/*.parquet"))
    task_files = sorted(meta_dir.glob("*tasks*.parquet")) if meta_dir.exists() else []
    episode_files = sorted(meta_dir.glob("episodes/**/*.parquet")) if meta_dir.exists() else []

    result: dict[str, Any] = {
        "dataset_root": str(root),
        "data_parquet_files": len(data_files),
        "task_metadata_files": [str(p) for p in task_files],
        "episode_metadata_files": [str(p) for p in episode_files],
        "task_filter": args.task_filter,
        "tasks": [],
        "matching_tasks": [],
        "short_shards": [],
        "numeric_checks": {},
        "warnings": [],
    }

    for task_file in task_files:
        rows = table_rows(read_parquet(task_file))
        for row in rows:
            text = " ".join(str(v) for v in row.values())
            result["tasks"].append(row)
            if args.task_filter and args.task_filter.lower() in text.lower():
                result["matching_tasks"].append(row)

    for parquet in data_files[:50]:
        table = read_parquet(parquet)
        if table.num_rows < args.min_rows:
            result["short_shards"].append({"file": str(parquet), "rows": table.num_rows})
        bad = numeric_bad_counts(table)
        bad = {k: v for k, v in bad.items() if v["nan"] or v["inf"]}
        if bad:
            result["numeric_checks"][str(parquet)] = bad

    required_hint = ["observation", "action"]
    if not data_files:
        result["warnings"].append("No data parquet files found under data/**/*.parquet.")
    if not task_files:
        result["warnings"].append("No task metadata parquet found under meta/.")
    if not episode_files:
        result["warnings"].append("No episode metadata parquet found under meta/.")
    if data_files:
        sample_columns = read_parquet(data_files[0]).column_names
        for hint in required_hint:
            if not any(hint in column for column in sample_columns):
                result["warnings"].append(f"No column containing '{hint}' found in first data shard.")
        result["sample_columns"] = sample_columns

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote QC report: {output}")
    print(f"Data shards: {len(data_files)}")
    print(f"Tasks discovered: {len(result['tasks'])}")
    if args.task_filter:
        print(f"Matching tasks: {len(result['matching_tasks'])}")
    print(f"Warnings: {len(result['warnings'])}")


if __name__ == "__main__":
    main()
