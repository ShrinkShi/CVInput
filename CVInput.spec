# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


datas = [
    ('icon.ico', '.'),
    ('assets/icon/icon512.png', 'assets/icon'),
    ('assets/icon/icon256.png', 'assets/icon'),
]

for asset in ('about.png', 'close.png', 'email.png', 'github.png', 'min.png', 'set.png', 'top.png'):
    datas.append((f'assets/{asset}', 'assets'))

for locale_file in Path('src/locales').glob('*.json'):
    datas.append((str(locale_file), 'src/locales'))


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CVInput',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
