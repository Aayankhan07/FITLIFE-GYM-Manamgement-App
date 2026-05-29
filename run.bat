@echo off
:: FitLife Gym Management System Startup Launcher
title FitLife - Gym Management System
color 0A

echo ===================================================
echo   FITLIFE - MALE FITNESS CHAIN MANAGEMENT SYSTEM  
echo ===================================================
echo.

:: 1. Detect Python Installation
echo Detecting Python installation...
set PYTHON_CMD=python

:: Check if global python command works
python --version >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON_CMD=
    
    :: Check if the "py" launcher works
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
    ) else (
        :: Search in local AppData (standard user installation)
        for /d %%d in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do (
            if exist "%%d\python.exe" set PYTHON_CMD="%%d\python.exe"
        )
        :: Search in Program Files (all users installation)
        if not defined PYTHON_CMD (
            for /d %%d in ("C:\Program Files\Python*") do (
                if exist "%%d\python.exe" set PYTHON_CMD="%%d\python.exe"
            )
        )
        :: Search in C:\Python
        if not defined PYTHON_CMD (
            for /d %%d in ("C:\Python*") do (
                if exist "%%d\python.exe" set PYTHON_CMD="%%d\python.exe"
            )
        )
    )
)

:: If Python is still not found
if not defined PYTHON_CMD (
    color 0C
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo.
    echo Please install Python (make sure to check "Add Python to PATH" during installation)
    echo or configure your environment variables.
    echo.
    pause
    exit /b
)

:: Log the detected Python executable
if "%PYTHON_CMD%"=="python" (
    echo [OK] Python detected in system PATH.
) else (
    echo [OK] Python detected at: %PYTHON_CMD%
)
echo.

:: 2. Create a dynamic checker script to verify requirements
echo Checking required Python packages...

echo import sys, importlib.metadata, re > temp_check_reqs.py
echo missing = [] >> temp_check_reqs.py
echo for line in open('requirements.txt'): >> temp_check_reqs.py
echo     line = line.strip() >> temp_check_reqs.py
echo     if not line or line.startswith('#'): continue >> temp_check_reqs.py
echo     name = re.split('[^a-zA-Z0-9_-]', line)[0].strip() >> temp_check_reqs.py
echo     found = False >> temp_check_reqs.py
echo     for x in (name, name.replace('_', '-').lower(), name.replace('-', '_').lower()): >> temp_check_reqs.py
echo         try: >> temp_check_reqs.py
echo             importlib.metadata.version(x) >> temp_check_reqs.py
echo             found = True; break >> temp_check_reqs.py
echo         except Exception: pass >> temp_check_reqs.py
echo     if not found: missing.append(name) >> temp_check_reqs.py
echo if missing: >> temp_check_reqs.py
echo     print('Missing packages: ' + ', '.join(missing)) >> temp_check_reqs.py
echo     sys.exit(1) >> temp_check_reqs.py
echo sys.exit(0) >> temp_check_reqs.py

%PYTHON_CMD% temp_check_reqs.py
set REQS_STATUS=%errorlevel%
del temp_check_reqs.py

:: 3. Handle Missing Requirements
if %REQS_STATUS% neq 0 (
    color 0E
    echo.
    echo [WARNING] Some required Python packages are missing!
    echo.
    set /p choice="Would you like to install the missing requirements now? (Y/N): "
    if /i "%choice%"=="Y" (
        echo.
        echo Installing requirements...
        %PYTHON_CMD% -m pip install -r requirements.txt
        if %errorlevel% neq 0 (
            color 0C
            echo.
            echo [ERROR] Failed to install requirements. Please run 'pip install -r requirements.txt' manually.
            echo.
            pause
            exit /b
        )
    ) else (
        echo.
        echo [WARNING] Continuing without installing requirements. The app may crash if dependencies are missing.
        echo.
    )
) else (
    echo [OK] All dependencies are successfully installed!
)
echo.

:: 4. Check for settings.json configuration
if not exist "config\settings.json" (
    color 0E
    echo [WARNING] config\settings.json not found!
    echo Creating it from config\settings_template.json...
    copy config\settings_template.json config\settings.json >nul
    echo.
    echo [IMPORTANT] A template settings file has been copied to:
    echo             config\settings.json
    echo Please edit it with your MS SQL Server credentials before continuing.
    echo.
    pause
)

:: 5. Start the Application
color 0A
echo Starting application...
echo.
%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERROR] The application crashed or exited with an error code (%errorlevel%).
    echo.
    pause
)
