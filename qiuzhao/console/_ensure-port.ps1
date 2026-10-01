# Free TCP port if occupied (used by start-console.bat).
param(
  [Parameter(Mandatory = $true)]
  [int]$Port
)

$ErrorActionPreference = "Continue"
$pids = @()

try {
  $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if ($conns) {
    $pids = @($conns | Select-Object -ExpandProperty OwningProcess -Unique)
  }
} catch {
  # Fallback when Get-NetTCPConnection is unavailable
}

if (-not $pids) {
  $lines = netstat -ano | Select-String -Pattern ":$Port\s+.*LISTENING"
  foreach ($line in $lines) {
    $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
    if ($parts.Count -ge 5) {
      $pidText = $parts[-1]
      if ($pidText -match '^\d+$') { $pids += [int]$pidText }
    }
  }
  $pids = $pids | Select-Object -Unique
}

foreach ($procId in $pids) {
  if ($procId -le 0) { continue }
  Write-Host "Port $Port in use by PID $procId — stopping..."
  Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}

# Brief wait so the OS releases the socket
$deadline = (Get-Date).AddSeconds(5)
while ((Get-Date) -lt $deadline) {
  $still = $false
  try {
    $still = [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
  } catch {
    $still = [bool](netstat -ano | Select-String -Pattern ":$Port\s+.*LISTENING")
  }
  if (-not $still) { break }
  Start-Sleep -Milliseconds 200
}

Write-Host "Port $Port is free."
