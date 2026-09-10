param(
    [string]$PolicyPath = ".\outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model",
    [string]$Tasks = "libero_goal",
    [string]$TaskIds = "[8]",
    [int]$Episodes = 10,
    [string]$OutputDir = ".\eval_logs\pi05_libero_task10_4090_utf8"
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:HF_ENDPOINT = $null
$env:HF_HUB_DISABLE_XET = "1"
$env:HF_HUB_ENABLE_HF_TRANSFER = "0"

$python = "E:\projects\lerobot_experiment\envs\lerobot312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        throw "python not found. Activate the LeRobot environment first."
    }
    $python = $cmd.Source
}

Write-Host "Evaluating policy with LIBERO simulation."
Write-Host "PolicyPath=$PolicyPath Tasks=$Tasks TaskIds=$TaskIds Episodes=$Episodes"

& $python -m lerobot.scripts.lerobot_eval `
  --output_dir=$OutputDir `
  --env.type=libero `
  --env.task=$Tasks `
  --env.task_ids=$TaskIds `
  --eval.batch_size=1 `
  --eval.n_episodes=$Episodes `
  --policy.path=$PolicyPath `
  --policy.n_action_steps=10 `
  --env.max_parallel_tasks=1

if ($LASTEXITCODE -ne 0) {
    throw "lerobot_eval failed with exit code $LASTEXITCODE"
}
