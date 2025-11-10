# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - QTomography GUI 打包配置
使用方法: pyinstaller build_gui.spec
"""

import sys
import os
from pathlib import Path

# 项目根目录（PyInstaller spec 文件中不能使用 __file__，使用当前工作目录）
project_root = Path(os.getcwd())

# PyInstaller 加密相关（可选，设置为 None 表示不使用加密）
block_cipher = None

a = Analysis(
    ['run_gui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 如果需要包含数据文件，在这里添加
        # ('path/to/data', 'data'),
    ],
    hiddenimports=[
        'qtomography',
        'qtomography.gui',
        'qtomography.gui.app',
        'qtomography.gui.main_window',
        'qtomography.gui.panels',
        'qtomography.gui.services',
        'qtomography.gui.widgets',
        'qtomography.gui.domain',
        'qtomography.gui.application',
        'qtomography.gui.infrastructure',
        'qtomography.app',
        'qtomography.app.controller',
        'qtomography.app.config_io',
        'qtomography.domain',
        'qtomography.domain.reconstruction',
        'qtomography.domain.measurement',
        'qtomography.infrastructure',
        'qtomography.infrastructure.visualization',
        'qtomography.infrastructure.persistence',
        'qtomography.analysis',
        'PySide6',
        'numpy',
        'scipy',
        'pandas',
        'matplotlib',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.tests',
        'numpy.tests',
        'scipy.tests',
        'pytest',
        'IPython',
        'jupyter',
        'win32com',
        'pythoncom',
        'pywintypes',
        'win32api',
        'win32con',
        'win32gui',
        'win32service',
        'win32serviceutil',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QTomography',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口（GUI应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，在这里指定路径，例如: 'resources/icon.ico'
)

