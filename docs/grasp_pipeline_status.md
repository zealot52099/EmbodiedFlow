# Grasp Pipeline Status

Updated: 2026-09-11

## Goal

Implement a resumable research prototype for generic multi-robot grasp/place tasks:
dataset registry, adapter-ready postprocessing, pi0.5/pi0.7-ready training workflow, MuJoCo/LIBERO evaluation, and Isaac Sim visualization planning.

## Current Stage

Implementation stage: v1 smoke infrastructure, single-task pi0.5 BC eval, diverse LIBERO multi-task full training/eval, Isaac-ready preview export, obstacle-avoidance curriculum planning, and MuJoCo obstacle eval smoke are validated.

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
- Ran full pi0.5 diverse multi-task BC training for 30000 steps on the 40-task / 400-episode subset.
- Full multi-task train result: final checkpoint `outputs\pi05_libero_multitask_4090\checkpoints\030000\pretrained_model`; final logged loss 0.217, grad norm 2.262, lr 2.5e-06, memory 12.85 GB.
- Ran full `libero_goal` task ids 0-9 eval with 10 episodes per task using the 30000-step multi-task checkpoint.
- Full multi-task eval result: 95/100 successes, 95.0% success rate, avg sum reward 0.95, avg max reward 0.95, 100 rollout videos.
- Added obstacle-avoidance curriculum generator: `scripts\prepare_libero_obstacle_curriculum.py`.
- Added obstacle readiness summarizer: `scripts\summarize_obstacle_readiness.py`.
- Added MuJoCo obstacle XML injector smoke tool: `scripts\libero_obstacle_xml_injector.py`.
- Added obstacle curriculum wrapper: `scripts\run_obstacle_curriculum_plan.ps1`.
- Generated obstacle curriculum: 50 scenarios, 450 planned episodes for `libero_goal` task ids 0-9.
- Generated obstacle readiness report from the 30000-step checkpoint eval. Priority task ids for obstacle data collection are 2, 3, and 9; prioritized stage-1 collection is 310 episodes.
- Generated obstacle injector smoke XML: `artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911\obstacle_injector_smoke.xml`.
- Added obstacle-injected LIBERO eval runner: `scripts\eval_pi05_libero_obstacle.py`.
- Added obstacle eval smoke wrapper: `scripts\eval_pi05_libero_obstacle_smoke.ps1`.
- Ran obstacle eval smoke on `libero_goal_00_easy_00` for 1 episode: task success 100.0%, avoidance success 100.0%, collision episode count 0.
- Ran priority obstacle eval smoke on `libero_goal_02_easy_00`, `libero_goal_03_easy_00`, and `libero_goal_09_easy_00` for 1 episode each: task success 66.7%, avoidance success 66.7%, collision episode count 0; failed scenario was `libero_goal_03_easy_00`.
- Fixed obstacle eval injection lifecycle so obstacles are injected after each LIBERO rollout reset from a cached base MuJoCo XML instead of being lost on reset.
- Added obstacle minimum-clearance telemetry to `scripts\eval_pi05_libero_obstacle.py` using a conservative geom center-distance minus `geom_rbound` proxy.
- Ran broader easy obstacle eval over `libero_goal` task ids 0-9: 10 easy scenarios, 3 episodes per scenario, 30/30 task successes, 100.0% safety success, 100.0% avoidance success, 0 collision episodes, 0 clearance violations, min clearance 0.503 m.
- Installed Isaac Sim 6.1.0.0 via pip/conda into `E:\envs\isaacsim61` with launcher `E:\envs\isaacsim61\Scripts\isaacsim.exe`.
- Updated Isaac detection/preview launch scripts to recognize the pip/conda install at `E:\envs\isaacsim61`.
- Verified Isaac Sim headless stage load with `scripts\isaac_load_preview.py`: the exported `put_bowl_on_plate_preview.usda` opened successfully, Isaac detected the RTX 4090, and Warp detected CUDA.
- Fixed pip-mode Isaac preview launcher to call `E:\envs\isaacsim61\python.exe scripts\isaac_load_preview.py --scene ...` instead of passing a USDA path as the first `isaacsim.exe` positional argument.
- Verified Isaac GUI preview launch after keeping the SimulationApp loop alive: process `E:\envs\isaacsim61\python.exe` stayed running after 120 seconds with window title `Isaac Sim Python 6.1.0` and loaded `put_bowl_on_plate_preview.usda`.

## Blockers

- pi0.7 is treated as schema-compatible future work until official trainable engineering assets are available.
- Isaac Sim 6.1.0.0 is installed at `E:\envs\isaacsim61`, but first launch is blocked until the user reviews/accepts the NVIDIA Omniverse EULA. Host platform risk remains: Windows 10 and NVIDIA driver 560.81 are below the current Isaac Sim 6.x documented Windows support/recommendation.

