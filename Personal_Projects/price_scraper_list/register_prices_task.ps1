# Registers the twice-weekly client price check (ADR-014): run_prices.ps1 on Monday and
# Thursday at 07:30, before the store opens and before the hourly probe starts.
# Runs as the current user, only while logged on (a missed run starts at the next logon).
# Usage:  .\register_prices_task.ps1
#         .\register_prices_task.ps1 -Days Monday,Thursday -At 07:30
#         .\register_prices_task.ps1 -Remove
param(
    [ValidateSet("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")]
    [string[]]$Days = @("Monday", "Thursday"),
    [string]$At = "07:30",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$TaskName = "Rappi Client Price Check (twice weekly)"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed '$TaskName'." -ForegroundColor Yellow
    exit 0
}

$Root = $PSScriptRoot
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Root\run_prices.ps1`"" `
    -WorkingDirectory $Root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Days -At $At
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Force `
    -Description "price_scraper_list: run_prices.ps1 (client listings + in-stock competitor search -> client Excel). 0 ok, 1 failed." `
    -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null

Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo | Select-Object TaskName, NextRunTime | Format-List
Write-Host "Runs $($Days -join ', ') at $At. Logs: logs\prices_<date>.log" -ForegroundColor Cyan
Write-Host "Test it now with:  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
