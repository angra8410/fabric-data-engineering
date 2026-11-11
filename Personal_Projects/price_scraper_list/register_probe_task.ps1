# Registers the hourly visibility probe (ADR-013): every day, every hour from 09:15 to
# 20:15 (one check before opening and one after closing as controls), for -Days days,
# then the task stops firing on its own. Runs as the current user, only while logged on.
# Usage:  .\register_probe_task.ps1              (14 days from today)
#         .\register_probe_task.ps1 -Days 7
#         .\register_probe_task.ps1 -Remove      (unregister)
param(
    [int]$Days = 14,
    [string]$From = "09:15",
    [int]$Runs = 12,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$TaskName = "Rappi Visibility Probe (hourly)"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed '$TaskName'." -ForegroundColor Yellow
    exit 0
}

$Root = $PSScriptRoot
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Root\run_probe.ps1`"" `
    -WorkingDirectory $Root
$start = [datetime]::ParseExact($From, "HH:mm", $null)
$trigger = New-ScheduledTaskTrigger -Daily -At $start
# repeat hourly: 09:15, 10:15 ... 20:15 (duration a few minutes past the last run)
$repeat = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Hours ($Runs - 1) -Minutes 5)
$trigger.Repetition = $repeat.Repetition
$trigger.EndBoundary = (Get-Date).Date.AddDays($Days).ToString("s")
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
    -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Force `
    -Description "price_scraper_list: run_probe.ps1 (hourly client visibility check, separate DB). Ends $($trigger.EndBoundary)." `
    -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null

Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo | Select-Object TaskName, NextRunTime | Format-List
Write-Host "Runs hourly $From + $($Runs - 1)h until $($trigger.EndBoundary). Logs: logs\probe_<date>.log" -ForegroundColor Cyan
Write-Host "Test it now with:  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