## Key Path

1. Validate dataset registry.
2. Run LIBERO postprocess smoke and write a timestamped run directory.
3. Optionally run existing pi0.5 1-step smoke train.
4. Completed: run a broader easy obstacle eval over all `libero_goal` task ids with multiple seeds.
5. Completed: add minimum clearance telemetry using a conservative MuJoCo geom proxy.
6. Run medium obstacle eval over all `libero_goal` task ids, starting with 3 episodes per selected medium scenario.
7. Collect planner-first expert trajectories for priority weak tasks, starting with task ids 2, 3, and 9.
8. Fine-tune from `outputs\pi05_libero_multitask_4090\checkpoints\030000\pretrained_model` with a 60/40 mix of obstacle expert and original multi-task data.
9. Add RLinf PPO/GRPO integration after collision-aware BC reaches >=90% avoidance success on easy+medium scenarios.
10. Install or locate Isaac Sim, then open the exported USDA scene and replace the handcrafted preview trajectory with rollout-derived transforms.

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

Diverse LIBERO training/eval, already completed for the 30000-step checkpoint:

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

Obstacle-avoidance curriculum planning:

```powershell
cd E:\projects\robot
powershell -ExecutionPolicy Bypass -File .\scripts\run_obstacle_curriculum_plan.ps1
```

Obstacle-injected LIBERO eval smoke:

