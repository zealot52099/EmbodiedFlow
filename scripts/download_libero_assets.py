from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from urllib.parse import quote

from huggingface_hub import list_repo_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", default="lerobot/libero-assets")
    parser.add_argument("--repo-type", default="dataset")
    parser.add_argument("--revision", default="main")
    parser.add_argument("--endpoint", default=os.environ.get("HF_ENDPOINT", "https://huggingface.co"))
    parser.add_argument("--output-dir", default="data/libero_assets")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    endpoint = args.endpoint.rstrip("/")
    repo_prefix = "datasets/" if args.repo_type == "dataset" else ""
    files = list_repo_files(args.repo_id, repo_type=args.repo_type, revision=args.revision)

    downloaded = 0
    skipped = 0
    for index, path in enumerate(files, start=1):
        if path.endswith("/"):
            continue
        target = output_dir / path
        if target.exists() and target.stat().st_size > 0:
            skipped += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        encoded_path = "/".join(quote(part) for part in path.split("/"))
        url = f"{endpoint}/{repo_prefix}{args.repo_id}/resolve/{args.revision}/{encoded_path}"
        print(f"[{index}/{len(files)}] {path}", flush=True)
        subprocess.run(
            ["curl.exe", "-L", "--fail", "--retry", "5", "--retry-delay", "2", "-o", str(target), url],
            check=True,
        )
        downloaded += 1

    print(f"done downloaded={downloaded} skipped={skipped} output_dir={output_dir}")


if __name__ == "__main__":
    main()
