param(
    [int]$BatchSize = 1,
    [int]$Steps = 1,
    [string]$OutputDir = ".\outputs\pi05_libero_smoke",
    [string]$DatasetRoot = ".\data\lerobot_libero",
    [string]$PretrainedPath = ".\models\pi05_libero_base",
    [string]$EpisodesFile = ".\artifacts\libero_task10\episodes.txt"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"

Write-Host "Running a Pi 0.5 smoke train. This verifies imports, dataset loading, model loading, and one optimizer step."

.\scripts\train_pi05_libero_4090.ps1 `
  -BatchSize $BatchSize `
  -Steps $Steps `
  -SaveFreq 0 `
  -OutputDir $OutputDir `
  -JobName "pi05_libero_smoke" `
  -DatasetRoot $DatasetRoot `
  -PretrainedPath $PretrainedPath `
  -EpisodesFile $EpisodesFile
