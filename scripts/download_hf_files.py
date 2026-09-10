from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import hf_hub_download


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", default="lerobot/libero")
    parser.add_argument("--repo-type", default="dataset")
    parser.add_argument("--local-dir", default="data/lerobot_libero")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    os.environ.pop("HF_ENDPOINT", None)
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")

    root = Path(args.local_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for filename in args.files:
        print(f"downloading {filename}")
        path = hf_hub_download(
            repo_id=args.repo_id,
            filename=filename,
            repo_type=args.repo_type,
            local_dir=root,
            etag_timeout=60,
        )
        print(f" -> {path}")


if __name__ == "__main__":
    main()
