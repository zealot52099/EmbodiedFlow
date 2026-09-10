param(
    [int]$SmokeBatchSize = 1,
    [int]$TrainBatchSize = 8,
    [int]$TrainSteps = 30000,
    [string]$DatasetRoot = ".\data\lerobot_libero",
    [string]$PretrainedPath = ".\models\pi05_libero_base",
    [string]$OutputDir = ".\outputs\pi05_libero_spatial_4090",
    [string]$EpisodesFile = ".\artifacts\libero_task10\episodes.txt",
    [switch]$SkipSmoke,
    [switch]$SkipTrain
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

Write-Host "== Step 1: verify dataset and Pi 0.5 checkpoint =="
.\scripts\verify_pi05_task.ps1 -DatasetRoot $DatasetRoot -ModelRoot $PretrainedPath

if (-not $SkipSmoke) {
    Write-Host "== Step 2: run 1-step smoke training =="
    .\scripts\run_smoke_train_pi05.ps1 `
      -BatchSize $SmokeBatchSize `
      -Steps 1 `
      -DatasetRoot $DatasetRoot `
      -PretrainedPath $PretrainedPath `
      -EpisodesFile $EpisodesFile
}

if (-not $SkipTrain) {
    Write-Host "== Step 3: run full 4090 training =="
    .\scripts\train_pi05_libero_4090.ps1 `
      -BatchSize $TrainBatchSize `
      -Steps $TrainSteps `
      -DatasetRoot $DatasetRoot `
      -PretrainedPath $PretrainedPath `
      -OutputDir $OutputDir `
      -EpisodesFile $EpisodesFile
}

Write-Host "Pipeline completed."
