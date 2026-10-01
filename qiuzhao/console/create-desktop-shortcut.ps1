# Create/update desktop shortcuts for Qiuzhao console (prod + dev)
$ErrorActionPreference = "Stop"
$prodBat = Join-Path $PSScriptRoot "start-console.bat"
$devBat = Join-Path $PSScriptRoot "start-console-dev.bat"
$targets = New-Object System.Collections.Generic.List[string]

$defaultDesktop = [Environment]::GetFolderPath("Desktop")
if ($defaultDesktop) { [void]$targets.Add($defaultDesktop) }

foreach ($extra in @("D:\Desktop")) {
  if (Test-Path -LiteralPath $extra) { [void]$targets.Add($extra) }
}
# Custom Chinese desktop folder
$cnDesktop = Join-Path "D:\" ([char]0x684C + [char]0x9762)
if (Test-Path -LiteralPath $cnDesktop) { [void]$targets.Add($cnDesktop) }

$uniq = $targets | Select-Object -Unique
if (-not $uniq) { throw "Desktop folder not found" }

$shortcuts = @(
  @{
    Name = "Qiuzhao-Console.lnk"
    Target = $prodBat
    Desc = "Qiuzhao SPA prod http://127.0.0.1:8765/jobs"
  },
  @{
    Name = "Qiuzhao-Console-Dev.lnk"
    Target = $devBat
    Desc = "Qiuzhao DEV hot reload http://127.0.0.1:5173/jobs"
  }
)

foreach ($desktop in $uniq) {
  $w = New-Object -ComObject WScript.Shell
  foreach ($s in $shortcuts) {
    $lnkPath = Join-Path $desktop $s.Name
    $lnk = $w.CreateShortcut($lnkPath)
    $lnk.TargetPath = $s.Target
    $lnk.WorkingDirectory = "d:\AgentProjects\work"
    $lnk.Description = $s.Desc
    $lnk.Save()
    Write-Host ("Updated: " + $lnkPath)
  }
}
