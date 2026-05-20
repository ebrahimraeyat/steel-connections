@echo off
title Steel Connections - Installer
color 0A

echo ============================================================
echo       Steel Connections - One-Click Installer
echo ============================================================
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

:: Name of the conda environment to create
set "ENV_NAME=steel-connections"
:: Python version to use inside conda env
set "PY_VER=3.12"

:: ---------------------------------------------------------------
:: 1. Locate or install Miniconda
:: ---------------------------------------------------------------
echo [1/4] Checking for Conda ...

set "CONDA_EXE="
for %%C in (
    "%USERPROFILE%\miniconda3\Scripts\conda.exe"
    "%USERPROFILE%\Miniconda3\Scripts\conda.exe"
    "%USERPROFILE%\anaconda3\Scripts\conda.exe"
    "%USERPROFILE%\Anaconda3\Scripts\conda.exe"
    "%ProgramData%\Miniconda3\Scripts\conda.exe"
    "%ProgramData%\Anaconda3\Scripts\conda.exe"
) do (
    if exist %%C set "CONDA_EXE=%%~C"
)

if defined CONDA_EXE (
    echo      Conda found: %CONDA_EXE%
    goto :conda_found
)

:: Try PATH
where conda >nul 2>&1
if %errorlevel% equ 0 (
    for /f "usebackq delims=" %%X in (`where conda`) do set "CONDA_EXE=%%X"
    echo      Conda found in PATH: %CONDA_EXE%
    goto :conda_found
)

echo      Conda not found. Downloading Miniconda ...
set "MINI_INSTALLER=%TEMP%\Miniconda3-latest.exe"
powershell -NoProfile -Command "& { [Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile '%MINI_INSTALLER%' }"
if not exist "%MINI_INSTALLER%" (
    echo      ERROR: Failed to download Miniconda.
    echo      Please install Miniconda manually from: https://www.anaconda.com/download
    pause
    exit /b 1
)

echo      Installing Miniconda silently (please wait) ...
start /wait "" "%MINI_INSTALLER%" /S /D=%USERPROFILE%\Miniconda3
del "%MINI_INSTALLER%" 2>nul

call :refresh_path
set "CONDA_EXE=%USERPROFILE%\Miniconda3\Scripts\conda.exe"
if not exist "%CONDA_EXE%" (
    echo      ERROR: Miniconda installation failed.
    echo      Please install Miniconda manually and run install.bat again.
    pause
    exit /b 1
)
echo      Miniconda installed successfully.

:conda_found
echo.

:: Derive CONDA_BASE from CONDA_EXE (go up two levels from Scripts/conda.exe)
for %%F in ("%CONDA_EXE%") do set "CONDA_SCRIPTS=%%~dpF"
for %%D in ("%CONDA_SCRIPTS:~0,-1%") do set "CONDA_BASE=%%~dpD"
set "CONDA_BASE=%CONDA_BASE:~0,-1%"

:: ---------------------------------------------------------------
:: 2. Create conda environment if it doesn't exist
:: ---------------------------------------------------------------
echo [2/4] Setting up conda environment "%ENV_NAME%" ...

call "%CONDA_EXE%" env list 2>nul | findstr /b "%ENV_NAME% " >nul 2>&1
if %errorlevel% equ 0 (
    echo      Environment already exists. Skipping creation.
    goto :env_done
)

echo      Creating environment with Python %PY_VER% ...
call "%CONDA_EXE%" create -y -n "%ENV_NAME%" python=%PY_VER% -c conda-forge
if %errorlevel% neq 0 (
    echo      ERROR: Failed to create conda environment.
    pause
    exit /b 1
)

:env_done
echo.

:: ---------------------------------------------------------------
:: 3. Install pythonocc-core (conda) + pip dependencies
:: ---------------------------------------------------------------
echo [3/4] Installing OCC and project dependencies ...
echo      Step 3a: pythonocc-core from conda-forge ...
call "%CONDA_EXE%" install -y -n "%ENV_NAME%" -c conda-forge pythonocc-core
if %errorlevel% neq 0 (
    echo      ERROR: Failed to install pythonocc-core.
    pause
    exit /b 1
)

:: Resolve path to the env's pip
set "ENV_PYTHON="
for /f "usebackq delims=" %%P in (`"%CONDA_EXE%" run -n "%ENV_NAME%" python -c "import sys; print(sys.executable)"`
) do set "ENV_PYTHON=%%P"

if not defined ENV_PYTHON (
    echo      ERROR: Could not resolve Python path inside conda env.
    pause
    exit /b 1
)

echo      Step 3b: pip dependencies ...
call "%CONDA_EXE%" run -n "%ENV_NAME%" pip install -e . --no-deps
call "%CONDA_EXE%" run -n "%ENV_NAME%" pip install pyside6 numpy pandas ezdxf python-docx
if %errorlevel% neq 0 (
    echo      ERROR: pip install failed.
    pause
    exit /b 1
)
echo.

:: ---------------------------------------------------------------
:: 4. Create launcher and run
:: ---------------------------------------------------------------
echo [4/4] Creating launcher and starting Steel Connections ...

:: Write run_steel_connections.bat pointing at conda env
(
    echo @echo off
    echo set "ROOT=%%~dp0"
    echo cd /d "%%ROOT%%"
    echo set "CONDA_EXE=%CONDA_EXE%"
    echo call "%%CONDA_EXE%%" run -n %ENV_NAME% python "%%ROOT%%src\steel_connections\main_window.py" %%*
) > "%ROOT%run_steel_connections.bat"

echo.
echo ============================================================
echo   Installation complete!
echo   To launch the app later: run_steel_connections.bat
echo ============================================================
echo.

call "%CONDA_EXE%" run -n "%ENV_NAME%" python src\steel_connections\main_window.py
if %errorlevel% neq 0 (
    echo.
    echo   ERROR: Application failed to start. Check messages above.
    pause
    exit /b 1
)

pause
goto :eof

:: ---------------------------------------------------------------
:: Subroutine: Refresh PATH from registry
:: ---------------------------------------------------------------
:refresh_path
for /f "tokens=2,*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%B"
set "PATH=%SYS_PATH%;%USR_PATH%"
goto :eof
