param(
    [string]$TaskName = "ExamCurrentAffairsBot",
    [string]$At = "08:00"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$runScript = Join-Path $projectRoot "scripts\run_bot.ps1"

if (-not (Test-Path $runScript)) {
    throw "Run script not found: $runScript"
}

$triggerTime = [DateTime]::ParseExact($At, "HH:mm", $null)
$actionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$runScript`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $triggerTime
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Posts exam current affairs digest to Telegram channel." `
    -Force | Out-Null

Write-Host "Scheduled task '$TaskName' installed. It will run daily at $At."
