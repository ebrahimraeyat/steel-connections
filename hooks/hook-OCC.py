# hooks/hook-OCC.py
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

hiddenimports = collect_submodules('OCC')
datas = collect_data_files('OCC')
binaries = collect_dynamic_libs('OCC')