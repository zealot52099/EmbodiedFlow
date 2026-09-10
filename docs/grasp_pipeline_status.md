# Grasp Pipeline Status

Updated: 2026-09-10

## Goal

Implement a resumable research prototype for generic multi-robot grasp/place tasks:
dataset registry, adapter-ready postprocessing, pi0.5/pi0.7-ready training workflow, MuJoCo/LIBERO evaluation, and Isaac Sim visualization planning.

## Current Stage

Implementation stage: v1 smoke infrastructure and pi0.5 BC evaluation are validated against the local LIBERO task.

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

## Blockers

- pi0.7 is treated as schema-compatible future work until official trainable engineering assets are available.
- Isaac Sim visualization is planned as a second platform layer; v1 smoke validation uses LIBERO/MuJoCo-compatible local assets.

## Key Path

1. Validate dataset registry.
2. Run LIBERO postprocess smoke and write a timestamped run directory.
3. Optionally run existing pi0.5 1-step smoke train.
4. Add RLinf PPO/GRPO integration scaffold now that BC smoke/eval are healthy.
5. Add Isaac Sim replay export once rollout trajectory format is stable.

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
# Add RLinf PPO/GRPO scaffold and a broader LIBERO suite eval wrapper.
```

## Artifact Index

- Dataset registry: `data\grasp_dataset_registry.json`
- Registry summary: `artifacts\grasp_pipeline\dataset_registry_summary.md`
- Run directories: `artifacts\grasp_pipeline\runs\`
- Prior pi0.5 checkpoint: `outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model`
- Prior LIBERO eval result: `eval_logs\pi05_libero_task10_goal8_10ep\eval_info.json`
- Latest BC eval result: `eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910\eval_info.json`
- Latest BC eval videos: `eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910\videos\libero_goal_8\`

## Failure Log

- No new failures recorded yet. If a command fails, inspect the latest run directory for `failure.json` and update this section before continuing.

## Latest Verified Run

- Run name: `eval_pi05_goal8_20260910`
- Run directory: `artifacts\grasp_pipeline\runs\eval_pi05_goal8_20260910`
- Status: success
- Outputs:
  - `eval_summary.json`
  - full eval info in ignored local output: `eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910\eval_info.json`
  - 10 local rollout videos in ignored local output: `eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910\videos\libero_goal_8\`

## Verification Commands Run

```powershell
python .\scripts\grasp_dataset_registry.py
python .\scripts\grasp_postprocess_pipeline.py --dataset-root .\data\lerobot_libero --model-root .\models\pi05_libero_base --run-name smoke_manual_check --max-shards 2
powershell -ExecutionPolicy Bypass -File .\scripts\run_grasp_pipeline_smoke.ps1 -RunName smoke_orchestrator_check -SkipPi05SmokeTrain
powershell -ExecutionPolicy Bypass -File .\scripts\run_grasp_pipeline_smoke.ps1 -RunName smoke_full_final
python -m py_compile .\scripts\grasp_dataset_registry.py .\scripts\grasp_postprocess_pipeline.py
.\scripts\eval_pi05_libero_lerobot.ps1 -PolicyPath ".\outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model" -Tasks "libero_goal" -TaskIds "[8]" -Episodes 10 -OutputDir ".\eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910"
```

## Training Smoke Note

The final smoke run wrote `outputs\pi05_libero_smoke\checkpoints\000001\training_state\training_step.json` with `step=1`. The underlying `lerobot-train` process still returned exit code 1 after writing the checkpoint, so the wrapper records this as a teardown warning rather than a failed smoke train. Revisit this before long unattended runs, but the import/data/model/optimizer-step path has been validated.

## Latest BC Evaluation Note

The 2026-09-10 rerun loaded `outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model` successfully with all keys loaded. The LIBERO `libero_goal` task 8 evaluation completed 10 episodes with 10 successes, `pc_success=100.0`, `avg_sum_reward=1.0`, and 10 rollout videos written locally.
