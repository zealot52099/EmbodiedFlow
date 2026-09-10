param(
    [int]$BatchSize = 8,
    [int]$Steps = 30000,
    [int]$SaveFreq = 5000,
    [string]$OutputDir = ".\outputs\pi05_libero_spatial_4090",
    [string]$JobName = "pi05_libero_spatial_4090",
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
$env:HF_ENDPOINT = $null
$env:HF_HUB_DISABLE_XET = "1"
$env:HF_HUB_ENABLE_HF_TRANSFER = "0"

$expectedModelBytes = 14467165872
$modelFile = Join-Path $PretrainedPath "model.safetensors"
if (-not (Test-Path -LiteralPath $modelFile)) {
    throw "Missing Pi 0.5 checkpoint: $modelFile"
}
$modelSize = (Get-Item -LiteralPath $modelFile).Length
if ($modelSize -lt $expectedModelBytes) {
    throw "Incomplete Pi 0.5 checkpoint: $modelFile is $modelSize bytes, expected $expectedModelBytes bytes."
}

$lerobotTrain = "E:\projects\lerobot_experiment\envs\lerobot312\Scripts\lerobot-train.exe"
if (-not (Test-Path -LiteralPath $lerobotTrain)) {
    $cmd = Get-Command lerobot-train -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        throw "lerobot-train not found. Install with: pip install 'lerobot[pi]'"
    }
    $lerobotTrain = $cmd.Source
}

Write-Host "Launching Pi 0.5 expert-only behavior cloning on lerobot/libero."
Write-Host "BatchSize=$BatchSize Steps=$Steps OutputDir=$OutputDir"

$episodeArgs = @()
if ($EpisodesFile -and (Test-Path -LiteralPath $EpisodesFile)) {
    $episodesText = (Get-Content -LiteralPath $EpisodesFile -Raw).Trim()
    if ($episodesText) {
        $episodeArgs = @("--dataset.episodes=[$episodesText]")
        Write-Host "Using task episode subset from $EpisodesFile"
        Write-Host "Episodes=[$episodesText]"
    }
}

& $lerobotTrain `
  --dataset.repo_id=lerobot/libero `
  --dataset.root=$DatasetRoot `
  @episodeArgs `
  --policy.type=pi05 `
  --policy.pretrained_path=$PretrainedPath `
  --policy.normalization_mapping='{"ACTION": "MEAN_STD", "STATE": "MEAN_STD", "VISUAL": "IDENTITY"}' `
  --policy.n_action_steps=10 `
  --policy.empty_cameras=1 `
  --policy.freeze_vision_encoder=true `
  --policy.train_expert_only=true `
  --policy.gradient_checkpointing=true `
  --policy.dtype=bfloat16 `
  --policy.device=cuda `
  --policy.push_to_hub=false `
  --output_dir=$OutputDir `
  --job_name=$JobName `
  --batch_size=$BatchSize `
  --num_workers=4 `
  --steps=$Steps `
  --save_freq=$SaveFreq `
  --seed=1000

if ($LASTEXITCODE -ne 0) {
    $checkpointName = "{0:D6}" -f $Steps
    $expectedStepFile = Join-Path $OutputDir "checkpoints\$checkpointName\training_state\training_step.json"
    if (Test-Path -LiteralPath $expectedStepFile) {
        Write-Warning "lerobot-train exited with code $LASTEXITCODE after writing $expectedStepFile. Treating this as a completed run with a teardown warning."
    } else {
        throw "lerobot-train failed with exit code $LASTEXITCODE and did not write $expectedStepFile"
    }
}
