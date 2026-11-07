# Jarvis Lite Windows Launcher
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Host.UI.RawUI.WindowTitle = "Jarvis Lite"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "`n==============================================================" -ForegroundColor Red
    Write-Host " [ERROR] Virtual environment not found in .venv!" -ForegroundColor Red
    Write-Host "==============================================================" -ForegroundColor Red
    Write-Host "`nPlease complete setup first:"
    Write-Host "  1. python -m venv .venv"
    Write-Host "  2. .venv\Scripts\pip install -r requirements.txt`n"
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host "Starting Jarvis Lite..." -ForegroundColor Cyan
Write-Host "Logs: data/logs/jarvis.log`n" -ForegroundColor DarkGray

& $PythonExe -m jarvis.main

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[ERROR] Jarvis exited with code $LASTEXITCODE. See data/logs/jarvis.log" -ForegroundColor Yellow
    Read-Host "Press Enter to exit..."
}