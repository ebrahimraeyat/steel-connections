# launch.ps1 — run the app with the project venv + conda OCC DLL paths
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$condaEnv   = "C:\Users\ebrahim\miniconda3\envs\osdag-2025"

# Prepend conda env paths so OCC .pyd files find their DLL dependencies
$env:PATH = "$condaEnv;$condaEnv\Library\bin;$condaEnv\Library\mingw-w64\bin;" + $env:PATH

& "$scriptDir\.venv\Scripts\python.exe" "$scriptDir\src\steel_connections\main_window.py" @args
