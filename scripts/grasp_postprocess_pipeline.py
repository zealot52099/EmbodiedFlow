"""Smoke postprocessing pipeline for grasp datasets.

The v1 implementation is intentionally adapter-oriented. LIBERO/LeRobot can be
inspected end-to-end today; teleop, ego, UMI, and additional simulator datasets
share the same normalized manifest schema as adapters are added.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run_text(command: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return "unavailable"
    return (result.stdout or result.stderr or "").strip() or "unavailable"


def env_header(workspace: Path, dataset_root: Path, model_root: Path | None) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "git_branch": run_text(["git", "branch", "--show-current"], workspace),
        "git_root": run_text(["git", "rev-parse", "--show-toplevel"], workspace),
        "python": sys.version.replace("\n", " "),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "protocol_buffers_python_implementation": os.environ.get("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"),
        "gpu": run_text(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            workspace,
        ),
        "dataset_root": str(dataset_root),
        "model_root": str(model_root) if model_root else None,
    }


def load_parquet(path: Path) -> Any:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("pyarrow is required for LeRobot parquet inspection: pip install pyarrow") from exc
    return pq.read_table(path)


def scalar_bad_counts(values: list[Any]) -> dict[str, int]:
    checked = 0
    nan_count = 0
    inf_count = 0
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
    return {"checked": checked, "nan": nan_count, "inf": inf_count}


def parquet_numeric_report(table: Any) -> dict[str, dict[str, int]]:
    report: dict[str, dict[str, int]] = {}
    for name in table.column_names:
        counts = scalar_bad_counts(table[name].to_pylist())
        if counts["checked"]:
            report[name] = counts
    return report


def inspect_lerobot(dataset_root: Path, max_shards: int, seed: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    meta_dir = dataset_root / "meta"
    info_path = meta_dir / "info.json"
    stats_path = meta_dir / "stats.json"
    if not info_path.exists():
        raise FileNotFoundError(f"Missing LeRobot metadata: {info_path}")

    info = read_json(info_path)
    stats = read_json(stats_path) if stats_path.exists() else {}
    data_files = sorted(dataset_root.glob("data/**/*.parquet"))
    task_files = sorted(meta_dir.glob("*tasks*.parquet"))
    episode_files = sorted(meta_dir.glob("episodes/**/*.parquet"))

    features = info.get("features", {})
    camera_keys = [key for key, value in features.items() if value.get("dtype") == "video"]
    action_keys = [key for key in features if key == "action" or key.endswith(".action")]
    state_keys = [key for key in features if "state" in key]

    tasks: list[dict[str, Any]] = []
    for task_file in task_files:
        table = load_parquet(task_file)
        columns = {name: table[name].to_pylist() for name in table.column_names}
        for row_index in range(table.num_rows):
            tasks.append({name: columns[name][row_index] for name in table.column_names})

    episode_count = info.get("total_episodes", 0)
    episode_ids = list(range(int(episode_count))) if isinstance(episode_count, int) else []
    rng = random.Random(seed)
    rng.shuffle(episode_ids)
    train_cut = int(len(episode_ids) * 0.8)
    val_cut = int(len(episode_ids) * 0.9)
    split = {
        "seed": seed,
        "train": sorted(episode_ids[:train_cut]),
        "val": sorted(episode_ids[train_cut:val_cut]),
        "test": sorted(episode_ids[val_cut:]),
    }

    sampled_numeric: dict[str, Any] = {}
    short_shards: list[dict[str, Any]] = []
    for parquet_path in data_files[:max_shards]:
        table = load_parquet(parquet_path)
        if table.num_rows < 10:
            short_shards.append({"file": str(parquet_path), "rows": table.num_rows})
        sampled_numeric[str(parquet_path)] = parquet_numeric_report(table)

    warnings: list[str] = []
    if not data_files:
        warnings.append("No data parquet files found.")
    if not camera_keys:
        warnings.append("No video camera keys found in features.")
    if not action_keys:
        warnings.append("No action key found; this dataset cannot train low-level robot action directly.")
    if not state_keys:
        warnings.append("No robot state key found.")
    if not tasks:
        warnings.append("No task metadata loaded.")
    missing_stats = [key for key in ("action", "observation.state") if key not in stats]
    if missing_stats:
        warnings.append(f"Missing normalization stats for: {', '.join(missing_stats)}")

    normalized_schema = {
        "schema_version": "1.0",
        "format": "lerobot_style_grasp_episode_manifest",
        "dataset_type": "teleop",
        "robot": {
            "robot_type": info.get("robot_type"),
            "embodiment_metadata_required": [
                "robot_type",
                "action_space",
                "control_frequency_hz",
                "camera_layout",
                "gripper_type",
            ],
        },
        "episode_fields": {
            "images": camera_keys,
            "state": state_keys,
            "action": action_keys,
            "language": "task_index -> meta/tasks.parquet",
            "task_metadata": ["task_index", "episode_index"],
            "pi07_ready_context": [
                "language",
                "embodiment_metadata",
                "task_metadata",
                "subgoal_image",
                "success_failure_label",
            ],
        },
        "ego_policy": "Ego-only sources may populate language/subgoal/affordance fields, but must not synthesize low-level robot actions.",
    }

    qc = {
        "dataset_root": str(dataset_root),
        "adapter": "lerobot_libero",
        "total_episodes": info.get("total_episodes"),
        "total_frames": info.get("total_frames"),
        "total_tasks": info.get("total_tasks"),
        "fps": info.get("fps"),
        "data_parquet_files": len(data_files),
        "task_metadata_files": [str(path) for path in task_files],
        "episode_metadata_files": [str(path) for path in episode_files],
        "camera_keys": camera_keys,
        "state_keys": state_keys,
        "action_keys": action_keys,
        "task_count_loaded": len(tasks),
        "sample_tasks": tasks[:10],
        "short_shards": short_shards,
        "numeric_report_sampled_shards": sampled_numeric,
        "normalization_keys": sorted(stats.keys()),
        "warnings": warnings,
    }
    return normalized_schema, qc, split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="data/lerobot_libero")
    parser.add_argument("--model-root", default="models/pi05_libero_base")
    parser.add_argument("--run-root", default="artifacts/grasp_pipeline/runs")
    parser.add_argument("--run-name", default="")
    parser.add_argument("--adapter", default="lerobot_libero", choices=["lerobot_libero"])
    parser.add_argument("--max-shards", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1000)
    args = parser.parse_args()

    workspace = Path.cwd().resolve()
    dataset_root = Path(args.dataset_root).resolve()
    model_root = Path(args.model_root).resolve() if args.model_root else None
    run_name = args.run_name or f"postprocess_{now_stamp()}"
    run_dir = Path(args.run_root).resolve() / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    header = env_header(workspace, dataset_root, model_root)
    write_json(run_dir / "env.json", header)
    write_json(run_dir / "config.json", vars(args))

    log_lines = ["# Grasp postprocess run", "", json.dumps(header, indent=2, ensure_ascii=False), ""]
    try:
        if not dataset_root.exists():
            raise FileNotFoundError(f"Dataset root does not exist: {dataset_root}")
        schema, qc, split = inspect_lerobot(dataset_root, args.max_shards, args.seed)
        write_json(run_dir / "normalized_schema.json", schema)
        write_json(run_dir / "qc_report.json", qc)
        write_json(run_dir / "split.json", split)
        manifest = {
            "status": "success",
            "run_dir": str(run_dir),
            "outputs": {
                "env": str(run_dir / "env.json"),
                "config": str(run_dir / "config.json"),
                "normalized_schema": str(run_dir / "normalized_schema.json"),
                "qc_report": str(run_dir / "qc_report.json"),
                "split": str(run_dir / "split.json"),
            },
            "next_recommended_command": (
                "powershell -ExecutionPolicy Bypass -File scripts\\run_grasp_pipeline_smoke.ps1 "
                "-SkipPostprocess"
            ),
        }
        write_json(run_dir / "manifest.json", manifest)
        log_lines.append("Status: success")
        print(f"Wrote grasp postprocess run: {run_dir}")
        print(f"Warnings: {len(qc['warnings'])}")
    except Exception as exc:
        failure = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "failed_command": " ".join(sys.argv),
            "suggested_next_step": "Fix the missing dependency/path above, then rerun the same command.",
        }
        write_json(run_dir / "failure.json", failure)
        log_lines.append(json.dumps(failure, indent=2, ensure_ascii=False))
        (run_dir / "run.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        raise

    (run_dir / "run.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
