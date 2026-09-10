param(
    [string]$DisplayName = "pi05_libero_base_model",
    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Stop"

while ($true) {
    $job = Get-BitsTransfer -AllUsers | Where-Object { $_.DisplayName -eq $DisplayName } | Select-Object -First 1
    if ($null -eq $job) {
        Write-Host "$(Get-Date -Format s) BITS job not found: $DisplayName"
        break
    }

    $pct = 0
    if ($job.BytesTotal -gt 0) {
        $pct = [math]::Round(($job.BytesTransferred / $job.BytesTotal) * 100, 2)
    }
    Write-Host "$(Get-Date -Format s) $($job.JobState) $($job.BytesTransferred) / $($job.BytesTotal) bytes ($pct%)"

    if ($job.JobState -eq "Transferred") {
        Complete-BitsTransfer -BitsJob $job
        Write-Host "BITS transfer completed."
        break
    }

    if ($job.JobState -in @("Error", "TransientError")) {
        Write-Host $job.ErrorDescription
        break
    }

    Start-Sleep -Seconds $IntervalSeconds
}
