# Shared lock so only one scheduled job drives a browser on Rappi at a time
# (weekly run, twice-weekly price check, hourly probe). Dot-source it:  . "$PSScriptRoot\scrape_lock.ps1"
$ScrapeLock = Join-Path $PSScriptRoot "data\.scrape.lock"

function Test-ScrapeBusy {
    if (-not (Test-Path $ScrapeLock)) { return $false }
    $owner = 0
    [int]::TryParse((Get-Content $ScrapeLock -ErrorAction SilentlyContinue | Select-Object -First 1), [ref]$owner) | Out-Null
    if ($owner -eq $PID) { return $false }
    return [bool](Get-Process -Id $owner -ErrorAction SilentlyContinue)   # stale lock if its process is gone
}

# Waits up to $Minutes for other jobs; returns $true when the lock was taken.
function Enter-ScrapeLock([int]$Minutes = 0) {
    $deadline = (Get-Date).AddMinutes($Minutes)
    while (Test-ScrapeBusy) {
        if ((Get-Date) -ge $deadline) { return $false }
        Start-Sleep -Seconds 30
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $ScrapeLock) | Out-Null
    Set-Content -Path $ScrapeLock -Value $PID
    return $true
}

function Exit-ScrapeLock {
    if ((Test-Path $ScrapeLock) -and ((Get-Content $ScrapeLock -ErrorAction SilentlyContinue | Select-Object -First 1) -eq "$PID")) {
        Remove-Item $ScrapeLock -Force -ErrorAction SilentlyContinue
    }
}
