@echo off
:: Launch MurmurTone Settings GUI with Python 3.12
start "" "C:\Users\tucke\AppData\Local\Programs\Python\Python312\pythonw.exe" "%~dp0settings_gui.py"
ping -n 2 127.0.0.1 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0show_window.ps1"
