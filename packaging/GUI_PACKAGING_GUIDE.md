# QTomography GUI 打包完整指南

## 🎯 打包准备状态评估

### ✅ 已就绪的部分

1. **代码结构** ✅
   - GUI 入口清晰：`run_gui.py` 和 `qtomography.gui.app.main`
   - 模块化设计，依赖关系明确
   - 没有硬编码的绝对路径

2. **依赖管理** ✅
   - `requirements.txt` 和 `pyproject.toml` 已同步
   - PySide6 已正确声明
   - 所有核心依赖已列出

3. **路径处理** ✅
   - 配置文件使用用户目录：`~/.qtomography/gui_config.json`
   - 文件选择使用 Qt 标准对话框
   - 输出目录由用户指定

4. **打包配置** ✅
   - `build_gui.spec` 已创建
   - `build_gui.py` 打包脚本已就绪
   - 隐藏导入已配置

### ⚠️ 需要注意的部分

1. **日志路径** ✅ **已改进**
   - ~~当前使用相对路径 `logs/`，打包后可能无法写入~~
   - ✅ **已完成**：已改为用户目录 `~/.qtomography/logs/`
   - 日志文件位置：`~/.qtomography/logs/qtomography_gui.log`

2. **应用图标** ⚠️
   - 当前没有图标文件
   - **建议**：准备 `.ico` 文件（Windows）或 `.icns` 文件（macOS）

3. **版本显示** ⚠️
   - GUI 窗口标题显示 "QTomography GUI (MVP)"
   - **建议**：添加"关于"对话框显示版本号

## 🚀 快速开始打包

### 方法 1：使用打包脚本（推荐）

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 运行打包脚本
python build_gui.py
```

### 方法 2：直接使用 PyInstaller

```bash
pyinstaller build_gui.spec
```

### 打包结果

打包完成后，可执行文件位于：
- **Windows**: `dist/QTomography.exe`
- **macOS**: `dist/QTomography.app`
- **Linux**: `dist/QTomography`

## 📋 打包配置说明

### build_gui.spec 关键配置

```python
# 入口点
['run_gui.py']

# 隐藏导入（确保所有模块都被包含）
hiddenimports=[
    'qtomography',
    'qtomography.gui',
    # ... 其他模块
]

# 控制台模式（False = 不显示控制台窗口）
console=False

# 单文件模式（True = 一个exe文件，False = 目录模式）
onefile=True
```

## 🔧 可选改进建议

### 1. 改进日志路径 ✅ **已完成**

~~修改 `qtomography/gui/app.py`：~~

```python
def setup_logging() -> None:
    """Configure logging for GUI application.
    
    Logs are saved to the user's home directory under ~/.qtomography/logs/
    to ensure they can be written even when the application is packaged.
    """
    # 使用用户目录存储日志（与配置文件保持一致）
    # 这样打包后也能正常写入日志
    log_dir = Path.home() / ".qtomography" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # ... 其余代码保持不变
```

**优点**：
- ✅ 打包后也能正常写入日志
- ✅ 日志文件统一管理（与配置文件在同一目录）
- ✅ 符合桌面应用最佳实践

### 2. 添加应用图标

1. **准备图标文件**：
   - Windows: `resources/icon.ico` (256x256 或 512x512)
   - macOS: `resources/icon.icns`
   - 可以使用在线工具转换 PNG 到 ICO/ICNS

2. **更新 build_gui.spec**：
   ```python
   exe = EXE(
       # ... 其他配置 ...
       icon='resources/icon.ico',  # Windows
   )
   ```

3. **更新 build_gui.spec 的 datas**：
   ```python
   datas=[
       ('resources/icon.ico', 'resources'),  # 如果需要运行时访问
   ],
   ```

### 3. 添加版本信息（Windows）

创建 `version_info.txt`：

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Your Company'),
        StringStruct('FileDescription', 'QTomography - Quantum State Tomography Tool'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('InternalName', 'QTomography'),
        StringStruct('LegalCopyright', 'Copyright (C) 2025'),
        StringStruct('OriginalFilename', 'QTomography.exe'),
        StringStruct('ProductName', 'QTomography'),
        StringStruct('ProductVersion', '1.0.0.0')
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
```

然后在 `build_gui.spec` 中添加：

```python
exe = EXE(
    # ... 其他配置 ...
    version='version_info.txt',
)
```

### 4. 优化打包大小

如果打包文件过大，可以：

1. **排除不必要的模块**：
   ```python
   excludes=[
       'tkinter',
       'matplotlib.tests',
       'numpy.tests',
       'scipy.tests',
       'pytest',
       'IPython',
       'jupyter',
       # 添加更多不需要的模块
   ],
   ```

