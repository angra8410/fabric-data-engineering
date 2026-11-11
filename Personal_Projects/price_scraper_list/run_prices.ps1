# Twice-weekly price check for the client store (ADR-014). Safe to launch from Task Scheduler.
# Refreshes her own Rappi listings, searches every in-stock product again, and writes the
# client Excel ("Cambiar precio en Rappi"). Logs to logs/prices_<yyyyMMdd_HHmmss>.log.
# Exit 0 ok/skipped, 1 failed.
param (
    [string]$ConfigPath = "config/settings.yaml"
)

Set-Location $PSScriptRoot
. "$PSScriptRoot\scrape_lock.ps1"
$env:PYTHONIOENCODING = "utf-8"
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$LogDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("prices_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$Utf8 = New-Object System.Text.UTF8Encoding($false)

function Write-Log([string]$Message) {
    Write-Host $Message
    [System.IO.File]::AppendAllText($LogFile, $Message + "`r`n", $Utf8)
}

$exitCode = 0
try {
    Write-Log "==== price check $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    if (-not (Enter-ScrapeLock -Minutes 20)) {
        Write-Log "Skipped: another scraping job kept running for 20 minutes."
    }
    else {
        $ErrorActionPreference = "Continue"
        & $VenvPython -u main.py --config $ConfigPath client-report --search stock --catalog 2>&1 |
            ForEach-Object { Write-Log "$_" }
        $exitCode = $LASTEXITCODE
    }
}
catch {
    Write-Log "Price check FAILED: $_"
    $exitCode = 1
}
finally {
    Exit-ScrapeLock
    Write-Log "Finished at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') with exit code $exitCode"
    Get-ChildItem $LogDir -Filter "prices_*.log" | Sort-Object Name -Descending | Select-Object -Skip 30 | Remove-Item -Force
}
exit $exitCode
