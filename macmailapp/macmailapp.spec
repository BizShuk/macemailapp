# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['macmailapp/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('macmailapp/macmailapp.applescript', 'macmailapp')],
    hidden_imports=['ScriptingBridge', 'AppKit'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mail',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)