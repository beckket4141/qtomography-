"""命令行接口入口模块。

这个 __init__.py 文件的作用：
==================

1. 将 cli 目录标记为 Python 包（package）
2. 定义包的公开接口（public API）
3. 简化导入路径


Python 知识点详解：
==================

知识点 1: __init__.py 的作用
----------------------------
在 Python 中，一个包含 __init__.py 的目录会被识别为"包"（package）。
没有这个文件，Python 就不会把这个目录当作包来处理。

目录结构：
    qtomography/
    └── cli/
        ├── __init__.py   ← 这个文件！使 cli 成为一个包
        └── main.py       ← 包含实际功能代码

知识点 2: 相对导入 (from .main import main)
------------------------------------------
语法：from .模块名 import 对象名
    - '.' 表示当前包（cli/）
    - 'main' 表示 main.py 模块
    - 最后的 'main' 是函数名

等价于：from qtomography.cli.main import main

知识点 3: __all__ 的作用
------------------------
__all__ 定义了当使用 'from qtomography.cli import *' 时，
哪些名称会被导出（公开接口）。

这是一种"显式声明"的方式，提高代码可维护性。

知识点 4: 导入路径简化
----------------------
有了这个 __init__.py，用户可以用更简洁的方式导入：

    # 方式 1：简洁导入（推荐）
    from qtomography.cli import main
    
    # 方式 2：完整路径导入
    from qtomography.cli.main import main

两者等价，但方式 1 更简洁！
"""

# ========== 相对导入 ==========
# 从同一包内的 main.py 模块导入 main 函数
# '.' 表示当前包（cli/）
from .main import main

# ========== 公开接口声明 ==========
# 定义这个包对外暴露的接口
# 当使用 'from qtomography.cli import *' 时，只会导入这里列出的名称
__all__ = ["main"]
