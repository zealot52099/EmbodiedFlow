param(
    [int]$BatchSize = 8,
    [int]$Steps = 30000,
    [int]$SaveFreq = 5000,
    [string]$OutputDir = ".\outputs\pi05_libero_spatial_4090",
    [string]$JobName = "pi05_libero_spatial_4090",
    [string]$DatasetRoot = ".\data\lerobot_libero",
    [string]$PretrainedPath = ".\models\pi05_libero_base",
    [string]$EpisodesFile = ".\artifacts\libero_task10\episodes.txt",
    [string]$LogDir = ".\artifacts\training_logs"
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}
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

$python = "E:\projects\lerobot_experiment\envs\lerobot312\python.exe"
$usePythonModule = $true
if (-not (Test-Path -LiteralPath $python)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        throw "python not found. Activate the LeRobot environment first."
    }
    $python = $cmd.Source
}

Write-Host "Launching Pi 0.5 expert-only behavior cloning on lerobot/libero."
Write-Host "BatchSize=$BatchSize Steps=$Steps OutputDir=$OutputDir"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$safeJobName = $JobName -replace '[^A-Za-z0-9_.-]', '_'
$stdoutLog = Join-Path $LogDir "$safeJobName.stdout.log"
$stderrLog = Join-Path $LogDir "$safeJobName.stderr.log"
Write-Host "StdoutLog=$stdoutLog"
Write-Host "StderrLog=$stderrLog"

$episodeArgs = @()
if ($EpisodesFile -and (Test-Path -LiteralPath $EpisodesFile)) {
    $episodesText = (Get-Content -LiteralPath $EpisodesFile -Raw).Trim()
    if ($episodesText) {
        $episodeArgs = @("--dataset.episodes=[$episodesText]")
        Write-Host "Using task episode subset from $EpisodesFile"
        Write-Host "Episodes=[$episodesText]"
    }
}

$trainArgs = @(
  "--dataset.repo_id=lerobot/libero",
  "--dataset.root=$DatasetRoot"
)
$trainArgs += $episodeArgs
$trainArgs += @(
  "--policy.type=pi05",
  "--policy.pretrained_path=$PretrainedPath",
  '--policy.normalization_mapping={"ACTION":"MEAN_STD","STATE":"MEAN_STD","VISUAL":"IDENTITY"}',
  "--policy.n_action_steps=10",
  "--policy.empty_cameras=1",
  "--policy.freeze_vision_encoder=true",
  "--policy.train_expert_only=true",
  "--policy.gradient_checkpointing=true",
  "--policy.dtype=bfloat16",
  "--policy.device=cuda",
  "--policy.push_to_hub=false",
  "--output_dir=$OutputDir",
  "--job_name=$JobName",
  "--batch_size=$BatchSize",
  "--num_workers=4",
  "--steps=$Steps",
  "--save_freq=$SaveFreq",
  "--seed=1000"
)

function Quote-ProcessArg([string]$Value) {
    return '"' + ($Value -replace '"', '\"') + '"'
}

$processArgs = @("-m", "lerobot.scripts.lerobot_train") + $trainArgs
$argumentLine = ($processArgs | ForEach-Object { Quote-ProcessArg $_ }) -join " "
$process = Start-Process `
    -FilePath $python `
    -ArgumentList $argumentLine `
    -WorkingDirectory (Get-Location).Path `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -NoNewWindow `
    -Wait `
    -PassThru

if ($process.ExitCode -ne 0) {
    $checkpointName = "{0:D6}" -f $Steps
    $expectedStepFile = Join-Path $OutputDir "checkpoints\$checkpointName\training_state\training_step.json"
    if (Test-Path -LiteralPath $expectedStepFile) {
        Write-Warning "lerobot-train exited with code $($process.ExitCode) after writing $expectedStepFile. Treating this as a completed run with a teardown warning."
    } else {
        Write-Host "== lerobot-train stdout tail =="
        if (Test-Path -LiteralPath $stdoutLog) { Get-Content -LiteralPath $stdoutLog -Tail 80 }
        Write-Host "== lerobot-train stderr tail =="
        if (Test-Path -LiteralPath $stderrLog) { Get-Content -LiteralPath $stderrLog -Tail 120 }
        throw "lerobot-train failed with exit code $($process.ExitCode) and did not write $expectedStepFile"
    }
}

Write-Host "lerobot-train completed. Logs: $stdoutLog ; $stderrLog"
