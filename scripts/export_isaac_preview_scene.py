"""Export an Isaac Sim-ready USDA preview scene for the grasp/place task.

This script does not require Isaac Sim or the USD Python bindings. It writes a
plain ASCII USD stage that can be opened in Isaac Sim after installation.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def run_text(command: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return "unavailable"
    return (result.stdout or result.stderr or "").strip() or "unavailable"


def find_isaac_candidates() -> list[str]:
    roots = [Path.home() / "AppData/Local/ov/pkg"]
    candidates: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        try:
            for path in root.iterdir():
                if not path.is_dir():
                    continue
                lowered = path.name.lower()
                if "isaac" not in lowered:
                    continue
                launchers = [
                    path / "isaac-sim.bat",
                    path / "isaac-sim.selector.bat",
                    path / "python.bat",
                    path / "kit/kit.exe",
                ]
                if any(candidate.exists() for candidate in launchers):
                    candidates.append(str(path))
        except (OSError, PermissionError):
            continue
    return candidates


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def usda_text() -> str:
    return """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{
    def DistantLight "KeyLight"
    {
        float inputs:angle = 0.35
        float inputs:intensity = 550
        double3 xformOp:rotateXYZ = (-45, 0, -35)
        uniform token[] xformOpOrder = ["xformOp:rotateXYZ"]
    }

    def Camera "Camera"
    {
        float focalLength = 28
        double3 xformOp:translate = (1.35, -1.7, 1.15)
        double3 xformOp:rotateXYZ = (62, 0, 39)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
    }

    def Xform "TabletopTask"
    {
        custom string task = "put the bowl on the plate"
        custom string source_eval = "LIBERO libero_goal task_id=8"

        def Cube "Table"
        {
            double3 xformOp:translate = (0, 0, 0.36)
            double3 xformOp:scale = (0.75, 0.55, 0.035)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
            color3f[] primvars:displayColor = [(0.55, 0.48, 0.38)]
        }

        def Cylinder "Plate_Target"
        {
            double radius = 0.14
            double height = 0.025
            double3 xformOp:translate = (0.18, 0.02, 0.42)
            uniform token[] xformOpOrder = ["xformOp:translate"]
            color3f[] primvars:displayColor = [(0.88, 0.88, 0.82)]
        }

        def Sphere "Bowl_Start"
        {
            double radius = 0.09
            double3 xformOp:translate = (-0.25, -0.12, 0.47)
            double3 xformOp:scale = (1, 1, 0.45)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
            color3f[] primvars:displayColor = [(0.08, 0.08, 0.09)]
        }

        def Sphere "Bowl_Placed_Ghost"
        {
            double radius = 0.09
            double3 xformOp:translate = (0.18, 0.02, 0.48)
            double3 xformOp:scale = (1, 1, 0.45)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
            color3f[] primvars:displayColor = [(0.1, 0.32, 0.95)]
            float primvars:displayOpacity = 0.35
        }

        def Cube "Gripper_Open"
        {
            double3 xformOp:translate = (-0.25, -0.12, 0.66)
            double3 xformOp:scale = (0.06, 0.025, 0.08)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
            color3f[] primvars:displayColor = [(0.12, 0.12, 0.13)]
        }

        def BasisCurves "EndEffector_Trajectory"
        {
            uniform token type = "linear"
            int[] curveVertexCounts = [5]
            point3f[] points = [
                (-0.35, -0.2, 0.72),
                (-0.25, -0.12, 0.62),
                (-0.25, -0.12, 0.52),
                (0.03, -0.05, 0.62),
                (0.18, 0.02, 0.55)
            ]
            color3f[] primvars:displayColor = [(0.1, 0.7, 0.25)]
            float[] widths = [0.01]
        }
    }
}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/grasp_pipeline/runs/isaac_preview_20260910")
    parser.add_argument("--eval-info", default="eval_logs/pi05_libero_task10_goal8_10ep_rerun_20260910/eval_info.json")
    parser.add_argument("--video-dir", default="eval_logs/pi05_libero_task10_goal8_10ep_rerun_20260910/videos/libero_goal_8")
    args = parser.parse_args()

    workspace = Path.cwd().resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene_path = output_dir / "put_bowl_on_plate_preview.usda"
    scene_path.write_text(usda_text(), encoding="utf-8")

    video_dir = Path(args.video_dir).resolve()
    videos = sorted(str(path) for path in video_dir.glob("*.mp4")) if video_dir.exists() else []
    eval_info = Path(args.eval_info).resolve()
    metrics: dict[str, Any] = {}
    if eval_info.exists():
        payload = json.loads(eval_info.read_text(encoding="utf-8"))
        metrics = payload.get("overall", {})

    isaac_candidates = find_isaac_candidates()
    manifest = {
        "status": "asset_exported",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "git_branch": run_text(["git", "branch", "--show-current"], workspace),
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "isaac_sim_detected": bool(isaac_candidates),
        "isaac_candidates": isaac_candidates,
        "scene_usda": str(scene_path),
        "task": "put the bowl on the plate",
        "source_eval_info": str(eval_info),
        "source_video_dir": str(video_dir),
        "source_video_count": len(videos),
        "sample_video": videos[0] if videos else None,
        "metrics": metrics,
        "open_in_isaac_sim": "File > Open > select put_bowl_on_plate_preview.usda",
        "note": "Isaac Sim was not launched by this script; this is an Isaac-ready preview asset export.",
    }
    write_json(output_dir / "manifest.json", manifest)
    print(f"Wrote Isaac-ready scene: {scene_path}")
    print(f"Wrote manifest: {output_dir / 'manifest.json'}")
    print(f"Source videos found: {len(videos)}")
    print(f"Isaac Sim detected: {manifest['isaac_sim_detected']}")


if __name__ == "__main__":
    main()
