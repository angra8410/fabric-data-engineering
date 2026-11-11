# Environment initialization + verification for price_scraper_list
# Usage:  .\init.ps1            (setup + unit tests + stats)
#         .\init.ps1 -Smoke     (also scrape one query in one zone against live Rappi)
param([switch]$Smoke)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

function Invoke-Step([string]$Label, [scriptblock]$Cmd) {
    Write-Host "==> $Label" -ForegroundColor Cyan
    & $Cmd
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $Label (exit $LASTEXITCODE)" -ForegroundColor Red; exit $LASTEXITCODE }
}

if (-not (Test-Path $Py)) {
    Invoke-Step "Create virtual environment .venv" { python -m venv .venv }
}
Invoke-Step "Install dependencies" { & $Py -m pip install --disable-pip-version-check -q -r requirements-dev.txt }
Invoke-Step "Install Playwright Chromium" { & $Py -m playwright install chromium }
Invoke-Step "Unit tests" { & $Py -m pytest -q }
Invoke-Step "Database stats" { & $Py main.py stats }
if ($Smoke) {
    Invoke-Step "Live smoke scrape (poblado / 'hills perro')" { & $Py main.py run --zone poblado --query "hills perro" }
}
Write-Host "Setup and verification complete." -ForegroundColor Green
