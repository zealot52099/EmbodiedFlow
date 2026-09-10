param(
    [string]$DatasetRoot = ".\data\lerobot_libero",
    [string]$ModelRoot = ".\models\pi05_libero_base"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$python = "E:\Project\lerobot_experiment\envs\lerobot312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Expected Python not found: $python"
}

& $python .\scripts\verify_pi05_task.py `
  --dataset-root $DatasetRoot `
  --model-root $ModelRoot `
  --output .\artifacts\pi05_task_verification.json
