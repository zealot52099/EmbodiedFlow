param(
    [string]$DatasetRoot = ".\data\lerobot_libero",
    [string]$ModelRoot = ".\models\pi05_libero_base",
    [string]$RunRoot = ".\artifacts\grasp_pipeline\runs",
    [string]$RunName = "",
    [switch]$SkipRegistry,
    [switch]$SkipPostprocess,
    [switch]$SkipPi05SmokeTrain
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"

$Workspace = (Get-Location).Path
if ($RunName -eq "") {
    $RunName = "smoke_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
}
$ResolvedRunRoot = (Resolve-Path -LiteralPath $RunRoot -ErrorAction SilentlyContinue)
if ($null -eq $ResolvedRunRoot) {
    New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
    $ResolvedRunRoot = Resolve-Path -LiteralPath $RunRoot
}
$RunDir = Join-Path $ResolvedRunRoot.Path $RunName
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

$TranscriptPath = Join-Path $RunDir "orchestrator.log"
Start-Transcript -Path $TranscriptPath -Force | Out-Null

$Success = $false
try {
    $gitBranch = git branch --show-current 2>$null
    $pythonVersion = python --version
    try {
        $gpu = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
    } catch {
        $gpu = "unavailable"
    }

    $config = [ordered]@{
        run_name = $RunName
        workspace = $Workspace
        git_branch = $gitBranch
        python = $pythonVersion
        gpu = $gpu
        dataset_root = $DatasetRoot
        model_root = $ModelRoot
        skip_registry = [bool]$SkipRegistry
        skip_postprocess = [bool]$SkipPostprocess
        skip_pi05_smoke_train = [bool]$SkipPi05SmokeTrain
        protocol_buffers_python_implementation = $env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION
    }
    $config | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $RunDir "orchestrator_config.json") -Encoding UTF8

    Write-Host "== Grasp pipeline smoke =="
    Write-Host "Workspace: $Workspace"
    Write-Host "Git branch: $gitBranch"
    Write-Host "Python: $pythonVersion"
    Write-Host "GPU: $gpu"
    Write-Host "DatasetRoot: $DatasetRoot"
    Write-Host "ModelRoot: $ModelRoot"
    Write-Host "RunDir: $RunDir"

    if (-not $SkipRegistry) {
        Write-Host "== Step 1: validate dataset registry =="
        python .\scripts\grasp_dataset_registry.py `
          --registry .\data\grasp_dataset_registry.json `
          --summary-output .\artifacts\grasp_pipeline\dataset_registry_summary.md
    }

    if (-not $SkipPostprocess) {
        Write-Host "== Step 2: run postprocess smoke =="
        $argsList = @(
            ".\scripts\grasp_postprocess_pipeline.py",
            "--dataset-root", $DatasetRoot,
            "--model-root", $ModelRoot,
            "--run-root", $RunRoot,
            "--run-name", $RunName
        )
        python @argsList
    }

    if (-not $SkipPi05SmokeTrain) {
        Write-Host "== Step 3: run existing pi0.5 1-step smoke train =="
        .\scripts\run_smoke_train_pi05.ps1 `
          -BatchSize 1 `
          -Steps 1 `
          -DatasetRoot $DatasetRoot `
          -PretrainedPath $ModelRoot
    }

    $Success = $true
    $manifest = [ordered]@{
        status = "success"
        run_name = $RunName
        run_dir = $RunDir
        transcript = $TranscriptPath
        registry_summary = ".\artifacts\grasp_pipeline\dataset_registry_summary.md"
        postprocess_manifest = Join-Path $RunDir "manifest.json"
        pi05_smoke_checkpoint = ".\outputs\pi05_libero_smoke\checkpoints\000001"
        next_recommended_command = ".\scripts\eval_pi05_libero_lerobot.ps1 -PolicyPath .\outputs\pi05_libero_task10_4090_utf8\checkpoints\030000\pretrained_model -Tasks libero_goal -TaskIds '[8]' -Episodes 10"
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $RunDir "orchestrator_manifest.json") -Encoding UTF8
    Write-Host "Smoke pipeline completed."
} catch {
    $failure = [ordered]@{
        status = "failed"
        run_name = $RunName
        run_dir = $RunDir
        failed_command = $MyInvocation.Line
        error = $_.Exception.Message
        suggested_next_step = "Inspect orchestrator.log and any failure.json in this run directory, then rerun the same command after fixing the reported dependency or path."
    }
    $failure | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $RunDir "orchestrator_failure.json") -Encoding UTF8
    throw
} finally {
    Stop-Transcript | Out-Null
}

if (-not $Success) {
    exit 1
}
