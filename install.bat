@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Steel Connections Installer

echo.
echo =====================================================
echo   Steel Connections - Automated Installer
echo =====================================================
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python Launcher ^(py^) was not found on this system.
    echo.
    echo Please install Python 3.10+ from:
    echo   https://www.python.org/downloads/windows/
    echo and enable "Add python.exe to PATH" during setup.
    echo.
    pause
    exit /b 1
)

echo [1/6] Creating virtual environment...
py -3 -m venv .venv
if errorlevel 1 (
    echo [ERROR] Could not create virtual environment.
    pause
    exit /b 1
)

echo [2/6] Upgrading pip/setuptools/wheel...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip tools.
    pause
    exit /b 1
)

echo [3/6] Installing project dependencies...
call ".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

echo [4/6] Ensuring report dependency ^(python-docx^)...
call ".venv\Scripts\python.exe" -m pip install python-docx
if errorlevel 1 (
    echo [WARNING] Could not install python-docx. Report export may not work.
)

echo [5/6] Creating launcher script...
> "%ROOT%run_steel_connections.bat" (
    echo @echo off
    echo set "ROOT=%%~dp0"
    echo cd /d "%%ROOT%%"
    echo call "%%ROOT%%.venv\Scripts\python.exe" "%%ROOT%%src\steel_connections\main_window.py" %%*
)

echo [6/6] Setup complete.
echo.
echo -----------------------------------------------------
echo Installation finished successfully.
echo.
echo To run the software later:
echo   %ROOT%run_steel_connections.bat
echo -----------------------------------------------------
echo.

set /p RUNNOW=Run Steel Connections now? ^(Y/N^): 
if /I "%RUNNOW%"=="Y" (
    call "%ROOT%run_steel_connections.bat"
)

echo.
echo Installer finished.
pause
exit /b 0
