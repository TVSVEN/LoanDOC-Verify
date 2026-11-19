@echo off
setlocal
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.10 or newer was not found. Install Python and enable the python command.
    pause
    exit /b 1
)
python app.py
if errorlevel 1 pause
