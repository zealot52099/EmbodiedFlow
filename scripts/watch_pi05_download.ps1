param(
    [string]$ModelPath = ".\models\pi05_libero_base\model.safetensors",
    [int64]$ExpectedBytes = 14467165872,
    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Stop"

while ($true) {
    if (-not (Test-Path -LiteralPath $ModelPath)) {
        Write-Host "$(Get-Date -Format s) missing: $ModelPath"
    } else {
        $item = Get-Item -LiteralPath $ModelPath
        $pct = [math]::Round(($item.Length / $ExpectedBytes) * 100, 2)
        Write-Host "$(Get-Date -Format s) $($item.Length) / $ExpectedBytes bytes ($pct%)"
        if ($item.Length -ge $ExpectedBytes) {
            Write-Host "Download size target reached."
            break
        }
    }
    Start-Sleep -Seconds $IntervalSeconds
}
