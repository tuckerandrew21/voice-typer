@echo off
echo ========================================
echo CUDA Test: Restoring GPU Libraries
echo ========================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing CUDA packages...
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

echo.
echo ========================================
echo CUDA packages restored!
echo ========================================
pause
