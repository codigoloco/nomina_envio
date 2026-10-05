# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# Archivos y carpetas adicionales a incluir en la compilación
added_files = [
    ('migraciones', 'migraciones'),
    ('plantilla_pagos_ejemplo.xlsx', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # GUI PyQt5
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'PyQt5.sip',

        # Procesamiento de datos y Excel
        'pandas',
        'openpyxl',

        # Conexiones a bases de datos
        'sqlite3',
        'pyodbc',
        'pymysql',
        'psycopg2',

        # Envío de correos SMTP
        'smtplib',
        'email',
        'email.mime.multipart',
        'email.mime.text',

        # Migraciones dinámicas
        'migraciones',
        'migraciones.2026_10_03_184000_crear_tabla_migraciones',
        'migraciones.2026_10_03_184100_crear_tabla_empleados',
        'migraciones.2026_10_03_184200_crear_tabla_envios',
        'migraciones.2026_10_03_184300_crear_tabla_configuraciones',
        'migraciones.2026_10_03_184400_crear_tabla_auditoria',
        'migraciones.2026_10_03_184500_crear_tabla_config_carga_excel',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NominaApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NominaApp',
)
