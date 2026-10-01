@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
REM Production SPA on :8765 (uvicorn --reload for API; frontend needs npm run build or use Dev shortcut)
cd /d d:\AgentProjects\work
set QIUZHAO_VAULT=C:\Users\xd\Documents\ObsidianRecovery\my-obsidian-20260921\My_docs
set PORT=8765
set OPEN_URL=http://127.0.0.1:8765/jobs

echo.
echo Freeing port %PORT% if occupied...
powershell -NoProfile -ExecutionPolicy Bypass -File "qiuzhao\console\_ensure-port.ps1" -Port %PORT%
if errorlevel 1 (
  echo WARNING: could not fully free port %PORT%
)

if not exist "qiuzhao\web\dist\index.html" (
  echo SPA build missing — running npm install ^& build ...
  pushd qiuzhao\web
  call npm install
  call npm run build
  popd
  if not exist "qiuzhao\web\dist\index.html" (
    echo Build failed — will open /legacy after server starts.
    set OPEN_URL=http://127.0.0.1:8765/legacy
  )
)

echo.
echo SPA     : http://127.0.0.1:8765/jobs
echo Legacy  : http://127.0.0.1:8765/legacy
echo API docs: http://127.0.0.1:8765/api/docs
echo.
echo Note: API auto-reloads on Python changes (--reload).
echo       For SPA hot reload, use Qiuzhao-Console-Dev.lnk or start-console-dev.bat
echo       ^(Vite :5173^). Frontend dist changes still need: npm run build
echo.

REM Open browser only after /api/health is up (runs in background)
start "" /b powershell -NoProfile -ExecutionPolicy Bypass -File "qiuzhao\console\_wait-and-open.ps1" -HealthUrl "http://127.0.0.1:8765/api/health" -OpenUrl "!OPEN_URL!" -TimeoutSec 45

py -3.12 -m uvicorn console.app:app --app-dir qiuzhao --host 127.0.0.1 --port %PORT% --reload
echo.
echo Server exited.
pause
endlocal
