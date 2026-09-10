"""Load the exported grasp preview stage inside Isaac Sim.

Run this with Isaac Sim's bundled Python, for example:

    <ISAAC_SIM_ROOT>\python.bat scripts\isaac_load_preview.py --scene artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda

The script intentionally imports Isaac modules only inside main so the file can
be syntax-checked on machines without Isaac Sim.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True, help="USDA/USD stage to open.")
    parser.add_argument("--headless", action="store_true", help="Run Isaac Sim without GUI.")
    parser.add_argument("--frames", type=int, default=120, help="Number of frames to update after loading.")
    args = parser.parse_args()

    scene = Path(args.scene).resolve()
    if not scene.exists():
        raise SystemExit(f"Scene does not exist: {scene}")

    from isaacsim import SimulationApp  # type: ignore

    simulation_app = SimulationApp({"headless": args.headless})

    import omni.usd  # type: ignore

    usd_context = omni.usd.get_context()
    usd_context.open_stage(str(scene))

    for _ in range(max(args.frames, 1)):
        simulation_app.update()

    print(f"Loaded Isaac preview scene: {scene}")
    print("Close the Isaac Sim window when finished inspecting the grasp/place layout.")
    if args.headless:
        simulation_app.close()


if __name__ == "__main__":
    main()