```powershell
cd E:\projects\robot
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_obstacle_smoke.ps1 -TaskIds "2,3,9" -Difficulties "easy" -ScenarioLimit 3 -Episodes 1 -OutputDir ".\eval_logs\pi05_libero_obstacle_priority_easy_3scenarios_1ep"
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
- Latest Isaac install manifest: `artifacts\grasp_pipeline\runs\isaac_install_20260911\manifest.json`
- Latest Isaac verification manifest: `artifacts\grasp_pipeline\runs\isaac_verify_20260911\manifest.json`
- Latest Isaac GUI preview verification: `artifacts\grasp_pipeline\runs\isaac_gui_preview_verify_hold_20260911\verification.json`
- Diverse LIBERO subset summary: `artifacts\libero_multitask_diverse\summary.md`
- Diverse LIBERO episode file: `artifacts\libero_multitask_diverse\episodes.txt`
- Multi-task smoke checkpoint: `outputs\pi05_libero_multitask_smoke_fixed\checkpoints\000001\pretrained_model`
- Multi-task smoke train summary: `artifacts\grasp_pipeline\runs\multitask_libero_20260910\training_summary.json`
- Multi-task smoke eval summary: `artifacts\grasp_pipeline\runs\multitask_libero_20260910\eval_summary.json`
- Multi-task smoke eval videos: `eval_logs\pi05_libero_multitask_smoke_goal_all_1ep_20260910\videos\`
- Full multi-task checkpoint: `outputs\pi05_libero_multitask_4090\checkpoints\030000\pretrained_model`
- Full multi-task train summary: `artifacts\grasp_pipeline\runs\multitask_libero_full_20260911\training_summary.json`
- Full multi-task eval summary: `artifacts\grasp_pipeline\runs\multitask_libero_full_20260911\eval_summary.json`
- Full multi-task eval videos: `eval_logs\pi05_libero_multitask_goal_all_10ep\videos\`
- Obstacle curriculum: `artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911\obstacle_curriculum.json`
- Obstacle readiness report: `artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911\readiness_report.json`
- Obstacle curriculum summary: `artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911\summary.md`
- Obstacle injector smoke XML: `artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911\obstacle_injector_smoke.xml`
- Obstacle eval smoke summary: `eval_logs\pi05_libero_obstacle_smoke_task0_easy_1ep_v2\obstacle_eval_summary.json`
- Priority obstacle eval smoke summary: `eval_logs\pi05_libero_obstacle_priority_easy_3scenarios_1ep\obstacle_eval_summary.json`
- Obstacle eval smoke manifest: `artifacts\grasp_pipeline\runs\obstacle_eval_smoke_20260911\manifest.json`
- Latest easy obstacle eval summary: `eval_logs\pi05_libero_obstacle_goal_easy_all_3ep_clearance\obstacle_eval_summary.json`
- Latest easy obstacle eval videos: `eval_logs\pi05_libero_obstacle_goal_easy_all_3ep_clearance\videos\`
- Latest easy obstacle eval manifest: `artifacts\grasp_pipeline\runs\obstacle_eval_easy_all_20260911\manifest.json`

## Failure Log

- No new failures recorded yet. If a command fails, inspect the latest run directory for `failure.json` and update this section before continuing.

## Latest Verified Run

- Run name: `obstacle_eval_easy_all_20260911`
- Run directory: `artifacts\grasp_pipeline\runs\obstacle_eval_easy_all_20260911`
- Status: success
- Outputs:
  - `manifest.json`
  - local easy eval: `eval_logs\pi05_libero_obstacle_goal_easy_all_3ep_clearance\obstacle_eval_summary.json`
  - local easy eval videos: `eval_logs\pi05_libero_obstacle_goal_easy_all_3ep_clearance\videos\`

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
$env:OMNI_KIT_ACCEPT_EULA="YES"; & E:\envs\isaacsim61\python.exe .\scripts\isaac_load_preview.py --scene .\artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda --headless --frames 5
python -m py_compile .\scripts\export_isaac_preview_scene.py .\scripts\isaac_load_preview.py
powershell -ExecutionPolicy Bypass -File .\scripts\launch_isaac_preview.ps1
python .\scripts\render_isaac_preview_fallback.py
& E:\projects\lerobot_experiment\envs\lerobot312\python.exe .\scripts\prepare_libero_multitask.py --dataset-root .\data\lerobot_libero --output-dir .\artifacts\libero_multitask_diverse --max-episodes-per-task 10 --seed 1000
powershell -ExecutionPolicy Bypass -File .\scripts\run_pi05_multitask_smoke.ps1 -Steps 1 -BatchSize 1 -OutputDir .\outputs\pi05_libero_multitask_smoke_fixed
.\scripts\eval_pi05_libero_lerobot.ps1 -PolicyPath ".\outputs\pi05_libero_multitask_smoke_fixed\checkpoints\000001\pretrained_model" -Tasks "libero_goal" -TaskIds "[0,1,2,3,4,5,6,7,8,9]" -Episodes 1 -OutputDir ".\eval_logs\pi05_libero_multitask_smoke_goal_all_1ep_20260910"
python .\scripts\summarize_lerobot_eval.py --eval-info .\eval_logs\pi05_libero_multitask_smoke_goal_all_1ep_20260910\eval_info.json --output .\artifacts\grasp_pipeline\runs\multitask_libero_20260910\eval_summary.json
python -m py_compile .\scripts\prepare_libero_multitask.py .\scripts\summarize_lerobot_eval.py
powershell -ExecutionPolicy Bypass -File .\scripts\train_pi05_libero_multitask_4090.ps1 -Steps 30000 -BatchSize 1
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_goal_all.ps1 -PolicyPath ".\outputs\pi05_libero_multitask_4090\checkpoints\030000\pretrained_model" -Episodes 10 -OutputDir ".\eval_logs\pi05_libero_multitask_goal_all_10ep"
python -m py_compile .\scripts\prepare_libero_obstacle_curriculum.py .\scripts\summarize_obstacle_readiness.py .\scripts\libero_obstacle_xml_injector.py
powershell -ExecutionPolicy Bypass -File .\scripts\run_obstacle_curriculum_plan.ps1
python -m py_compile .\scripts\eval_pi05_libero_obstacle.py
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_obstacle_smoke.ps1 -TaskIds "0" -Difficulties "easy" -ScenarioLimit 1 -Episodes 1 -OutputDir ".\eval_logs\pi05_libero_obstacle_smoke_task0_easy_1ep_v2"
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_obstacle_smoke.ps1 -TaskIds "2,3,9" -Difficulties "easy" -ScenarioLimit 3 -Episodes 1 -OutputDir ".\eval_logs\pi05_libero_obstacle_priority_easy_3scenarios_1ep"
& E:\projects\lerobot_experiment\envs\lerobot312\python.exe -m py_compile .\scripts\eval_pi05_libero_obstacle.py
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_obstacle_smoke.ps1 -TaskIds "3" -Difficulties "easy" -ScenarioLimit 1 -Episodes 1 -OutputDir ".\eval_logs\pi05_libero_obstacle_task3_easy_clearance_1ep_v3"
powershell -ExecutionPolicy Bypass -File .\scripts\eval_pi05_libero_obstacle_smoke.ps1 -TaskIds "0,1,2,3,4,5,6,7,8,9" -Difficulties "easy" -ScenarioLimit 0 -Episodes 3 -OutputDir ".\eval_logs\pi05_libero_obstacle_goal_easy_all_3ep_clearance"
& E:\miniconda3\Scripts\conda.exe create -y -p E:\envs\isaacsim61 python=3.12
& E:\envs\isaacsim61\python.exe -m pip install "isaacsim[all,extscache]==6.1.0" --extra-index-url https://pypi.nvidia.com
& E:\envs\isaacsim61\python.exe -m pip install "isaacsim[compatibility-check]==6.1.0.0" --extra-index-url https://pypi.nvidia.com
& E:\envs\isaacsim61\python.exe -m pip check
powershell -ExecutionPolicy Bypass -File .\scripts\find_isaac_sim.ps1
```

