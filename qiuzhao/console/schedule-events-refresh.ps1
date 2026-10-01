# 刷新西电就业网宣讲会 / 双选会 → Obsidian 10_校园活动
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $Root "qiuzhao\scripts\fetch_xidian_events.py"))) {
  $Root = "D:\AgentProjects\work"
}
Set-Location $Root
if (-not $env:QIUZHAO_VAULT) {
  $env:QIUZHAO_VAULT = "C:\Users\xd\Documents\ObsidianRecovery\my-obsidian-20260921\My_docs"
}
$py = "py"
$out = Join-Path $Root "qiuzhao\tmp\xidian_events.json"
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
& $py -3.12 (Join-Path $Root "qiuzhao\scripts\fetch_xidian_events.py") `
  --write-vault --update-source-links --out $out
if ($LASTEXITCODE -ne 0) {
  Write-Error "fetch_xidian_events failed with code $LASTEXITCODE"
  exit $LASTEXITCODE
}
Write-Host "OK: refreshed campus events -> $env:QIUZHAO_VAULT\秋招\10_校园活动"
