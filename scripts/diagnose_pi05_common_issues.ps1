param(
    [string]$DatasetRoot = ".\data\lerobot_libero",
    [string]$ModelRoot = ".\models\pi05_libero_base"
)

$ErrorActionPreference = "Continue"

Write-Host "== Processes that may still be downloading =="
Get-Process python,powershell,conda -ErrorAction SilentlyContinue |
  Select-Object Id,ProcessName,CPU,StartTime,Path |
  Sort-Object StartTime

Write-Host "`n== GPU =="
nvidia-smi --query-gpu=name,memory.total,memory.used,driver_version --format=csv,noheader

Write-Host "`n== Dataset/model verification =="
powershell -ExecutionPolicy Bypass -File .\scripts\verify_pi05_task.ps1 `
  -DatasetRoot $DatasetRoot `
  -ModelRoot $ModelRoot

Write-Host "`n== Suggested fixes =="
Write-Host "1. If model.safetensors is incomplete, keep automatic download running or manually download it from Hugging Face."
Write-Host "2. If paths contain Chinese characters, run from R:\ after: cmd /c subst R: <project-path>"
Write-Host "3. If CUDA OOM appears, rerun training with -BatchSize 4 or -BatchSize 2."
