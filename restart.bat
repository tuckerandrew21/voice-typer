@echo off
cd /d "%~dp0"
echo Stopping existing processes...
taskkill /f /im python.exe 2>nul
timeout /t 1 /nobreak >nul

echo Starting MurmurTone...
start "" "%~dp0venv\Scripts\pythonw.exe" murmurtone.py
timeout /t 2 /nobreak >nul

echo Opening settings...
start "" "%~dp0venv\Scripts\python.exe" settings_gui.py
