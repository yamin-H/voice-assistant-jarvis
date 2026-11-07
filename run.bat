@echo off
title Jarvis Lite
setlocal enabledelayedexpansion

:: Navigate to the directory containing this script
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  ==============================================================
    echo   [ERROR] Virtual environment not found in .venv!
    echo  ==============================================================
    echo.
    echo   Please run the one-time setup first:
    echo     1. python -m venv .venv
    echo     2. .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starting Jarvis Lite...
echo Log output redirected to data\logs\jarvis.log
echo.

:: Run Jarvis using the virtual environment's python directly
".venv\Scripts\python.exe" -m jarvis.main

:: Keep the window open if an unexpected crash occurred
if %ERRORLEVEL% neq 0 (
    echo.
    echo ==============================================================
    echo  Jarvis terminated unexpectedly (Exit Code: %ERRORLEVEL%).
    echo  Check data\logs\jarvis.log for detailed diagnostics.
    echo ==============================================================
    echo.
    pause
)