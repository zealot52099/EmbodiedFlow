param(
    [string]$LocalDir = ".\models\paligemma-3b-pt-224-tokenizer",
    [string]$Pi05Preprocessor = ".\models\pi05_libero_base\policy_preprocessor.json"
)

$ErrorActionPreference = "Stop"

.\scripts\download_libero_direct.ps1 `
  -RepoId "google/paligemma-3b-pt-224" `
  -RepoType "model" `
  -LocalDir $LocalDir `
  -AllowPrefixes "added_tokens.json,config.json,preprocessor_config.json,special_tokens_map.json,tokenizer.json,tokenizer.model,tokenizer_config.json" `
  -Retries 3

$resolvedTokenizer = (Resolve-Path -LiteralPath $LocalDir).Path
$json = Get-Content -LiteralPath $Pi05Preprocessor -Raw | ConvertFrom-Json
foreach ($step in $json.steps) {
    if ($step.registry_name -eq "tokenizer_processor") {
        $step.config.tokenizer_name = $resolvedTokenizer
    }
}
$json | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Pi05Preprocessor -Encoding UTF8

Write-Host "Updated tokenizer_name in $Pi05Preprocessor"
Write-Host "tokenizer_name=$resolvedTokenizer"
