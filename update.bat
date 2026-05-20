@echo off
setlocal EnableDelayedExpansion
title Steel Connections - Updater
color 0E

echo ============================================================
echo          Steel Connections - Update ^& Run
echo ============================================================
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"
set "ENV_NAME=steel-connections"

:: ---------------------------------------------------------------
:: Locate conda
:: ---------------------------------------------------------------
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
if not defined CONDA_EXE (
    where conda >nul 2>&1
    if %errorlevel% equ 0 for /f "usebackq delims=" %%X in (`where conda`) do set "CONDA_EXE=%%X"
)

if not defined CONDA_EXE (
    echo  Conda not found. Running full installer ...
    call "%ROOT%install.bat"
    exit /b
)

:: ---------------------------------------------------------------
:: Check git and pull
:: ---------------------------------------------------------------
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Git is not installed or not in PATH.
    echo  Please run install.bat first.
    pause
    exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: This folder is not a Git repository.
    pause
    exit /b 1
)

echo [1/2] Pulling latest changes from GitHub ...
git pull
if %errorlevel% neq 0 (
    echo  WARNING: git pull failed. Trying stash + pull ...
    git stash
    git pull
    if !errorlevel! neq 0 (
        echo  ERROR: Could not update. Resolve conflicts manually.
        pause
        exit /b 1
    )
    echo  Stash applied. Run "git stash pop" to restore local changes.
)
echo  Code updated.
echo.

:: ---------------------------------------------------------------
:: Refresh packages and run
:: ---------------------------------------------------------------
echo [2/2] Refreshing dependencies and launching ...
call "%CONDA_EXE%" install -y -n "%ENV_NAME%" -c conda-forge pythonocc-core
call "%CONDA_EXE%" run -n "%ENV_NAME%" pip install -e . --no-deps
call "%CONDA_EXE%" run -n "%ENV_NAME%" pip install pyside6 numpy pandas ezdxf python-docx
echo.
call "%CONDA_EXE%" run -n "%ENV_NAME%" python src\steel_connections\main_window.py
if %errorlevel% neq 0 (
    echo.
    echo  Application exited with an error.
    pause
)
exit /b
