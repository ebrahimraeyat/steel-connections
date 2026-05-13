@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: build.bat  —  Full build pipeline for Steel Connection Designer
::
:: Requirements (run ONCE to set up, see README section below):
::   conda activate osdag-2025
::   pip install PySide6 numpy pandas python-docx pyinstaller
::   pip install -e .
::
:: Then just run this script from the repo root (inside activated env):
::   build.bat
:: ─────────────────────────────────────────────────────────────────────────────

setlocal enabledelayedexpansion

echo.
echo =====================================================
echo   Steel Connection Designer — Build Script
echo =====================================================
echo.

:: ── Step 1: PyInstaller ──────────────────────────────────────────────────────
echo [1/2] Running PyInstaller...
pyinstaller steel_connections.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed. See output above.
    exit /b 1
)

echo [1/2] PyInstaller done.  Output: dist\SteelConnections\
echo.

:: ── Step 2: Inno Setup ───────────────────────────────────────────────────────
echo [2/2] Compiling Inno Setup installer...

:: Try common install locations for ISCC
set ISCC=
for %%p in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) do (
    if exist %%p (
        set "ISCC=%%~p"
        goto :found_iscc
    )
)

echo [WARNING] Inno Setup 6 not found in standard locations.
echo           Install from: https://jrsoftware.org/isdl.php
echo           Then run manually:  ISCC.exe installer\setup.iss
echo.
echo [DONE] Portable folder is ready at: dist\SteelConnections\
goto :eof

:found_iscc
"%ISCC%" installer\setup.iss
if errorlevel 1 (
    echo [ERROR] Inno Setup compilation failed.
    exit /b 1
)

echo.
echo =====================================================
echo   BUILD COMPLETE
echo   Installer:  dist\SteelConnectionDesigner-0.1.0-Setup.exe
echo   Portable:   dist\SteelConnections\
echo =====================================================
echo.
