@echo off
REM Build script for MurmurTone
REM Creates both standalone EXE and Windows installer

echo ============================================
echo MurmurTone Build Script v1.0
echo ============================================
echo.

REM Check Python version (requires 3.12 or 3.13)
python -c "import sys; v=sys.version_info[:2]; exit(0 if (3,12)<=v<(3,14) else 1)" 2>nul
if errorlevel 1 (
    echo ERROR: Build requires Python 3.12 or 3.13
    echo.
    echo Current Python version:
    python --version
    echo.
    echo Install Python 3.12 from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo Python version OK
echo.

REM Step 1: Prepare bundled model
echo [Step 1/3] Preparing tiny.en model for bundling...
echo.

if not exist "models\tiny.en" (
    echo Model not found. Running prepare_model.py...
    python prepare_model.py
    if errorlevel 1 (
        echo ERROR: Failed to prepare model
        pause
        exit /b 1
    )
) else (
    echo Model already prepared at models\tiny.en\
)

echo.
echo [Step 2/3] Building EXE with PyInstaller...
echo.

REM Build with PyInstaller
python -m pip install -q pyinstaller >nul 2>&1
pyinstaller murmurtone.spec --noconfirm

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo Build successful: dist\MurmurTone\MurmurTone.exe
echo.

REM Step 3: Build installer (optional - requires Inno Setup)
echo [Step 3/3] Building Windows installer...
echo.

where iscc >nul 2>&1
if errorlevel 1 (
    echo Inno Setup not found. Skipping installer creation.
    echo.
    echo To build installer:
    echo   1. Install Inno Setup from https://jrsoftware.org/isdl.php
    echo   2. Add Inno Setup to PATH
    echo   3. Run: iscc installer.iss
    echo.
    goto :skip_installer
)

echo Building installer with Inno Setup...
iscc installer.iss

if errorlevel 1 (
    echo WARNING: Installer build failed
    goto :skip_installer
)

echo Installer created: installer_output\MurmurTone-1.0.0-Setup.exe
echo.

:skip_installer

echo ============================================
echo Build Complete!
echo ============================================
echo.
echo Output files:
echo   - Standalone: dist\MurmurTone\
echo   - Installer:  installer_output\MurmurTone-1.0.0-Setup.exe
echo.
pause
