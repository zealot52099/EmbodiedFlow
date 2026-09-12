param(
    [string]$EvalSummary = ".\artifacts\grasp_pipeline\runs\multitask_libero_full_20260911\eval_summary.json",
    [string]$OutputDir = ".\artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911",
    [string]$TaskIds = "0,1,2,3,4,5,6,7,8,9"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

python .\scripts\prepare_libero_obstacle_curriculum.py `
  --task-ids $TaskIds `
  --output-dir $OutputDir

python .\scripts\summarize_obstacle_readiness.py `
  --eval-summary $EvalSummary `
  --curriculum (Join-Path $OutputDir "obstacle_curriculum.json") `
  --output (Join-Path $OutputDir "readiness_report.json")

python .\scripts\libero_obstacle_xml_injector.py `
  --curriculum (Join-Path $OutputDir "obstacle_curriculum.json") `
  --output (Join-Path $OutputDir "obstacle_injector_smoke.xml")
