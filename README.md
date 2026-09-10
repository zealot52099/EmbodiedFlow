# EmbodiedFlow

Resumable research prototype for generic multi-robot grasp/place tasks.

## What Is In This Repo

- Dataset registry for teleoperation, ego, UMI, and simulation sources.
- Adapter-ready postprocessing smoke pipeline for LeRobot/LIBERO data.
- pi0.5 training smoke orchestration built around the existing local LIBERO setup.
- pi0.7-ready schema decisions for future trainable pi0.7 integration.
- Resume logs and manifests under `artifacts/grasp_pipeline`.

## Resume A Session

Read these files first:

1. `docs/grasp_pipeline_status.md`
2. `docs/grasp_pipeline_decisions.md`
3. Latest `artifacts/grasp_pipeline/runs/*/orchestrator_manifest.json`

The latest verified run at the time of this commit is:

```text
artifacts/grasp_pipeline/runs/smoke_full_final
```

## Smoke Commands

```powershell
cd E:\projects\robot
python .\scripts\grasp_dataset_registry.py
powershell -ExecutionPolicy Bypass -File .\scripts\run_grasp_pipeline_smoke.ps1 -RunName smoke_full_final
```

Large datasets, model weights, checkpoints, and rollout videos are intentionally ignored by Git.
