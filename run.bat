@echo off
cd /d "%~dp0"

echo Checking and installing application requirements...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Failed to verify or install requirements. Attempting to start anyway...
)
echo.

echo Starting FitLife Gym Management App...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%.
    pause
)
