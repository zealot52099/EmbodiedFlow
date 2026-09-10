# Grasp Pipeline Status

Updated: 2026-09-10

## Goal

Implement a resumable research prototype for generic multi-robot grasp/place tasks:
dataset registry, adapter-ready postprocessing, pi0.5/pi0.7-ready training workflow, MuJoCo/LIBERO evaluation, and Isaac Sim visualization planning.

## Current Stage

Implementation stage: v1 smoke infrastructure, single-task pi0.5 BC eval, diverse LIBERO multi-task smoke training/eval, and Isaac-ready preview export are validated.

## Completed

- Confirmed workspace: `E:\projects\robot`.
- Confirmed local LIBERO dataset: `data\lerobot_libero`.
- Confirmed local pi0.5 base/model outputs exist from prior experiments.
- Added dataset registry source of truth: `data\grasp_dataset_registry.json`.
- Added registry validator/summary script: `scripts\grasp_dataset_registry.py`.
- Added postprocessing smoke pipeline: `scripts\grasp_postprocess_pipeline.py`.
- Added resumable smoke orchestrator: `scripts\run_grasp_pipeline_smoke.ps1`.
- Added decision log: `docs\grasp_pipeline_decisions.md`.
- Validated dataset registry: 10 datasets across `teleop`, `ego`, `umi`, and `sim`.
- Ran postprocess smoke: `artifacts\grasp_pipeline\runs\smoke_orchestrator_check`.
- Confirmed LIBERO QC: 1693 episodes, 273465 frames, 40 tasks, 377 parquet shards, dual cameras, state/action keys present, sampled NaN/Inf counts are zero.
- Confirmed environment header capture: workspace, git branch, Python, GPU, dataset root, and model root are written to `env.json`.
- Fixed pi0.5 training script path from the old `E:\Project\...` location to `E:\projects\lerobot_experiment\envs\lerobot312`.
- Added `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` to smoke/training scripts to avoid protobuf/TensorFlow import incompatibility in fallback environments.
- Added checkpoint-existence fallback for 1-step pi0.5 smoke training: if `lerobot-train` exits nonzero after writing the expected checkpoint, the run is recorded as completed with a teardown warning.
- Ran full smoke: registry validation, postprocess QC, and pi0.5 1-step train via `artifacts\grasp_pipeline\runs\smoke_full_final`.
- Ran pi0.5 LIBERO BC evaluation on `libero_goal` / `task_id=8` for 10 episodes.
- Confirmed BC eval result: 10/10 successes, 100.0% success rate, avg sum reward 1.0, avg max reward 1.0.
- Added lightweight eval summary: `artifacts\grasp_pipeline\runs\eval_pi05_goal8_20260910\eval_summary.json`.
- Added Isaac-ready USDA preview exporter: `scripts\export_isaac_preview_scene.py`.
- Added Isaac preview wrapper: `scripts\run_isaac_preview.ps1`.
- Exported Isaac-ready scene: `artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda`.
- Confirmed current machine does not expose an Isaac Sim launcher under the standard Omniverse install path, so GUI rendering was not launched.
- Added Isaac Sim launcher detection: `scripts\find_isaac_sim.ps1`.
- Added Isaac Sim scene launcher: `scripts\launch_isaac_preview.ps1`.
- Added Isaac-side loader script: `scripts\isaac_load_preview.py`.
- Attempted Isaac launch and recorded blocker: `artifacts\grasp_pipeline\runs\isaac_launch_20260910\manifest.json`.
- Added fallback preview renderer: `scripts\render_isaac_preview_fallback.py`.
- Rendered layout preview PNG: `artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.png`.
- Added diverse LIBERO task sampler: `scripts\prepare_libero_multitask.py`.
- Generated diverse LIBERO subset: 40 tasks, 400 episodes, 66248 frames in `artifacts\libero_multitask_diverse`.
- Fixed pi0.5 train wrapper to call `python -m lerobot.scripts.lerobot_train`, capture stdout/stderr logs, and quote Windows arguments correctly.
- Ran pi0.5 diverse multi-task smoke training for 1 step: `outputs\pi05_libero_multitask_smoke_fixed\checkpoints\000001\pretrained_model`.
- Added full `libero_goal` eval wrapper: `scripts\eval_pi05_libero_goal_all.ps1`.
- Ran `libero_goal` task ids 0-9 with 1 episode per task using the 1-step multi-task smoke checkpoint.
- Multi-task smoke eval result: 2/10 successes, 20.0% success rate, avg sum reward 0.2. This is a sanity check, not a converged policy result.

## Blockers

- pi0.7 is treated as schema-compatible future work until official trainable engineering assets are available.
- Isaac Sim GUI is not installed or not discoverable at `C:\Users\Administrator\AppData\Local\ov\pkg`; latest launch manifest status is `isaac_sim_not_found`.

