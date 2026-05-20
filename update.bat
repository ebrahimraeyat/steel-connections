@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Steel Connections Updater

echo.
echo =====================================================
echo   Steel Connections - Update Script
echo =====================================================
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

if exist ".git" (
    where git >nul 2>&1
    if not errorlevel 1 (
        echo [1/3] Pulling latest changes from git...
        git pull --ff-only
        if errorlevel 1 (
            echo [WARNING] git pull failed. Continuing with dependency update.
        )
    ) else (
        echo [INFO] Git is not available. Skipping source update.
    )
) else (
    echo [INFO] This installation is not a git clone. Skipping source update.
)

if not exist ".venv\Scripts\python.exe" (
    echo [2/3] Virtual environment not found. Running install.bat...
    call "%ROOT%install.bat"
    exit /b %errorlevel%
)

echo [2/3] Updating pip...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

echo [3/3] Reinstalling dependencies...
call ".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 (
    echo [ERROR] Update failed during dependency installation.
    pause
    exit /b 1
)

echo.
echo Update completed successfully.
echo.
set /p RUNNOW=Run Steel Connections now? ^(Y/N^): 
if /I "%RUNNOW%"=="Y" (
    call "%ROOT%run_steel_connections.bat"
)

pause
exit /b 0
