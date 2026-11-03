@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo Please follow README.md to create .venv and install dependencies first.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "%~dp0main.py"
