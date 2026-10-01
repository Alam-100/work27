# Wait until console health endpoint responds, then open SPA (or legacy).
param(
  [string]$HealthUrl = "http://127.0.0.1:8765/api/health",
  [string]$OpenUrl = "http://127.0.0.1:8765/jobs",
  [int]$TimeoutSec = 45
)

$ErrorActionPreference = "Continue"
$deadline = (Get-Date).AddSeconds($TimeoutSec)

while ((Get-Date) -lt $deadline) {
  try {
    $resp = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 2
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
      Start-Process $OpenUrl
      exit 0
    }
  } catch {
    # not ready yet
  }
  Start-Sleep -Milliseconds 400
}

Write-Host "Health check timed out after ${TimeoutSec}s: $HealthUrl"
# Still open browser so user can retry / see error page
Start-Process $OpenUrl
exit 1
