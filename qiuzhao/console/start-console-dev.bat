@echo off
setlocal
chcp 65001 >nul
REM Dev launcher: Vite HMR + uvicorn --reload
cd /d d:\AgentProjects\work27
set QIUZHAO_VAULT=E:\obsidian\My_docs

echo.
echo Qiuzhao DEV — hot reload
echo   Open after start: http://127.0.0.1:5173/jobs
echo   API reload:       http://127.0.0.1:8765
echo   Finished UI? Use Qiuzhao-Console.lnk (production :8765)
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "qiuzhao\console\dev.ps1"
echo.
echo Dev session ended.
pause
endlocal
