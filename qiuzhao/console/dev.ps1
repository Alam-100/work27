# Dev mode: uvicorn --reload (API :8765) + Vite HMR (:5173)
$ErrorActionPreference = "Stop"
$ConsoleDir = $PSScriptRoot
$Root = Split-Path -Parent $ConsoleDir
$Web = Join-Path $Root "web"
$EnsurePort = Join-Path $ConsoleDir "_ensure-port.ps1"
$WaitOpen = Join-Path $ConsoleDir "_wait-and-open.ps1"

if (-not $env:QIUZHAO_VAULT) {
  $env:QIUZHAO_VAULT = "C:\Users\xd\Documents\ObsidianRecovery\my-obsidian-20260921\My_docs"
}

Write-Host ""
Write-Host "Qiuzhao DEV mode (hot reload)"
Write-Host "  API  : http://127.0.0.1:8765  (uvicorn --reload)"
Write-Host "  SPA  : http://127.0.0.1:5173  (Vite HMR — use this URL for UI edits)"
Write-Host "  Tip  : Production shortcut serves dist and needs npm run build for frontend."
Write-Host "QIUZHAO_VAULT=$env:QIUZHAO_VAULT"
Write-Host ""

Write-Host "Freeing ports 8765 / 5173 ..."
& $EnsurePort -Port 8765
& $EnsurePort -Port 5173

# API in a separate window so this window can host Vite
$apiCmd = @"
`$ErrorActionPreference = 'Stop'
`$env:QIUZHAO_VAULT = '$($env:QIUZHAO_VAULT)'
Set-Location '$Root'
Write-Host 'API with --reload on http://127.0.0.1:8765'
py -3.12 -m uvicorn console.app:app --app-dir qiuzhao --host 127.0.0.1 --port 8765 --reload
"@
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $apiCmd)

# Open browser after API is up (Vite may still be starting; /api is proxied)
Start-Process powershell -WindowStyle Hidden -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy", "Bypass",
  "-File", $WaitOpen,
  "-HealthUrl", "http://127.0.0.1:8765/api/health",
  "-OpenUrl", "http://127.0.0.1:5173/jobs",
  "-TimeoutSec", "60"
)

Set-Location $Web
if (-not (Test-Path "node_modules")) {
  Write-Host "npm install ..."
  npm install
}
Write-Host "Starting Vite ..."
npm run dev
