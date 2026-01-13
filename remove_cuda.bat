@echo off
echo ========================================
echo CUDA Test: Removing GPU Libraries
echo ========================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Uninstalling CUDA packages...
pip uninstall -y nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cuda-runtime-cu12 nvidia-cuda-nvrtc-cu12

echo.
echo ========================================
echo CUDA packages removed!
echo.
echo Now run restart.bat to test:
echo   - Settings GUI should show "GPU libraries not installed"
echo   - GPU install button should be available
echo   - Clicking Install should download and restore GPU support
echo ========================================
pause
