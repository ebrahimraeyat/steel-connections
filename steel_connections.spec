# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for Steel Connection Designer
# Build from the osdag-2025 conda environment (contains pythonocc-core).
#
# Usage (from repo root, inside activated osdag-2025 env):
#   pyinstaller steel_connections.spec --noconfirm
# ---------------------------------------------------------

import glob
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

SRC = Path('src')


def collect_conda_occt_runtime_binaries():
    """
    Collect OCCT runtime DLLs from <conda>/Library/bin.
    IMPORTANT: exclude all Qt DLLs — PySide6 ships its own Qt and mixing
    conda's Qt DLLs would cause 'procedure not found' errors.
    """
    lib_bin = Path(sys.prefix) / 'Library' / 'bin'
    if not lib_bin.exists():
        print(f"[DEBUG] Library/bin not found at {lib_bin}, skipping.")
        return []

    # Only these prefixes are OCCT/FreeImage/TBB — safe to add
    INCLUDE_PREFIXES = (
        'tk',       # TK*.dll  — OCCT modules
        'tbb',      # tbb*.dll — Intel TBB (OCCT threading)
        'tbbmalloc',
        'freeimage',
        'freetype',
        'openvr',
        'openal',
    )

    # Never copy anything that looks like a Qt or PyQt DLL
    EXCLUDE_PREFIXES = (
        'qt',       # Qt5*.dll, Qt6*.dll, QtCore.dll …
        'pyqt',
        'shiboken',
    )

    collected = []
    seen = set()
    for dll_path in lib_bin.glob('*.dll'):
        dll_name = dll_path.name.lower()
        if dll_name in seen:
            continue
        if any(dll_name.startswith(p) for p in EXCLUDE_PREFIXES):
            continue
        if any(dll_name.startswith(p) for p in INCLUDE_PREFIXES):
            seen.add(dll_name)
            collected.append((str(dll_path), '.'))

    print(f"[DEBUG] OCCT runtime DLLs from {lib_bin}: {len(collected)}")
    for p, _ in collected:
        print(f"        {Path(p).name}")
    return collected

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
all_binaries = occ_binaries + pyside_binaries + collect_conda_occt_runtime_binaries()
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
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # reduce size — not needed at runtime
        'tkinter', 'matplotlib', 'scipy', 'IPython', 'jupyter',
        'pytest', 'unittest',
        # exclude conflicting Qt binding — only PySide6 is used
        'PyQt5', 'PyQt6',
        # --- Heavy Qt Modules (Not used in this app) ---
        'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DExtras',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtCharts',
        'PySide6.QtDataVisualization', 'PySide6.QtNetwork',
        'PySide6.QtTextToSpeech', 'PySide6.QtVirtualKeyboard',
        'PySide6.QtLocation', 'PySide6.QtPositioning',
        'PySide6.QtBluetooth', 'PySide6.QtNfc', 'PySide6.QtSerialPort'
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
