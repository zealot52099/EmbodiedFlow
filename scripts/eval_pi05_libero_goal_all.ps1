param(
    [string]$PolicyPath = ".\outputs\pi05_libero_multitask_4090\checkpoints\030000\pretrained_model",
    [int]$Episodes = 1,
    [string]$OutputDir = ".\eval_logs\pi05_libero_goal_all",
    [string]$SummaryOutput = ".\artifacts\grasp_pipeline\runs\multitask_libero_eval_latest\eval_summary.json"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

.\scripts\eval_pi05_libero_lerobot.ps1 `
  -PolicyPath $PolicyPath `
  -Tasks "libero_goal" `
  -TaskIds "[0,1,2,3,4,5,6,7,8,9]" `
  -Episodes $Episodes `
  -OutputDir $OutputDir

python .\scripts\summarize_lerobot_eval.py `
  --eval-info (Join-Path $OutputDir "eval_info.json") `
  --output $SummaryOutput `
  --command ".\scripts\eval_pi05_libero_goal_all.ps1 -PolicyPath $PolicyPath -Episodes $Episodes -OutputDir $OutputDir" `
  --note "All libero_goal task ids 0-9. Episodes means per task in the LeRobot eval wrapper."
