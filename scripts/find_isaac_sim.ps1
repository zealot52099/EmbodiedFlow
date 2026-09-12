param(
    [string]$IsaacRoot = ""
)

$ErrorActionPreference = "Stop"

$candidateRoots = @()
if ($IsaacRoot -ne "") {
    $candidateRoots += $IsaacRoot
}
if ($env:ISAAC_SIM_ROOT) {
    $candidateRoots += $env:ISAAC_SIM_ROOT
}
$candidateRoots += @(
    "E:\envs\isaacsim61",
    "$env:LOCALAPPDATA\ov\pkg",
    "C:\isaacsim",
    "C:\IsaacSim",
    "E:\isaacsim",
    "E:\IsaacSim"
)

$results = @()
foreach ($root in $candidateRoots | Select-Object -Unique) {
    if (-not $root -or -not (Test-Path -LiteralPath $root)) {
        continue
    }
    $rootItem = Get-Item -LiteralPath $root
    $pipLauncher = Join-Path $rootItem.FullName "Scripts\isaacsim.exe"
    $pipPython = Join-Path $rootItem.FullName "python.exe"
    if ($rootItem.PSIsContainer -and (Test-Path -LiteralPath $pipLauncher)) {
        $launchers = @($pipLauncher)
        if (Test-Path -LiteralPath $pipPython) {
            $launchers += $pipPython
        }
        $results += [pscustomobject]@{
            Root = $rootItem.FullName
            InstallType = "pip"
            Launchers = ($launchers -join ";")
        }
        continue
    }

    $dirs = @()
    if ($rootItem.PSIsContainer -and ($rootItem.Name -match "isaac|Isaac")) {
        $dirs += $rootItem
    }
    if ($rootItem.PSIsContainer) {
        $dirs += Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match "isaac|Isaac" }
    }

    foreach ($dir in $dirs | Select-Object -Unique) {
        $launchers = @(
            Join-Path $dir.FullName "isaac-sim.bat",
            Join-Path $dir.FullName "isaac-sim.selector.bat",
            Join-Path $dir.FullName "python.bat",
            Join-Path $dir.FullName "kit\kit.exe"
        )
        $existing = $launchers | Where-Object { Test-Path -LiteralPath $_ }
        if ($existing.Count -gt 0) {
            $results += [pscustomobject]@{
                Root = $dir.FullName
                InstallType = "workstation"
                Launchers = ($existing -join ";")
            }
        }
    }
}

$results | ConvertTo-Json -Depth 4
