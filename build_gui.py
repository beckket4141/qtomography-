#!/usr/bin/env python3
"""
QTomography GUI 打包脚本
使用 PyInstaller 将 GUI 应用打包为独立的可执行文件

使用方法:
    python build_gui.py
"""

import subprocess
import sys
from pathlib import Path

def check_pyinstaller():
    """检查是否安装了 PyInstaller"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """安装 PyInstaller"""
    print("正在安装 PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("PyInstaller 安装完成！")

def build_gui():
    """构建 GUI 可执行文件"""
    spec_file = Path(__file__).parent / "build_gui.spec"
    
    if not spec_file.exists():
        print(f"错误: 找不到配置文件 {spec_file}")
        return False
    
    print("开始打包 GUI 应用...")
    print(f"使用配置文件: {spec_file}")
    
    try:
        # 运行 PyInstaller
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            str(spec_file)
        ])
        
        print("\n" + "="*60)
        print("[SUCCESS] 打包完成！")
        print("="*60)
        print(f"\n可执行文件位置: dist/QTomography.exe")
        print(f"构建目录: build/")
        print("\n提示:")
        print("- 可以将 dist/QTomography.exe 分发给用户")
        print("- 首次运行可能需要几秒钟加载时间")
        print("- 确保目标机器有必要的系统依赖（如 Visual C++ Redistributable）")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] 打包失败: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("QTomography GUI 打包工具")
    print("="*60)
    print()
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        print("未检测到 PyInstaller，需要安装...")
        response = input("是否现在安装？(y/n): ").strip().lower()
        if response == 'y':
            install_pyinstaller()
        else:
            print("请先安装 PyInstaller: pip install pyinstaller")
            return 1
    
    # 构建
    if build_gui():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

