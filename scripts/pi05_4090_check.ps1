$ErrorActionPreference = "Stop"

Write-Host "== Pi 0.5 / RTX 4090 readiness check =="

function Test-Command($Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    return $null -ne $cmd
}

if (Test-Command "nvidia-smi") {
    Write-Host "`n[nvidia-smi]"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
} else {
    Write-Warning "nvidia-smi not found. Install NVIDIA driver/CUDA first."
}

Write-Host "`n[python]"
if (Test-Command "python") {
    python --version
    python -c "import sys; print('python_version_ok_for_openpi: ' + ('yes' if sys.version_info >= (3, 11) else 'no, prefer Python 3.11'))"
} else {
    Write-Warning "python not found."
}

Write-Host "`n[pip packages]"
if (Test-Command "python") {
    python -c "import importlib.util; names=['torch','lerobot','huggingface_hub']; [print(name + ': ' + ('ok' if importlib.util.find_spec(name) else 'missing')) for name in names]"
}

Write-Host "`n[recommendation]"
Write-Host "4090 is suitable for Pi 0.5 LoRA/expert-only finetuning, not full finetuning."
Write-Host "Start with scripts/train_pi05_libero_4090.ps1 after accepting the gated Paligemma license and running hf auth login."
