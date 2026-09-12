@echo off
setlocal

echo Starting backend (FastAPI, port 8000)...
start "TW Stock Dashboard - Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn app.main:app --port 8000"

echo Starting frontend (Vite, port 5173)...
start "TW Stock Dashboard - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Waiting for servers to come up...
timeout /t 5 /nobreak >nul

start "" "http://localhost:5173"

echo.
echo Both servers started in their own windows, and the browser should have opened.
echo To stop: close those two windows, or run stop.bat.
echo.
pause
