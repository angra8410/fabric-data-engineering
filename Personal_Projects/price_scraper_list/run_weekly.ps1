# Weekly runner for the Rappi price scraper (safe to launch from Task Scheduler).
param (
    [string]$ConfigPath = "config/settings.yaml"
)

# Task Scheduler starts in C:\Windows\System32: always work from the project folder.
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

$LogDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("run_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$Utf8 = New-Object System.Text.UTF8Encoding($false)

# Start-Transcript in Windows PowerShell 5.1 drops output of native programs
# (python) when the window is hidden, so every line is written to the log here.
function Write-Log([string]$Message, [string]$Color = "Gray") {
    Write-Host $Message -ForegroundColor $Color
    [System.IO.File]::AppendAllText($LogFile, $Message + "`r`n", $Utf8)
}

function Invoke-Python([string[]]$PyArgs) {
    $ErrorActionPreference = "Continue"   # stderr lines must not abort the pipeline
    & $VenvPython @PyArgs 2>&1 | ForEach-Object { Write-Log "$_" }
    return $LASTEXITCODE
}

# Exit codes: 0 = ok, 1 = failed, 2 = data saved but run degraded (many empty
# queries or Rappi markup drift; see "DEGRADED RUN" lines and logs/debug/).
$exitCode = 0
try {
    if (-not (Test-Path $VenvPython)) {
        throw "Virtual environment not found at $VenvPython. Run .\init.ps1 first."
    }

    Write-Log "==========================================" Cyan
    Write-Log "Weekly Rappi price extraction - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" Cyan
    Write-Log "User: $env:USERNAME | Config: $ConfigPath" Cyan
    Write-Log "==========================================" Cyan

    $code = Invoke-Python @("main.py", "--config", $ConfigPath, "run")
    if ($code -eq 2) {
        Write-Log "WARNING: scrape degraded - exporting what was saved, run will report exit 2." Yellow
        $exitCode = 2
    }
    elseif ($code -ne 0) { throw "Scrape failed (exit $code)" }

    $code = Invoke-Python @("main.py", "--config", $ConfigPath, "export")
    if ($code -ne 0) { throw "Export failed (exit $code)" }

    # Client pricing/visibility Excel (no-op when config/settings.local.yaml has no client)
    $code = Invoke-Python @("main.py", "--config", $ConfigPath, "client-report")
    if ($code -ne 0) {
        Write-Log "WARNING: client report failed (exit $code)" Yellow
        if ($exitCode -eq 0) { $exitCode = 2 }
    }

    Invoke-Python @("main.py", "--config", $ConfigPath, "stats") | Out-Null
    if ($exitCode -eq 0) { Write-Log "Weekly run finished successfully!" Green }
    else { Write-Log "Weekly run finished with warnings (exit $exitCode)." Yellow }
}
catch {
    Write-Log "Weekly run FAILED: $_" Red
    $exitCode = 1
}
finally {
    Write-Log "Finished at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') with exit code $exitCode"
    # keep the last 26 logs (~6 months)
    Get-ChildItem $LogDir -Filter "run_*.log" | Sort-Object Name -Descending | Select-Object -Skip 26 | Remove-Item -Force
}
exit $exitCode
