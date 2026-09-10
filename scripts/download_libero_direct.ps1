param(
    [string]$RepoId = "lerobot/libero",
    [string]$RepoType = "dataset",
    [string]$Revision = "main",
    [string]$LocalDir = ".\data\lerobot_libero",
    [string]$AllowPrefixes = "README.md,meta/,data/,videos/",
    [int]$Retries = 3
)

$ErrorActionPreference = "Stop"
$env:HF_ENDPOINT = $null

$root = (Resolve-Path -Path (New-Item -ItemType Directory -Force -Path $LocalDir)).Path
$repoPath = if ($RepoType -eq "dataset") {
    if ($RepoId.StartsWith("datasets/")) { $RepoId } else { "datasets/$RepoId" }
} else {
    $RepoId
}

$filesJson = python -c "import os, json; os.environ.pop('HF_TOKEN', None); from huggingface_hub import HfApi; print(json.dumps(HfApi().list_repo_files('$RepoId', repo_type='$RepoType')))"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to list Hugging Face repo files."
}

$files = $filesJson | ConvertFrom-Json
$prefixes = $AllowPrefixes.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$selected = @()
foreach ($file in $files) {
    foreach ($prefix in $prefixes) {
        if ($file -eq $prefix -or $file.StartsWith($prefix)) {
            $selected += $file
            break
        }
    }
}

Write-Host "Selected $($selected.Count) files from $RepoId."

foreach ($file in $selected) {
    $target = Join-Path $root ($file -replace "/", [IO.Path]::DirectorySeparatorChar)
    if (Test-Path -LiteralPath $target) {
        continue
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    $encoded = ($file -split "/" | ForEach-Object { [uri]::EscapeDataString($_) }) -join "/"
    $url = "https://huggingface.co/$repoPath/resolve/$Revision/$encoded"
    for ($attempt = 1; $attempt -le $Retries; $attempt++) {
        try {
            Write-Host "Downloading $file"
            Invoke-WebRequest -Uri $url -OutFile $target -UseBasicParsing -TimeoutSec 120
            break
        } catch {
            if ($attempt -eq $Retries) {
                throw "Failed to download $file from $url"
            }
            Start-Sleep -Seconds (5 * $attempt)
        }
    }
}

Write-Host "Direct download finished: $root"
