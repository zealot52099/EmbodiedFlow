param(
    [int]$BatchSize = 1,
    [int]$Steps = 30000,
    [int]$SaveFreq = 5000,
    [string]$DatasetRoot = ".\data\lerobot_libero",
    [string]$PretrainedPath = ".\models\pi05_libero_base",
    [string]$EpisodesFile = ".\artifacts\libero_multitask_diverse\episodes.txt",
    [string]$OutputDir = ".\outputs\pi05_libero_multitask_4090",
    [string]$LogDir = ".\artifacts\training_logs"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"

if (-not (Test-Path -LiteralPath $EpisodesFile)) {
    Write-Host "Diverse episode file missing; generating it first."
    & "E:\projects\lerobot_experiment\envs\lerobot312\python.exe" `
      .\scripts\prepare_libero_multitask.py `
      --dataset-root $DatasetRoot `
      --output-dir .\artifacts\libero_multitask_diverse `
      --max-episodes-per-task 10 `
      --seed 1000
}

.\scripts\train_pi05_libero_4090.ps1 `
  -BatchSize $BatchSize `
  -Steps $Steps `
  -SaveFreq $SaveFreq `
  -OutputDir $OutputDir `
  -JobName "pi05_libero_multitask_4090" `
  -DatasetRoot $DatasetRoot `
  -PretrainedPath $PretrainedPath `
  -EpisodesFile $EpisodesFile `
  -LogDir $LogDir
