# Registers (or updates) the weekly Windows scheduled task for the scraper.
# Usage:  .\register_task.ps1                         (Wednesday 10:00, default)
#         .\register_task.ps1 -Day Thursday -At 09:30
#         .\register_task.ps1 -Remove                 (unregister)
# Runs as the current user, only while logged on (no stored password, no admin).
param(
    [ValidateSet("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")]
    [string]$Day = "Wednesday",
    [string]$At = "10:00",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$TaskName = "Rappi Price Scraper (weekly)"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed '$TaskName'." -ForegroundColor Yellow
    exit 0
}

$Root = $PSScriptRoot
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Root\run_weekly.ps1`"" `
    -WorkingDirectory $Root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Day -At $At
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew `
    -RestartCount 1 -RestartInterval (New-TimeSpan -Minutes 30)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Force `
    -Description "price_scraper_list: run_weekly.ps1 (scrape -> export -> stats). Last Run Result: 0 ok, 1 failed, 2 degraded." `
    -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null

Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo |
    Select-Object TaskName, NextRunTime, LastRunTime, LastTaskResult | Format-List
Write-Host "Test it now with:  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
