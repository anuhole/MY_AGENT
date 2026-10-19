@echo off
title AutoTestAI - Launcher
echo ===================================================
echo           AutoTestAI - Starting System
echo ===================================================
echo.

cd /d "%~dp0backend"

echo [1/2] Checking Python dependencies...
pip install -r requirements.txt --quiet

echo.
echo [2/2] Launching Backend Server on http://localhost:8000 ...
start "AutoTestAI Backend" cmd /k "uvicorn app.main:app --reload --port 8000"

timeout /t 2 >nul

echo.
echo Opening Frontend in your default browser...
start "" "%~dp0frontend\index.html"

echo.
echo ===================================================
echo   AutoTestAI is running!
echo   - Backend API Docs: http://localhost:8000/docs
echo   - Frontend UI: Opened in your browser
echo ===================================================
pause
