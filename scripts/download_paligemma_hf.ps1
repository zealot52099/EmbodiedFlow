param(
    [string]$LocalDir = "E:\projects\robot\models\paligemma-3b-pt-224",
    [switch]$TokenizerOnly
)

$ErrorActionPreference = "Stop"

$env:HF_ENDPOINT = $null
$env:HF_HUB_DISABLE_XET = "1"
$env:HF_HUB_ENABLE_HF_TRANSFER = "0"

if ($env:HF_TOKEN) {
    Write-Warning "HF_TOKEN is set. If it is invalid, remove it before running: Remove-Item Env:HF_TOKEN"
}

$hf = "E:\Project\lerobot_experiment\envs\lerobot312\Scripts\hf.exe"
if (-not (Test-Path -LiteralPath $hf)) {
    $cmd = Get-Command hf -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        throw "hf CLI not found."
    }
    $hf = $cmd.Source
}

New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

if ($TokenizerOnly) {
    & $hf download google/paligemma-3b-pt-224 `
      added_tokens.json `
      config.json `
      preprocessor_config.json `
      special_tokens_map.json `
      tokenizer.json `
      tokenizer.model `
      tokenizer_config.json `
      --repo-type model `
      --local-dir $LocalDir
} else {
    & $hf download google/paligemma-3b-pt-224 `
      --repo-type model `
      --local-dir $LocalDir
}