## Training Smoke Note

The final smoke run wrote `outputs\pi05_libero_smoke\checkpoints\000001\training_state\training_step.json` with `step=1`. The underlying `lerobot-train` process still returned exit code 1 after writing the checkpoint, so the wrapper records this as a teardown warning rather than a failed smoke train. Revisit this before long unattended runs, but the import/data/model/optimizer-step path has been validated.

## Latest BC Evaluation Note

The 2026-09-10 rerun loaded `outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model` successfully with all keys loaded. The LIBERO `libero_goal` task 8 evaluation completed 10 episodes with 10 successes, `pc_success=100.0`, `avg_sum_reward=1.0`, and 10 rollout videos written locally.

## Latest Isaac Preview Note

The 2026-09-10 Isaac preview export succeeded and produced an Isaac-compatible USDA scene for `put the bowl on the plate`, linked to the latest BC eval metrics and 10 local LIBERO videos. Isaac Sim 6.1.0.0 is now installed via pip/conda at `E:\envs\isaacsim61`, and `scripts\find_isaac_sim.ps1` detects it. After the user accepted the NVIDIA Omniverse EULA, a headless verification opened `artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda`, updated 5 frames, detected the RTX 4090, and initialized Warp with CUDA. The pip-mode launcher was fixed to use `E:\envs\isaacsim61\python.exe scripts\isaac_load_preview.py --scene ...`; directly passing a USDA path as the first `isaacsim.exe` positional argument is invalid because that position is parsed as a Kit experience. A GUI launch was then verified after updating `scripts\isaac_load_preview.py` to keep the SimulationApp loop alive: process `30792` remained running after 120 seconds with window title `Isaac Sim Python 6.1.0`. Host platform risk remains because the machine is Windows 10 with NVIDIA driver 560.81, while current Isaac Sim 6.x Windows guidance targets Windows 11 and a newer driver.

The fallback PNG preview at `artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.png` is not an Isaac render; it is a quick layout check generated from the same scene geometry.

## Latest Multi-task LIBERO Note

The 2026-09-10 diverse LIBERO subset includes all 40 local tasks with up to 10 episodes each. It covers pick/place to plate, basket, drawers, microwave, stove/appliance, and furniture targets. A pi0.5 1-step smoke train completed on 400 episodes / 66248 frames and wrote `outputs\pi05_libero_multitask_smoke_fixed\checkpoints\000001\pretrained_model`. A broader `libero_goal` sanity eval over task ids 0-9 with 1 episode per task produced 2/10 successes (`pc_success=20.0`). Because this checkpoint was trained for only 1 step, the result validates pipeline coverage rather than model convergence.

The 2026-09-11 full multi-task BC run completed 30000 steps with checkpoints every 5000 steps and final checkpoint `outputs\pi05_libero_multitask_4090\checkpoints\030000\pretrained_model`. Evaluation on `libero_goal` task ids 0-9 with 10 episodes per task produced 95/100 successes (`pc_success=95.0`). Per-task success rates: task 0 100%, task 1 100%, task 2 80%, task 3 80%, task 4 100%, task 5 100%, task 6 100%, task 7 100%, task 8 100%, task 9 90%.

## Latest Obstacle-Avoidance Note

The 2026-09-11 obstacle curriculum planning run created `artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911\obstacle_curriculum.json` with 50 scenarios and 450 planned episodes across easy, medium, and hard obstacle layouts. The readiness report uses the latest 30000-step eval summary and prioritizes task ids 2, 3, and 9 for first-stage obstacle expert data collection. A MuJoCo XML injector smoke file was generated at `artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911\obstacle_injector_smoke.xml`. This is a planning/data-collection artifact plus injector smoke test, not yet a full LIBERO obstacle-injected evaluation result.

## Latest Obstacle Eval Note

The 2026-09-11 obstacle eval runner now injects MuJoCo obstacle geoms after each LIBERO rollout reset and records conservative minimum-clearance telemetry. The earlier smoke run found a task-3 timeout, but that run used the pre-fix injection lifecycle and should be treated as smoke-only. The fixed runner completed `libero_goal` task ids 0-9 on all 10 easy scenarios with 3 episodes each: 30/30 task successes, 100.0% task success, 100.0% safety success, 100.0% avoidance success, 0 collision episodes, 0 clearance violations, min clearance 0.503 m, and mean episode-min clearance 0.555 m. The weakest easy clearance was `libero_goal_05_easy_00` at 0.503 m, still well above the 0.04 m margin.
