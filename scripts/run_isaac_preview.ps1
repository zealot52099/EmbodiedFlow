param(
    [string]$OutputDir = ".\artifacts\grasp_pipeline\runs\isaac_preview_20260910",
    [string]$EvalInfo = ".\eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910\eval_info.json",
    [string]$VideoDir = ".\eval_logs\pi05_libero_task10_goal8_10ep_rerun_20260910\videos\libero_goal_8"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

Write-Host "== Isaac Sim preview/export =="
Write-Host "Workspace: $(Get-Location)"
Write-Host "OutputDir: $OutputDir"
Write-Host "EvalInfo: $EvalInfo"
Write-Host "VideoDir: $VideoDir"

python .\scripts\export_isaac_preview_scene.py `
  --output-dir $OutputDir `
  --eval-info $EvalInfo `
  --video-dir $VideoDir
