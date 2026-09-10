"""Render a lightweight PNG preview matching the Isaac-ready USDA scene."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/grasp_pipeline/runs/isaac_preview_20260910/put_bowl_on_plate_preview.png")
    args = parser.parse_args()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(9, 6), dpi=150)
    ax = fig.add_subplot(111, projection="3d")

    # Tabletop plane.
    table = [
        [(-0.75, -0.55, 0.36), (0.75, -0.55, 0.36), (0.75, 0.55, 0.36), (-0.75, 0.55, 0.36)]
    ]
    ax.add_collection3d(Poly3DCollection(table, facecolors="#8c7a61", edgecolors="#5d5142", alpha=0.75))

    # Plate target and bowl markers.
    ax.scatter([0.18], [0.02], [0.43], s=1200, c="#e0e0d2", edgecolors="#777777", marker="o", label="target plate")
    ax.scatter([-0.25], [-0.12], [0.48], s=800, c="#151518", edgecolors="#111111", marker="o", label="bowl start")
    ax.scatter([0.18], [0.02], [0.49], s=800, c="#1a52f2", alpha=0.35, edgecolors="#1a52f2", marker="o", label="bowl placed")

    # Simple gripper marker.
    ax.scatter([-0.25], [-0.12], [0.66], s=200, c="#2b2b2f", marker="s", label="gripper")

    xs = [-0.35, -0.25, -0.25, 0.03, 0.18]
    ys = [-0.20, -0.12, -0.12, -0.05, 0.02]
    zs = [0.72, 0.62, 0.52, 0.62, 0.55]
    ax.plot(xs, ys, zs, color="#22a447", linewidth=3, label="end-effector trajectory")
    ax.scatter(xs, ys, zs, c="#22a447", s=35)

    ax.set_title("Isaac-ready preview: put the bowl on the plate")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_xlim(-0.8, 0.8)
    ax.set_ylim(-0.6, 0.6)
    ax.set_zlim(0.3, 0.85)
    ax.view_init(elev=25, azim=-55)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(output)
    print(f"Wrote fallback preview PNG: {output}")


if __name__ == "__main__":
    main()
