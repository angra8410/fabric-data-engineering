# Hourly visibility probe of the client store (ADR-013). Safe to launch from Task Scheduler.
# Logs to logs/probe_<yyyyMMdd>.log (one file per day). Exit 0 ok/skipped, 1 failed.
param (
    [string]$ConfigPath = "config/settings.yaml"
)

Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$LogDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("probe_{0}.log" -f (Get-Date -Format "yyyyMMdd"))
$Utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-Log([string]$Message) {
    Write-Host $Message
    [System.IO.File]::AppendAllText($LogFile, $Message + "`r`n", $Utf8)
}

$exitCode = 0
try {
    Write-Log "---- probe $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    # Never scrape in parallel with the weekly run (one browser at a time on Rappi).
    $weekly = Get-ScheduledTask -TaskName "Rappi Price Scraper (weekly)" -ErrorAction SilentlyContinue
    if ($weekly -and $weekly.State -eq "Running") {
        Write-Log "Skipped: the weekly run is in progress."
    }
    else {
        $ErrorActionPreference = "Continue"
        & $VenvPython main.py --config $ConfigPath probe 2>&1 | ForEach-Object { Write-Log "$_" }
        $exitCode = $LASTEXITCODE
    }
}
catch {
    Write-Log "Probe FAILED: $_"
    $exitCode = 1
}
finally {
    Write-Log "exit $exitCode"
    Get-ChildItem $LogDir -Filter "probe_*.log" | Sort-Object Name -Descending | Select-Object -Skip 30 | Remove-Item -Force
}
exit $exitCode
