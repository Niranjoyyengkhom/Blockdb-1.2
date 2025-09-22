
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['iedb_api.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('auth_data', 'auth_data'),
        ('encryption', 'encryption'),
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'uvicorn.main',
        'uvicorn.server',
        'fastapi',
        'pydantic',
        'jose',
        'passlib',
        'cryptography',
        'email_validator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='IEDB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='iedb_icon.ico' if os.path.exists('iedb_icon.ico') else None,
)
