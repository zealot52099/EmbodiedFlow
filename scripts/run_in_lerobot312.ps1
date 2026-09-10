param(
    [Parameter(Mandatory = $true)]
    [string]$Command
)

$ErrorActionPreference = "Stop"

$envPath = "E:\Project\lerobot_experiment\envs\lerobot312"
if (-not (Test-Path -LiteralPath $envPath)) {
    throw "Expected LeRobot environment not found: $envPath"
}

conda run -p $envPath powershell -NoProfile -ExecutionPolicy Bypass -Command $Command
