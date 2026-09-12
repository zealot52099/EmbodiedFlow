param(
    [string]$IsaacRoot = "",
    [string]$Scene = ".\artifacts\grasp_pipeline\runs\isaac_preview_20260910\put_bowl_on_plate_preview.usda",
    [string]$RunDir = ".\artifacts\grasp_pipeline\runs\isaac_launch_20260910",
    [switch]$Headless
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$resolvedRunDir = (Resolve-Path -LiteralPath $RunDir).Path
$manifestPath = Join-Path $resolvedRunDir "manifest.json"
$scenePath = (Resolve-Path -LiteralPath $Scene).Path

$findArgs = @()
if ($IsaacRoot -ne "") {
    $findArgs += @("-IsaacRoot", $IsaacRoot)
}
$detectedJson = & .\scripts\find_isaac_sim.ps1 @findArgs
$detected = @()
if ($detectedJson) {
    $parsed = $detectedJson | ConvertFrom-Json
    if ($parsed -is [array]) {
        $detected = $parsed
    } elseif ($null -ne $parsed) {
        $detected = @($parsed)
    }
}

if ($detected.Count -eq 0) {
    $manifest = [ordered]@{
        status = "isaac_sim_not_found"
        timestamp = (Get-Date).ToString("s")
        scene = $scenePath
        run_dir = $resolvedRunDir
        searched_hint = "Set ISAAC_SIM_ROOT or pass -IsaacRoot to an Isaac Sim install directory."
        official_install_note = "Isaac Sim 6.0 Python installation requires Python 3.12; Windows may require long path support."
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Write-Host "Isaac Sim launcher not found."
    Write-Host "Wrote manifest: $manifestPath"
    exit 2
}

$root = $detected[0].Root
$installType = $detected[0].InstallType
$pythonBat = Join-Path $root "python.bat"
$isaacSimBat = Join-Path $root "isaac-sim.bat"
$pipIsaacSim = Join-Path $root "Scripts\isaacsim.exe"
$pipPython = Join-Path $root "python.exe"
$loadScript = (Resolve-Path -LiteralPath ".\scripts\isaac_load_preview.py").Path

if ($installType -eq "pip" -and (Test-Path -LiteralPath $pipPython)) {
    $arguments = @($loadScript, "--scene", $scenePath)
    if ($Headless) {
        $arguments += @("--headless")
    }
    Write-Host "Launching Isaac Sim pip Python: $pipPython"
    Write-Host "Scene: $scenePath"
    Start-Process -FilePath $pipPython -ArgumentList $arguments -WorkingDirectory (Get-Location).Path
    $launchMode = "isaacsim_pip_python"
} elseif (Test-Path -LiteralPath $pythonBat) {
    $arguments = @($loadScript, "--scene", $scenePath)
    if ($Headless) {
        $arguments += "--headless"
    }
    Write-Host "Launching Isaac Python: $pythonBat"
    Write-Host "Scene: $scenePath"
    Start-Process -FilePath $pythonBat -ArgumentList $arguments -WorkingDirectory (Get-Location).Path
    $launchMode = "isaac_python"
} elseif (Test-Path -LiteralPath $isaacSimBat) {
    Write-Host "Launching Isaac Sim: $isaacSimBat"
    Write-Host "Scene: $scenePath"
    Start-Process -FilePath $isaacSimBat -ArgumentList @($scenePath) -WorkingDirectory $root
    $launchMode = "isaac_sim_bat"
} else {
    throw "Detected Isaac root but no supported launcher found: $root"
}

$manifest = [ordered]@{
    status = "launch_requested"
    timestamp = (Get-Date).ToString("s")
    isaac_root = $root
    launch_mode = $launchMode
    scene = $scenePath
    run_dir = $resolvedRunDir
    note = "An Isaac Sim process was started. Inspect the visible Isaac window for the tabletop grasp/place preview."
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host "Wrote manifest: $manifestPath"
