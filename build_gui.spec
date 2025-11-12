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

# 版本与产物名称配置（由 build_gui.py 传递环境变量）
gui_version = os.environ.get("QTOMOGRAPHY_GUI_VERSION", "v1.0")
gui_name = os.environ.get("QTOMOGRAPHY_GUI_NAME", "QTomography")


def _sanitize(token: str) -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
    return "".join(ch if ch in allowed else "_" for ch in token)


sanitized_version = _sanitize(gui_version)
sanitized_name = _sanitize(gui_name).strip()
if not sanitized_name:
    sanitized_name = "QTomography"

exe_base_name = f"{sanitized_name}_{sanitized_version}"

# PyInstaller 加密相关（可选，设置为 None 表示不使用加密）
block_cipher = None

a = Analysis(
    ['run_gui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 包含用户文档（打包到 exe 同目录的 packaging/ 文件夹）
        (str(project_root / 'packaging' / 'USER_GUIDE.md'), 'packaging'),
        (str(project_root / 'packaging' / 'DATA_FORMAT_GUIDE.md'), 'packaging'),
        (str(project_root / 'packaging' / 'README.txt'), 'packaging'),
        (str(project_root / 'packaging' / 'README.md'), 'packaging'),
    ],
    hiddenimports=[
        'qtomography',
        'qtomography.gui',
        'qtomography.gui.app',
        'qtomography.gui.main_window',
        'qtomography.gui.panels',
        'qtomography.gui.services',
        'qtomography.gui.services.fidelity_service',
        'qtomography.gui.widgets',
        'qtomography.gui.domain',
        'qtomography.gui.application',
        'qtomography.gui.infrastructure',
        'qtomography.gui.panels.fidelity_panel',
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
    name=exe_base_name,
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

# 注意：
# 1. 当前使用单文件模式（onefile），datas 中的文件会被打包到 exe 内部
#    运行时解压到临时目录（sys._MEIPASS），不会自动出现在 dist 目录中
# 2. build_gui.py 脚本会在打包完成后自动复制 packaging 文件夹到 dist 目录
#    这样用户可以直接在 exe 同目录看到文档

