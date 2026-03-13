@echo off
setlocal EnableDelayedExpansion

echo ===================================================
echo   4IFIR-checker Installation Script (Windows)
echo ===================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Create virtual environment
echo [1/4] Creating virtual environment (venv)...
if exist venv (
    echo Virtual environment already exists.
) else (
    python -m venv venv
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Install dependencies
echo [2/4] Installing dependencies from requirements.txt...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 4. Verify setup
echo [3/4] Verifying installation...
python verify_setup.py
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Verification failed. Please check the logs above.
    pause
    exit /b 1
)

:: 5. Start the "server" (checker.py)
echo [4/4] Starting the application (checker.py)...
echo.
python checker.py
set RUN_STATUS=!ERRORLEVEL!

:: 6. Show final status
echo.
echo ===================================================
if %RUN_STATUS% equ 0 (
    echo [OK] Installation and initial run successful!
    echo Everything is working correctly.
) else (
    echo [WARNING] Application finished with exit code %RUN_STATUS%.
    echo This might be due to missing environment variables or network issues.
    echo Please check the output above.
)
echo ===================================================
echo.

:: Create a quick launch script
echo @echo off > run.bat
echo call venv\Scripts\activate >> run.bat
echo python checker.py %%* >> run.bat
echo pause >> run.bat

echo Created 'run.bat' for future launches.
echo.
pause
