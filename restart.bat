@echo off
cd /d "%~dp0"
taskkill /f /im python.exe 2>nul
timeout /t 1 /nobreak >nul
start "" ".\venv\Scripts\python.exe" murmurtone.py --settings
