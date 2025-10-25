# -*- mode: python ; coding: utf-8 -*-
import sys

icon_file = None
if sys.platform.startswith("win"):
    icon_file = "app_icon.ico"
elif sys.platform == "darwin":  # macOS
    icon_file = "app_icon.icns"
else:  # Linux
    icon_file = "app_icon_256x256.png"
block_cipher = None

a = Analysis(
    ['app.py'],                       # 👈 your Tkinter entry script
    pathex=[],
    binaries=[],
    datas = [
    ('downloadByDateApp.py', '.'),
    ('downloadPostsApp.py', '.'),
    ('downloadReelsApp.py', '.'),
    ('downloadStoriesApp.py', '.'),
    ('downloadHighlightsApp.py', '.'),
    ('downloadbyUrlApp.py', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Easy Instagram Downloader',   # 👈 name of your app
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                     # 👈 False = no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,          # 👈 optional app icon
)