2. **使用 UPX 压缩**（如果可用）：
   ```python
   upx=True,  # 已在配置中启用
   ```

3. **使用目录模式**（启动更快）：
   ```python
   onefile=False,  # 改为 False
   ```

## 🧪 测试打包结果

### 本地测试

1. **基本功能测试**：
   ```bash
   # 运行打包后的应用
   dist/QTomography.exe  # Windows
   # 或
   dist/QTomography.app/Contents/MacOS/QTomography  # macOS
   ```

2. **功能检查清单**：
   - [ ] 应用能正常启动
   - [ ] 能打开数据文件（CSV/Excel）
   - [ ] 能配置参数
   - [ ] 能执行重构
   - [ ] 能查看结果
   - [ ] 能保存/加载配置
   - [ ] 日志文件正常生成

### 干净环境测试

在另一台机器或虚拟机中测试（确保没有安装 Python）：

1. 复制 `dist/QTomography.exe` 到测试机器
2. 运行并测试所有功能
3. 检查是否有缺失的 DLL 或依赖

## 📦 分发建议

### Windows

1. **直接分发**：
   - 提供 `QTomography.exe` 文件
   - 用户直接运行即可

2. **创建安装程序**（可选）：
   - 使用 [Inno Setup](https://jrsoftware.org/isinfo.php) 创建安装程序
   - 或使用 [NSIS](https://nsis.sourceforge.io/)

3. **系统要求**：
   - Windows 10 或更高版本
   - 可能需要 Visual C++ Redistributable（通常已预装）

### macOS

1. **创建 .app 包**：
   - PyInstaller 会自动创建 `.app` 包

2. **创建 .dmg 镜像**（可选）：
   ```bash
   # 使用 create-dmg 工具
   create-dmg QTomography.dmg dist/QTomography.app
   ```

3. **代码签名**（可选，用于 Gatekeeper）：
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/QTomography.app
   ```

### Linux

1. **AppImage**（推荐）：
   - 使用 [appimagetool](https://github.com/AppImage/AppImageKit) 创建 AppImage

2. **Snap**：
   - 创建 `snapcraft.yaml` 配置文件

3. **Flatpak**：
   - 创建 `flatpak.json` 配置文件

## ⚠️ 常见问题与解决方案

### 问题 1：打包后无法启动

**症状**：双击 exe 文件没有反应或立即退出

**可能原因**：
- 缺少隐藏导入
- 路径问题
- 依赖缺失

**解决方案**：
```bash
# 使用控制台模式查看错误
# 修改 build_gui.spec: console=True
pyinstaller build_gui.spec

# 或使用 --debug 参数
pyinstaller --debug=all build_gui.spec
```

### 问题 2：文件过大（>500MB）

**解决方案**：
- 使用目录模式（`onefile=False`）
- 排除更多不必要的模块
- 考虑使用 Nuitka 编译

### 问题 3：启动慢（>10秒）

**解决方案**：
- 使用目录模式（启动更快）
- 或使用 Nuitka 编译为原生代码

### 问题 4：杀毒软件误报

**解决方案**：
- 代码签名（需要证书）
- 提交到杀毒软件厂商白名单
- 在 GitHub Release 中提供说明

### 问题 5：缺少 DLL 或依赖

**Windows**：
- 确保安装了 Visual C++ Redistributable
- 检查是否有缺失的 Qt DLL

**解决方案**：
```python
# 在 build_gui.spec 中明确包含 DLL
binaries=[
    ('path/to/missing.dll', '.'),
],
```

## 🎯 推荐工作流

1. **开发阶段**：
   ```bash
   python run_gui.py  # 直接运行开发版本
   ```

2. **打包测试**：
   ```bash
   python build_gui.py  # 打包
   dist/QTomography.exe  # 测试
   ```

3. **发布准备**：
   - 更新版本号
   - 创建 GitHub Release
   - 上传可执行文件
   - 编写发布说明

## 📚 相关资源

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [PySide6 部署指南](https://doc.qt.io/qtforpython/deployment.html)
- [Python 应用打包最佳实践](https://realpython.com/pyinstaller-python/)

## ✅ 下一步行动

1. **立即可以做的**：
   - [ ] 运行 `python build_gui.py` 测试打包
   - [ ] 在本地测试打包结果

2. **建议改进**（可选）：
   - [x] 改进日志路径（使用用户目录）✅ **已完成**
   - [ ] 添加应用图标
   - [ ] 添加版本信息对话框

3. **发布准备**：
   - [ ] 在干净环境中测试
   - [ ] 创建 GitHub Release
   - [ ] 准备用户文档

---

**当前状态**：✅ **可以开始打包** - 所有必要的配置已就绪！

