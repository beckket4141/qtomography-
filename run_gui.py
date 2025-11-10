#!/usr/bin/env python3
"""
QTomography GUI 启动脚本
支持直接运行，无需模块导入
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 现在可以正常导入
from qtomography.gui.app import main

if __name__ == "__main__":
    sys.exit(main())
