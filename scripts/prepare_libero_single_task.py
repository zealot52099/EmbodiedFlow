from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq


def stable_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else Path.cwd() / path


def read_table(path: Path):
    return pq.read_table(path)


def flatten_numbers(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, np.ndarray):
        return [float(v) for v in value.reshape(-1)]
    if isinstance(value, (list, tuple)):
        out: list[float] = []
        for item in value:
            out.extend(flatten_numbers(item))
        return out
    return []


def summarize_vectors(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [flatten_numbers(row.get(key)) for row in rows]
    values = [v for v in values if v]
    if not values:
        return {"present": False}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "present": True,
        "shape": list(arr.shape),
        "mean": np.round(arr.mean(axis=0), 6).tolist(),
        "std": np.round(arr.std(axis=0), 6).tolist(),
        "min": np.round(arr.min(axis=0), 6).tolist(),
        "max": np.round(arr.max(axis=0), 6).tolist(),
        "nan_count": int(np.isnan(arr).sum()),
        "inf_count": int(np.isinf(arr).sum()),
    }


def make_contact_sheet(
    dataset_root: Path,
    rows: list[dict[str, Any]],
    episode_meta: dict[int, dict[str, Any]],
    output: Path,
) -> str:
    try:
        import cv2
        from PIL import Image, ImageDraw
    except Exception as exc:  # noqa: BLE001
        return f"skipped: missing image dependency: {exc}"

    output.parent.mkdir(parents=True, exist_ok=True)
    selected = []
    if rows:
        indices = np.linspace(0, len(rows) - 1, min(8, len(rows)), dtype=int)
        selected = [rows[int(i)] for i in indices]

    thumbs = []
    for row in selected:
        for image_key in ["observation.images.image", "observation.images.image2"]:
            episode = episode_meta.get(int(row.get("episode_index", -1)), {})
            chunk_index = episode.get(f"videos/{image_key}/chunk_index")
            file_index = episode.get(f"videos/{image_key}/file_index")
            video_path = None
            if chunk_index is not None and file_index is not None:
                video_path = f"videos/{image_key}/chunk-{int(chunk_index):03d}/file-{int(file_index):03d}.mp4"
            timestamp = float(row.get("timestamp", 0.0) or 0.0)
            if not video_path:
                continue
            cap = cv2.VideoCapture(str(dataset_root / video_path))
            if not cap.isOpened():
                continue
            fps = cap.get(cv2.CAP_PROP_FPS) or 10.0
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(round(timestamp * fps))))
            ok, frame = cap.read()
            cap.release()
            if not ok:
                continue
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame).resize((160, 160))
            draw = ImageDraw.Draw(image)
            label = f"ep{row.get('episode_index')} {image_key.rsplit('.', 1)[-1]}"
            draw.rectangle((0, 138, 160, 160), fill=(0, 0, 0))
            draw.text((4, 142), label, fill=(255, 255, 255))
            thumbs.append(image)

    if not thumbs:
        return "skipped: no frames decoded"

    cols = 4
    rows_n = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 160, rows_n * 160), (245, 245, 245))
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % cols) * 160, (i // cols) * 160))
    sheet.save(output)
    return str(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="data/lerobot_libero")
    parser.add_argument("--task-index", type=int, default=10)
    parser.add_argument("--output-dir", default="artifacts/libero_task10")
    parser.add_argument("--max-rows-for-stats", type=int, default=5000)
    args = parser.parse_args()

    dataset_root = stable_path(args.dataset_root)
    output_dir = stable_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tasks = read_table(dataset_root / "meta/tasks.parquet").to_pylist()
    task_map = {int(row["task_index"]): row.get("__index_level_0__", "") for row in tasks}
    task_text = task_map.get(args.task_index, "")
    if not task_text:
        raise SystemExit(f"Task index not found: {args.task_index}")

    episode_table = read_table(dataset_root / "meta/episodes/chunk-000/file-000.parquet")
    episode_rows = episode_table.to_pylist()
    episode_meta = {int(row["episode_index"]): row for row in episode_rows}

    selected_rows: list[dict[str, Any]] = []
    schema_columns: list[str] = []
    parquet_files = sorted((dataset_root / "data").glob("**/*.parquet"))
    selected_episode_set: set[int] = set()
    for parquet_file in parquet_files:
        table = read_table(parquet_file)
        if not schema_columns:
            schema_columns = table.column_names
        if "task_index" in table.column_names:
            task_subset = [row for row in table.to_pylist() if int(row.get("task_index", -1)) == args.task_index]
            selected_episode_set.update(int(row["episode_index"]) for row in task_subset)
            if len(selected_rows) < args.max_rows_for_stats:
                remaining = args.max_rows_for_stats - len(selected_rows)
                selected_rows.extend(task_subset[:remaining])

    selected_episodes = sorted(selected_episode_set)
    if not selected_episodes:
        raise SystemExit(f"No episodes found for task_index={args.task_index}")

    episode_lengths = Counter(int(row["episode_index"]) for row in selected_rows)
    action_summary = summarize_vectors(selected_rows, "action")
    state_summary = summarize_vectors(selected_rows, "observation.state")

    report = {
        "dataset_root": str(dataset_root),
        "task_index": args.task_index,
        "task_text": task_text,
        "selected_episode_count": len(selected_episodes),
        "selected_episodes": selected_episodes,
        "rows_sampled_for_stats": len(selected_rows),
        "episode_lengths_in_sample": dict(sorted(episode_lengths.items())),
        "schema_columns": schema_columns,
        "action_summary": action_summary,
        "state_summary": state_summary,
        "postprocessing": {
            "filtered_to_single_task_index": args.task_index,
            "generated_episode_list_for_training": True,
            "numeric_qc_for_selected_rows": True,
            "visual_contact_sheet": True,
            "physical_files_rewritten": False,
            "reason_no_rewrite": "LeRobot supports episode filtering at training time; keeping the source dataset immutable avoids duplicating ~2GB of videos.",
        },
    }

    (output_dir / "episodes.txt").write_text(
        ",".join(str(ep) for ep in selected_episodes), encoding="utf-8"
    )
    (output_dir / "episodes.json").write_text(
        json.dumps({"episodes": selected_episodes}, indent=2), encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    sheet_status = make_contact_sheet(
        dataset_root,
        selected_rows,
        episode_meta,
        output_dir / "visual_contact_sheet.jpg",
    )
    report["visual_contact_sheet"] = sheet_status
    (output_dir / "summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Prepared task {args.task_index}: {task_text}")
    print(f"Episodes: {len(selected_episodes)}")
    print(f"Rows sampled: {len(selected_rows)}")
    print(f"Wrote: {output_dir}")
    print(f"Visual: {sheet_status}")


if __name__ == "__main__":
    main()
