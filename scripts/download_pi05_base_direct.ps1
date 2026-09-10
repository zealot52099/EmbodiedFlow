param(
    [string]$LocalDir = ".\models\pi05_libero_base",
    [int]$Retries = 3
)

$ErrorActionPreference = "Stop"

.\scripts\download_libero_direct.ps1 `
  -RepoId "lerobot/pi05_libero_base" `
  -RepoType "model" `
  -LocalDir $LocalDir `
  -AllowPrefixes ".gitattributes,README.md,config.json,model.safetensors,policy_preprocessor.json,policy_postprocessor.json" `
  -Retries $Retries
