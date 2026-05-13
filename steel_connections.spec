# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for Steel Connection Designer
# Build from the osdag-2025 conda environment (contains pythonocc-core).
#
# Usage (from repo root, inside activated osdag-2025 env):
#   pyinstaller steel_connections.spec --noconfirm
# ---------------------------------------------------------

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

SRC = Path('src')

# ── Collect OCC (pythonocc-core) ──────────────────────────────────────────────
occ_datas, occ_binaries, occ_hiddenimports = collect_all('OCC')

# ── Collect PySide6 ───────────────────────────────────────────────────────────
pyside_datas, pyside_binaries, pyside_hiddenimports = collect_all('PySide6')

# ── Application data files ────────────────────────────────────────────────────
app_datas = [
    # CSV data tables
    (str(SRC / 'steel_connections' / 'data' / '*.csv'),
     'steel_connections/data'),
    # QSS themes + resource images
    (str(SRC / 'steel_connections' / 'data' / 'themes'),
     'steel_connections/data/themes'),
]

all_datas    = occ_datas    + pyside_datas    + app_datas
all_binaries = occ_binaries + pyside_binaries
all_hidden   = (
    occ_hiddenimports
    + pyside_hiddenimports
    + collect_submodules('steel_connections')
    # pandas / numpy dynamic sub-modules
    + collect_submodules('pandas')
    + collect_submodules('numpy')
    # python-docx
    + collect_submodules('docx')
)

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(SRC / 'steel_connections' / 'main_window.py')],
    pathex=[str(SRC)],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # reduce size — not needed at runtime
        'tkinter', 'matplotlib', 'scipy', 'IPython', 'jupyter',
        'pytest', 'unittest',
    ],
    noarchive=False,
    optimize=0,
)

# ── PYZ archive ───────────────────────────────────────────────────────────────
pyz = PYZ(a.pure)

# ── EXE ───────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # COLLECT mode — folder output
    name='SteelConnections',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                      # UPX can corrupt OCC DLLs — keep disabled
    console=False,                  # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='installer\\icon.ico',   # uncomment and set path if you have an icon
)

# ── COLLECT ───────────────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SteelConnections',
)
