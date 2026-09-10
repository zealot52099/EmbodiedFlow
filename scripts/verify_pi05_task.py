from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_DATASET_FILES = [
    "meta/info.json",
    "meta/stats.json",
    "meta/tasks.parquet",
    "meta/episodes/chunk-000/file-000.parquet",
]

REQUIRED_MODEL_FILES = [
    "config.json",
    "model.safetensors",
    "policy_preprocessor.json",
    "policy_postprocessor.json",
]

EXPECTED_MODEL_SAFETENSORS_BYTES = 14_467_165_872


def count_files(root: Path, pattern: str) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.glob(pattern))


def stable_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return Path.cwd() / path


def check_safetensors(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.stat().st_size < EXPECTED_MODEL_SAFETENSORS_BYTES:
        return (
            "incomplete_or_downloading: "
            f"{path.stat().st_size}/{EXPECTED_MODEL_SAFETENSORS_BYTES} bytes"
        )
    try:
        from safetensors import safe_open

        with safe_open(path, framework="pt", device="cpu") as handle:
            keys = list(handle.keys())
        return f"ok, tensors={len(keys)}"
    except Exception as exc:  # noqa: BLE001
        return f"invalid: {type(exc).__name__}: {exc}"


def run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
    output = (result.stdout + result.stderr).strip()
    return output.splitlines()[0] if output else f"exit={result.returncode}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="data/lerobot_libero")
    parser.add_argument("--model-root", default="models/pi05_libero_base")
    parser.add_argument("--output", default="artifacts/pi05_task_verification.json")
    args = parser.parse_args()

    dataset_root = stable_path(args.dataset_root)
    model_root = stable_path(args.model_root)

    dataset_missing = [name for name in REQUIRED_DATASET_FILES if not (dataset_root / name).exists()]
    model_missing = [name for name in REQUIRED_MODEL_FILES if not (model_root / name).exists()]

    report = {
        "python": sys.version,
        "executables": {
            "python": sys.executable,
            "lerobot-train": shutil.which("lerobot-train"),
            "lerobot-eval": shutil.which("lerobot-eval"),
        },
        "torch": run([sys.executable, "-c", "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no_cuda')"]),
        "lerobot": run([sys.executable, "-c", "import lerobot; print(getattr(lerobot, '__version__', 'no_version'))"]),
        "dataset": {
            "root": str(dataset_root),
            "missing_required": dataset_missing,
            "parquet_count": count_files(dataset_root, "data/**/*.parquet"),
            "video_count": count_files(dataset_root, "videos/**/*.mp4"),
        },
        "model": {
            "root": str(model_root),
            "missing_required": model_missing,
            "model_safetensors_size": (model_root / "model.safetensors").stat().st_size
            if (model_root / "model.safetensors").exists()
            else 0,
            "safetensors_check": check_safetensors(model_root / "model.safetensors"),
            "expected_model_safetensors_size": EXPECTED_MODEL_SAFETENSORS_BYTES,
        },
    }

    info_path = dataset_root / "meta/info.json"
    if info_path.exists():
        report["dataset"]["info"] = json.loads(info_path.read_text(encoding="utf-8"))

    output = stable_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote verification report: {output}")
    print(f"Dataset parquet: {report['dataset']['parquet_count']}")
    print(f"Dataset videos: {report['dataset']['video_count']}")
    print(f"Dataset missing: {dataset_missing or 'none'}")
    print(f"Model missing: {model_missing or 'none'}")
    print(f"Safetensors: {report['model']['safetensors_check']}")

    safetensors_status = str(report["model"]["safetensors_check"])
    if (
        dataset_missing
        or model_missing
        or safetensors_status.startswith("invalid")
        or safetensors_status.startswith("incomplete")
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