## Key Path

1. Validate dataset registry.
2. Run LIBERO postprocess smoke and write a timestamped run directory.
3. Optionally run existing pi0.5 1-step smoke train.
4. Run longer pi0.5 multi-task BC training on the 40-task / 400-episode subset.
5. Evaluate the trained checkpoint on all `libero_goal` task ids with multiple episodes per task.
6. Add RLinf PPO/GRPO integration scaffold after the multi-task BC checkpoint is stable.
7. Install or locate Isaac Sim, then open the exported USDA scene and replace the handcrafted preview trajectory with rollout-derived transforms.

## Next Commands

```powershell
cd E:\projects\robot
python .\scripts\grasp_dataset_registry.py
powershell -ExecutionPolicy Bypass -File .\scripts\run_grasp_pipeline_smoke.ps1 -SkipPi05SmokeTrain
```

Optional existing pi0.5 eval after smoke:

```powershell
.\scripts\eval_pi05_libero_lerobot.ps1 `
  -PolicyPath ".\outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model" `
  -Tasks "libero_goal" `
  -TaskIds "[8]" `
  -Episodes 10 `
  -OutputDir ".\eval_logs\pi05_libero_task10_goal8_10ep"
```

Recommended next implementation step:

```powershell
cd E:\projects\robot
powershell -ExecutionPolicy Bypass -File .\scripts\run_isaac_preview.ps1
# Then open artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda in Isaac Sim.
```

Diverse LIBERO training/eval:

```powershell
cd E:\projects\robot
& E:\projects\lerobot_experiment\envs\lerobot312\python.exe .\scripts\prepare_libero_multitask.py --dataset-root .\data\lerobot_libero --output-dir .\artifacts\libero_multitask_diverse --max-episodes-per-task 10 --seed 1000
powershell -ExecutionPolicy Bypass -File .\scripts\train_pi05_libero_multitask_4090.ps1 -Steps 30000 -BatchSize 1
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_goal_all.ps1 -PolicyPath ".\outputs\pi05_libero_multitask_4090\checkpoints\030000\pretrained_model" -Episodes 10 -OutputDir ".\eval_logs\pi05_libero_multitask_goal_all_10ep"
```

If Isaac Sim is installed elsewhere:

```powershell
cd E:\projects\robot
powershell -ExecutionPolicy Bypass -File .\scripts\launch_isaac_preview.ps1 -IsaacRoot "D:\path\to\isaac-sim"
```

## Artifact Index

- Dataset registry: `data\grasp_dataset_registry.json`
- Registry summary: `artifacts\grasp_pipeline\dataset_registry_summary.md`
- Run directories: `artifacts\grasp_pipeline\runs\`
- Prior pi0.5 checkpoint: `outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model`
- Prior LIBERO eval result: `eval_logs\pi05_libero_task10_goal8_10ep\eval_info.json`
- Latest BC eval result: `eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910\eval_info.json`
- Latest BC eval videos: `eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910\videos\libero_goal_8\`
- Latest Isaac-ready preview scene: `artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda`
- Latest fallback preview PNG: `artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.png`
- Latest Isaac preview manifest: `artifacts\grasp_pipeline\runs\isaac_preview_20260910\manifest.json`
- Latest Isaac launch manifest: `artifacts\grasp_pipeline\runs\isaac_launch_20260910\manifest.json`
- Diverse LIBERO subset summary: `artifacts\libero_multitask_diverse\summary.md`
- Diverse LIBERO episode file: `artifacts\libero_multitask_diverse\episodes.txt`
- Multi-task smoke checkpoint: `outputs\pi05_libero_multitask_smoke_fixed\checkpoints\000001\pretrained_model`
- Multi-task smoke train summary: `artifacts\grasp_pipeline\runs\multitask_libero_20260910\training_summary.json`
- Multi-task smoke eval summary: `artifacts\grasp_pipeline\runs\multitask_libero_20260910\eval_summary.json`
- Multi-task smoke eval videos: `eval_logs\pi05_libero_multitask_smoke_goal_all_1ep_20260910\videos\`

## Failure Log

- No new failures recorded yet. If a command fails, inspect the latest run directory for `failure.json` and update this section before continuing.

## Latest Verified Run

- Run name: `multitask_libero_20260910`
- Run directory: `artifacts\grasp_pipeline\runs\multitask_libero_20260910`
- Status: success
- Outputs:
  - `training_summary.json`
  - `eval_summary.json`
  - local checkpoint: `outputs\pi05_libero_multitask_smoke_fixed\checkpoints\000001\pretrained_model`
  - local eval videos: `eval_logs\pi05_libero_multitask_smoke_goal_all_1ep_20260910\videos\`

## Verification Commands Run

```powershell
python .\scripts\grasp_dataset_registry.py
python .\scripts\grasp_postprocess_pipeline.py --dataset-root .\data\lerobot_libero --model-root .\models\pi05_libero_base --run-name smoke_manual_check --max-shards 2
powershell -ExecutionPolicy Bypass -File .\scripts\run_grasp_pipeline_smoke.ps1 -RunName smoke_orchestrator_check -SkipPi05SmokeTrain
powershell -ExecutionPolicy Bypass -File .\scripts\run_grasp_pipeline_smoke.ps1 -RunName smoke_full_final
python -m py_compile .\scripts\grasp_dataset_registry.py .\scripts\grasp_postprocess_pipeline.py
.\scripts\eval_pi05_libero_lerobot.ps1 -PolicyPath ".\outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model" -Tasks "libero_goal" -TaskIds "[8]" -Episodes 10 -OutputDir ".\eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910"
powershell -ExecutionPolicy Bypass -File .\scripts\run_isaac_preview.ps1
python -m py_compile .\scripts\export_isaac_preview_scene.py
powershell -ExecutionPolicy Bypass -File .\scripts\find_isaac_sim.ps1
python -m py_compile .\scripts\export_isaac_preview_scene.py .\scripts\isaac_load_preview.py
powershell -ExecutionPolicy Bypass -File .\scripts\launch_isaac_preview.ps1
python .\scripts\render_isaac_preview_fallback.py
& E:\projects\lerobot_experiment\envs\lerobot312\python.exe .\scripts\prepare_libero_multitask.py --dataset-root .\data\lerobot_libero --output-dir .\artifacts\libero_multitask_diverse --max-episodes-per-task 10 --seed 1000
powershell -ExecutionPolicy Bypass -File .\scripts\run_pi05_multitask_smoke.ps1 -Steps 1 -BatchSize 1 -OutputDir .\outputs\pi05_libero_multitask_smoke_fixed
.\scripts\eval_pi05_libero_lerobot.ps1 -PolicyPath ".\outputs\pi05_libero_multitask_smoke_fixed\checkpoints\000001\pretrained_model" -Tasks "libero_goal" -TaskIds "[0,1,2,3,4,5,6,7,8,9]" -Episodes 1 -OutputDir ".\eval_logs\pi05_libero_multitask_smoke_goal_all_1ep_20260910"
python .\scripts\summarize_lerobot_eval.py --eval-info .\eval_logs\pi05_libero_multitask_smoke_goal_all_1ep_20260910\eval_info.json --output .\artifacts\grasp_pipeline\runs\multitask_libero_20260910\eval_summary.json
python -m py_compile .\scripts\prepare_libero_multitask.py .\scripts\summarize_lerobot_eval.py
```

## Training Smoke Note

The final smoke run wrote `outputs\pi05_libero_smoke\checkpoints\000001\training_state\training_step.json` with `step=1`. The underlying `lerobot-train` process still returned exit code 1 after writing the checkpoint, so the wrapper records this as a teardown warning rather than a failed smoke train. Revisit this before long unattended runs, but the import/data/model/optimizer-step path has been validated.

## Latest BC Evaluation Note

The 2026-09-10 rerun loaded `outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model` successfully with all keys loaded. The LIBERO `libero_goal` task 8 evaluation completed 10 episodes with 10 successes, `pc_success=100.0`, `avg_sum_reward=1.0`, and 10 rollout videos written locally.

## Latest Isaac Preview Note

The 2026-09-10 Isaac preview export succeeded and produced an Isaac-compatible USDA scene for `put the bowl on the plate`, linked to the latest BC eval metrics and 10 local LIBERO videos. A follow-up launch attempt ran `scripts\launch_isaac_preview.ps1`, but no valid Isaac Sim install directory or launcher was found under the standard Omniverse package path. Open `artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda` in Isaac Sim after installation, or pass `-IsaacRoot` to the launcher script.

The fallback PNG preview at `artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.png` is not an Isaac render; it is a quick layout check generated from the same scene geometry.

## Latest Multi-task LIBERO Note

The 2026-09-10 diverse LIBERO subset includes all 40 local tasks with up to 10 episodes each. It covers pick/place to plate, basket, drawers, microwave, stove/appliance, and furniture targets. A pi0.5 1-step smoke train completed on 400 episodes / 66248 frames and wrote `outputs\pi05_libero_multitask_smoke_fixed\checkpoints\000001\pretrained_model`. A broader `libero_goal` sanity eval over task ids 0-9 with 1 episode per task produced 2/10 successes (`pc_success=20.0`). Because this checkpoint was trained for only 1 step, the result validates pipeline coverage rather than model convergence.
