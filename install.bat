@echo off
title Steel Connections - Installer
color 0A

echo ============================================================
echo       Steel Connections - One-Click Installer
echo ============================================================
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

:: ---------------------------------------------------------------
:: 1. Check / install Git
:: ---------------------------------------------------------------
echo [1/3] Checking Git ...
where git >nul 2>&1
if %errorlevel% equ 0 goto :git_ok

echo      Git not found. Downloading Git installer ...
echo      (This may take a minute)
echo.
set "GIT_INSTALLER=%TEMP%\git-installer.exe"
powershell -NoProfile -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/latest/download/Git-2.47.1-64-bit.exe' -OutFile $env:TEMP'\git-installer.exe' }"
if not exist "%GIT_INSTALLER%" (
    echo      ERROR: Failed to download Git installer.
    echo      Please install Git manually from https://git-scm.com/downloads
    pause
    exit /b 1
)
start /wait "" "%GIT_INSTALLER%" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"
del "%GIT_INSTALLER%" 2>nul

call :refresh_path
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo      Git installation may require reopening this terminal.
    echo      Please close this window and double-click install.bat again.
    pause
    exit /b 1
)
echo      Git installed successfully.
goto :git_done

:git_ok
echo      Git found.

:git_done
echo.

:: ---------------------------------------------------------------
:: 2. Check / install uv
:: ---------------------------------------------------------------
echo [2/3] Checking uv ...
where uv >nul 2>&1
if %errorlevel% equ 0 goto :uv_ok

echo      uv not found. Installing uv ...
powershell -NoProfile -ExecutionPolicy ByPass -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; irm https://astral.sh/uv/install.ps1 | iex }"

call :refresh_path
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo      uv installation may require reopening this terminal.
    echo      Please close this window and double-click install.bat again.
    pause
    exit /b 1
)
echo      uv installed successfully.
goto :uv_done

:uv_ok
echo      uv found.

:uv_done
echo.

:: ---------------------------------------------------------------
:: 3. Install dependencies and run
:: ---------------------------------------------------------------
echo [3/3] Installing dependencies and launching Steel Connections ...
echo      (This may take a few minutes on first run)
echo.
uv run --no-dev python src/steel_connections/main_window.py
if %errorlevel% neq 0 (
    echo.
    echo      ERROR: Application failed to start.
    echo      Check the error messages above.
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
