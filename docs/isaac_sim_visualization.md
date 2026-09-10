# Isaac Sim Visualization

Updated: 2026-09-10

## Current Local State

This machine does not currently expose an Isaac Sim launcher under the standard Omniverse package path. The project therefore exports an Isaac-ready USD/USDA scene and provides launcher scripts that will run once Isaac Sim is installed or `ISAAC_SIM_ROOT` is set.

Latest scene:

```text
artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda
```

The scene represents the LIBERO task `put the bowl on the plate`: table, target plate, start bowl, placed bowl ghost, gripper marker, and end-effector trajectory.

## Commands

Regenerate the preview scene:

```powershell
cd E:\projects\robot
powershell -ExecutionPolicy Bypass -File .\scripts\run_isaac_preview.ps1
```

Detect an Isaac Sim install:

```powershell
cd E:\projects\robot
powershell -ExecutionPolicy Bypass -File .\scripts\find_isaac_sim.ps1
```

Launch the scene if Isaac Sim is installed:

```powershell
cd E:\projects\robot
powershell -ExecutionPolicy Bypass -File .\scripts\launch_isaac_preview.ps1
```

If Isaac Sim is installed outside the default Omniverse path:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\launch_isaac_preview.ps1 -IsaacRoot "D:\path\to\isaac-sim"
```

## Install Notes

NVIDIA's current Isaac Sim documentation says the 6.0 Python package path requires Python 3.12, and Windows may need long path support enabled before installation. Prefer the official NVIDIA Isaac Sim documentation for exact installation commands and version compatibility.

## Next Upgrade

After Isaac Sim launches successfully, replace the handcrafted trajectory in the USDA preview with rollout-derived object/end-effector transforms from LIBERO evaluation data.
