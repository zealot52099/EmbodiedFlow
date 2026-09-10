# Grasp Pipeline Decisions

Updated: 2026-09-10

## Locked Decisions

- Goal shape: research prototype, not a full production platform.
- Workspace: `E:\projects\robot`.
- Task family: generic multi-robot grasp/place manipulation.
- v1 execution anchor: local LIBERO + pi0.5 assets already present in this project.
- Evaluation split: MuJoCo/LIBERO first for measurable success rate; Isaac Sim second for high-fidelity 3D replay and demonstration.
- Training order: behavior cloning/SFT first, RL after a stable BC checkpoint.
- pi0.5 default: frozen VLM, train expert/action head, bf16, gradient checkpointing, single RTX 4090 friendly.
- pi0.7 default: pi0.7-ready input/context schema only until official trainable weights/tooling are available.
- Ego data policy: Ego datasets may produce semantic labels, affordance hints, and subgoal images; they must not be treated as low-level robot action trajectories.

## Interfaces

- Dataset categories are exactly `teleop`, `ego`, `umi`, and `sim`.
- Registry source of truth: `data/grasp_dataset_registry.json`.
- Run artifacts are stored under `artifacts/grasp_pipeline/runs/<run_name>/`.
- Each run directory should contain `env.json`, `config.json`, `manifest.json` or `failure.json`, and a `run.log`.
- Normalized output should follow a LeRobot-style episode manifest with images, state, action, language, task metadata, and embodiment metadata.

## Resume Contract

To resume in a new conversation, read these files first:

1. `docs/grasp_pipeline_status.md`
2. `docs/grasp_pipeline_decisions.md`
3. The latest `artifacts/grasp_pipeline/runs/*/manifest.json` or `failure.json`

The next action must be taken from the status file unless a newer run manifest clearly supersedes it.
