@echo off
setlocal enabledelayedexpansion

echo Stopping backend (port 8000)...
set FOUND_BACKEND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    set FOUND_BACKEND=1
)
if !FOUND_BACKEND!==1 (
    echo Backend stopped.
) else (
    echo Backend was not running.
)

echo Stopping frontend (port 5173)...
set FOUND_FRONTEND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    set FOUND_FRONTEND=1
)
if !FOUND_FRONTEND!==1 (
    echo Frontend stopped.
) else (
    echo Frontend was not running.
)

echo.
echo Done.
pause
