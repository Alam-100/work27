$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $env:QIUZHAO_VAULT) {
  $env:QIUZHAO_VAULT = "C:\Users\xd\Documents\ObsidianRecovery\my-obsidian-20260921\My_docs"
}
Write-Host "QIUZHAO_VAULT=$env:QIUZHAO_VAULT"
Write-Host "API + SPA (if built): http://127.0.0.1:8765"
Write-Host "Legacy console:       http://127.0.0.1:8765/legacy"
Write-Host "Dev SPA (optional):   cd qiuzhao\web; npm run dev  -> http://127.0.0.1:5173"
Set-Location $Root
py -3.12 -m uvicorn console.app:app --app-dir qiuzhao --host 127.0.0.1 --port 8765 --reload
