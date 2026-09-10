param(
    [string]$DatasetRoot = ".\data\lerobot_libero",
    [string]$PretrainedPath = ".\models\pi05_libero_base",
    [string]$EpisodesFile = ".\artifacts\libero_multitask_diverse\episodes.txt",
    [string]$OutputDir = ".\outputs\pi05_libero_multitask_smoke",
    [int]$Steps = 1,
    [int]$BatchSize = 1
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"

if (-not (Test-Path -LiteralPath $EpisodesFile)) {
    throw "Missing diverse episodes file: $EpisodesFile. Run scripts\prepare_libero_multitask.py first."
}

Write-Host "Running pi0.5 diverse multi-task smoke train."
Write-Host "DatasetRoot=$DatasetRoot"
Write-Host "EpisodesFile=$EpisodesFile"
Write-Host "OutputDir=$OutputDir"
Write-Host "Steps=$Steps BatchSize=$BatchSize"

.\scripts\train_pi05_libero_4090.ps1 `
  -BatchSize $BatchSize `
  -Steps $Steps `
  -SaveFreq 0 `
  -OutputDir $OutputDir `
  -JobName "pi05_libero_multitask_smoke" `
  -DatasetRoot $DatasetRoot `
  -PretrainedPath $PretrainedPath `
  -EpisodesFile $EpisodesFile
