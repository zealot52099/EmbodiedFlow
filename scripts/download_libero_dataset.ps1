param(
    [string]$RepoId = "lerobot/libero",
    [string]$RepoType = "dataset",
    [string]$LocalDir = ".\data\lerobot_libero",
    [int]$MaxWorkers = 1,
    [int]$Retries = 5
)

$ErrorActionPreference = "Stop"
$env:HF_ENDPOINT = $null

Write-Host "Downloading $RepoId from Hugging Face."
Write-Host "If access fails, run 'hf auth login' first."

$resolved = (Resolve-Path -Path (New-Item -ItemType Directory -Force -Path $LocalDir)).Path

for ($attempt = 1; $attempt -le $Retries; $attempt++) {
    Write-Host "Download attempt $attempt / $Retries"
    $env:HF_HUB_DISABLE_XET = "1"
    $env:HF_HUB_ENABLE_HF_TRANSFER = "0"
    python -c "import os; from huggingface_hub import snapshot_download; os.environ.pop('HF_TOKEN', None); print(snapshot_download(repo_id='$RepoId', repo_type='$RepoType', local_dir=r'$resolved', max_workers=$MaxWorkers, etag_timeout=60))"
    if ($LASTEXITCODE -eq 0) {
        break
    }
    if ($attempt -eq $Retries) {
        throw "Download failed after $Retries attempts. Check Hugging Face network/proxy access."
    }
    Start-Sleep -Seconds (10 * $attempt)
}

Write-Host "Download finished. Typical cache location is under:"
Write-Host "$resolved"
