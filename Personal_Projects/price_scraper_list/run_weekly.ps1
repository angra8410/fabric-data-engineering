# Weekly runner for the Rappi price scraper (safe to launch from Task Scheduler).
param (
    [string]$ConfigPath = "config/settings.yaml"
)

# Task Scheduler starts in C:\Windows\System32: always work from the project folder.
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

$LogDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("run_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
Start-Transcript -Path $LogFile | Out-Null

# Exit codes: 0 = ok, 1 = failed, 2 = data saved but run degraded (many empty
# queries or Rappi markup drift; see "DEGRADED RUN" lines and logs/debug/).
$exitCode = 0
try {
    if (-not (Test-Path $VenvPython)) {
        throw "Virtual environment not found at $VenvPython. Run .\init.ps1 first."
    }

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Weekly Rappi price extraction - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan

    & $VenvPython main.py --config $ConfigPath run
    if ($LASTEXITCODE -eq 2) {
        Write-Host "WARNING: scrape degraded - exporting what was saved, run will report exit 2." -ForegroundColor Yellow
        $exitCode = 2
    }
    elseif ($LASTEXITCODE -ne 0) { throw "Scrape failed (exit $LASTEXITCODE)" }

    & $VenvPython main.py --config $ConfigPath export
    if ($LASTEXITCODE -ne 0) { throw "Export failed (exit $LASTEXITCODE)" }

    & $VenvPython main.py --config $ConfigPath stats
    if ($exitCode -eq 0) { Write-Host "Weekly run finished successfully!" -ForegroundColor Green }
    else { Write-Host "Weekly run finished with warnings (exit $exitCode)." -ForegroundColor Yellow }
}
catch {
    Write-Host "Weekly run FAILED: $_" -ForegroundColor Red
    $exitCode = 1
}
finally {
    Stop-Transcript | Out-Null
    # keep the last 26 logs (~6 months)
    Get-ChildItem $LogDir -Filter "run_*.log" | Sort-Object Name -Descending | Select-Object -Skip 26 | Remove-Item -Force
}
exit $exitCode
