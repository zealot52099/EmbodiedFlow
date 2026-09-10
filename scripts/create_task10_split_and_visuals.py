from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np
import pyarrow.parquet as pq
from PIL import Image, ImageDraw


def stable_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else Path.cwd() / path


def load_summary(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frame_from_video(path: Path, frame_index: int) -> Image.Image | None:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_index))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame)


def make_episode_strip(dataset_root: Path, episode_row: dict, episode_id: int, output: Path) -> bool:
    thumbs = []
    for image_key in ["observation.images.image", "observation.images.image2"]:
        chunk = int(episode_row[f"videos/{image_key}/chunk_index"])
        file_id = int(episode_row[f"videos/{image_key}/file_index"])
        video_path = dataset_root / f"videos/{image_key}/chunk-{chunk:03d}/file-{file_id:03d}.mp4"
        length = int(episode_row["length"])
        frame_indices = np.linspace(0, max(0, length - 1), 6, dtype=int)
        for frame_index in frame_indices:
            image = frame_from_video(video_path, int(frame_index))
            if image is None:
                continue
            image = image.resize((160, 160))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 138, 160, 160), fill=(0, 0, 0))
            draw.text((4, 142), f"ep{episode_id} {image_key[-6:]} f{frame_index}", fill=(255, 255, 255))
            thumbs.append(image)

    if not thumbs:
        return False

    cols = 6
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 160, rows * 160), (245, 245, 245))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((idx % cols) * 160, (idx // cols) * 160))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="data/lerobot_libero")
    parser.add_argument("--summary", default="artifacts/libero_task10/summary.json")
    parser.add_argument("--output-dir", default="artifacts/libero_task10_split")
    parser.add_argument("--test-count", type=int, default=10)
    args = parser.parse_args()

    dataset_root = stable_path(args.dataset_root)
    output_dir = stable_path(args.output_dir)
    summary = load_summary(stable_path(args.summary))
    episodes = list(map(int, summary["selected_episodes"]))

    test_episodes = episodes[-args.test_count :]
    train_episodes = episodes[: -args.test_count]

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "train_episodes.txt").write_text(",".join(map(str, train_episodes)), encoding="utf-8")
    (output_dir / "test_episodes.txt").write_text(",".join(map(str, test_episodes)), encoding="utf-8")
    (output_dir / "split.json").write_text(
        json.dumps(
            {
                "task_index": summary["task_index"],
                "task_text": summary["task_text"],
                "train_episodes": train_episodes,
                "test_episodes": test_episodes,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    episode_rows = pq.read_table(dataset_root / "meta/episodes/chunk-000/file-000.parquet").to_pylist()
    episode_meta = {int(row["episode_index"]): row for row in episode_rows}
    visual_paths = []
    for episode_id in test_episodes[:4]:
        ok = make_episode_strip(
            dataset_root,
            episode_meta[episode_id],
            episode_id,
            output_dir / f"test_episode_{episode_id}.jpg",
        )
        if ok:
            visual_paths.append(str(output_dir / f"test_episode_{episode_id}.jpg"))

    print(f"train episodes={len(train_episodes)}")
    print(f"test episodes={len(test_episodes)}")
    print(f"visuals={visual_paths}")


if __name__ == "__main__":
    main()
