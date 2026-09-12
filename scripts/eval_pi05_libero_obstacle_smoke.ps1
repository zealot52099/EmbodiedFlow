param(
    [string]$PolicyPath = ".\outputs\pi05_libero_multitask_4090\checkpoints\030000\pretrained_model",
    [string]$Curriculum = ".\artifacts\grasp_pipeline\runs\obstacle_curriculum_20260911\obstacle_curriculum.json",
    [string]$TaskIds = "0",
    [string]$Difficulties = "easy",
    [int]$ScenarioLimit = 1,
    [int]$Episodes = 1,
    [string]$OutputDir = ".\eval_logs\pi05_libero_obstacle_smoke"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"
$env:HF_ENDPOINT = $null
$env:HF_HUB_DISABLE_XET = "1"
$env:HF_HUB_ENABLE_HF_TRANSFER = "0"

& "E:\projects\lerobot_experiment\envs\lerobot312\python.exe" `
  .\scripts\eval_pi05_libero_obstacle.py `
  --policy-path $PolicyPath `
  --curriculum $Curriculum `
  --task-ids $TaskIds `
  --difficulties $Difficulties `
  --scenario-limit $ScenarioLimit `
  --episodes $Episodes `
  --output-dir $OutputDir
