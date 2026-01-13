# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MurmurTone
Build with: pyinstaller murmurtone.spec
"""

import os
import sys

block_cipher = None

# Get the directory containing this spec file
spec_dir = os.path.dirname(os.path.abspath(SPEC))

# Data files to include
datas = [
    ('icon.ico', '.'),
    ('icon.png', '.'),
    ('LICENSE', '.'),
    ('THIRD_PARTY_LICENSES.md', '.'),
    ('assets/logo/murmurtone-logo-icon.ico', 'assets/logo'),
]

# Check if bundled model exists and include it
model_dir = os.path.join(spec_dir, 'models', 'tiny.en')
if os.path.exists(model_dir):
    datas.append(('models/tiny.en', 'models/tiny.en'))
    print(f"Including bundled model from: {model_dir}")
else:
    print(f"WARNING: No bundled model found at {model_dir}")
    print("The app will download the model on first run.")

a = Analysis(
    ['murmurtone.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # faster-whisper and ctranslate2
        'faster_whisper',
        'ctranslate2',

        # pynput Windows backend
        'pynput.keyboard._win32',
        'pynput.mouse._win32',

        # Audio
        'sounddevice',
        '_sounddevice_data',

        # GUI
        'tkinter',
        'tkinter.ttk',

        # Other
        'numpy',
        'PIL',
        'pystray',
        'pystray._win32',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused modules to reduce size
        'matplotlib',
        'scipy',
        'pandas',
        'torch',  # We use ctranslate2, not torch
        'tensorflow',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MurmurTone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window - runs as tray app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MurmurTone',
)
