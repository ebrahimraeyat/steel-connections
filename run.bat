@echo off
title Steel Connections (Developer Run)
cd /d "%~dp0"

:: 1. اضافه کردن مسیر سورس به PYTHONPATH تا نیازی به نصب نباشد
set "PYTHONPATH=%~dp0src"

:: 2. پیدا کردن مسیر Conda
set "CONDA_EXE="
for %%C in (
    "%USERPROFILE%\miniconda3\Scripts\conda.exe"
    "%USERPROFILE%\Miniconda3\Scripts\conda.exe"
    "%USERPROFILE%\anaconda3\Scripts\conda.exe"
    "%USERPROFILE%\Anaconda3\Scripts\conda.exe"
    "%ProgramData%\Miniconda3\Scripts\conda.exe"
    "%ProgramData%\Anaconda3\Scripts\conda.exe"
) do (
    if exist "%%~C" set "CONDA_EXE=%%~C"
)
if not defined CONDA_EXE (
    for /f "usebackq delims=" %%X in (`where conda 2^>nul`) do set "CONDA_EXE=%%X"
)

if not defined CONDA_EXE (
    echo [ERROR] Conda not found! Please open Anaconda Prompt to run.
    pause
    exit /b 1
)

:: 3. اجرای برنامه در محیط civiltools
echo Starting Steel Connections via civiltools environment ...
call "%CONDA_EXE%" run -n civiltools --no-capture-output python src\steel_connections\main_window.py

if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error.
    pause
)
