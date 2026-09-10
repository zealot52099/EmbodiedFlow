param(
    [string]$Drive = "R:",
    [string]$ProjectRoot = "E:\projects\robot"
)

$ErrorActionPreference = "Stop"

cmd /c "subst $Drive /D" 2>$null | Out-Null
cmd /c "subst $Drive `"$ProjectRoot`""

Write-Host "$Drive -> $ProjectRoot"
