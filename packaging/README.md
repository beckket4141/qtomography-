# QTomography GUI 打包指南

本目录包含将 QTomography GUI 打包为独立桌面应用的配置和脚本。

## 📦 打包工具选择

### 推荐：PyInstaller（已配置）

**优点**：
- ✅ 跨平台支持（Windows、macOS、Linux）
- ✅ 简单易用，配置灵活
- ✅ 自动处理依赖
- ✅ 支持单文件或目录模式
- ✅ 社区活跃，文档完善

**缺点**：
- ⚠️ 打包文件较大（~200-500MB）
- ⚠️ 首次启动可能较慢

## 🚀 快速开始

### 1. 安装打包工具

```bash
pip install pyinstaller
```

### 2. 打包应用

```bash
# 方式1：使用打包脚本（推荐）
python build_gui.py

# 方式2：直接使用 PyInstaller
pyinstaller build_gui.spec
```

### 3. 获取可执行文件

打包完成后，可执行文件位于：
- **Windows**: `dist/QTomography.exe`
- **macOS**: `dist/QTomography.app`
- **Linux**: `dist/QTomography`

## 📋 打包配置说明

### build_gui.spec

这是 PyInstaller 的配置文件，包含：
- **入口点**: `run_gui.py`
- **隐藏导入**: 所有必要的模块
- **排除项**: 测试、开发工具等不需要的模块
- **控制台**: 设置为 `False`（GUI应用不显示控制台）

### 自定义配置

#### 添加应用图标

1. 准备图标文件（`.ico` for Windows, `.icns` for macOS）
2. 在 `build_gui.spec` 中修改：
   ```python
   icon='resources/icon.ico',  # Windows
   # 或
   icon='resources/icon.icns',  # macOS
   ```

#### 单文件模式 vs 目录模式

当前配置为**单文件模式**（一个exe文件）。如需目录模式（更快启动），修改 `build_gui.spec`：

```python
exe = EXE(
    # ... 其他配置 ...
    onefile=False,  # 改为 False 使用目录模式
)
```

#### 包含数据文件

如果需要包含额外的数据文件，在 `build_gui.spec` 的 `datas` 列表中添加：

```python
datas=[
    ('path/to/data', 'data'),
    ('path/to/config', 'config'),
],
```

## 🔧 其他打包工具

### 选项 2：Nuitka（编译为原生代码）

**优点**：
- ✅ 性能更好（编译为C++）
- ✅ 文件更小
- ✅ 启动更快

**缺点**：
- ⚠️ 配置更复杂
- ⚠️ 需要C++编译器

```bash
pip install nuitka
python -m nuitka --standalone --onefile --windows-disable-console run_gui.py
```

### 选项 3：cx_Freeze

```bash
pip install cx_Freeze
# 需要创建 setup.py 配置文件
```

### 选项 4：Briefcase (BeeWare)

适合需要发布到应用商店的场景。

```bash
pip install briefcase
briefcase create
briefcase build
```

## 📝 打包前检查清单

- [ ] 确保所有依赖已安装
- [ ] 测试 GUI 应用正常运行
- [ ] 检查是否有外部资源文件需要包含
- [ ] 准备应用图标（可选）
- [ ] 更新版本号（在 pyproject.toml 中）
- [ ] 测试打包后的应用

## 🧪 测试打包结果

1. **在干净环境中测试**：
   - 在另一台机器上测试
   - 或在虚拟机中测试
   - 确保没有安装 Python 和相关依赖

2. **检查功能**：
   - 启动应用
   - 测试所有主要功能
   - 检查文件读写权限
   - 检查日志文件生成

## 📦 分发建议

### Windows
- 提供 `.exe` 文件
- 考虑创建安装程序（使用 Inno Setup 或 NSIS）
- 提供卸载程序

### macOS
- 提供 `.app` 文件或 `.dmg` 镜像
- 可能需要代码签名（用于 Gatekeeper）

### Linux
- 提供 AppImage、Snap 或 Flatpak 格式
- 或提供 `.deb`/`.rpm` 包

## ⚠️ 注意事项

1. **文件大小**：打包后的文件可能较大（200-500MB），这是正常的
2. **启动时间**：首次启动可能需要几秒钟解压
3. **系统依赖**：Windows 可能需要 Visual C++ Redistributable
4. **杀毒软件**：可能误报，需要代码签名或提交到杀毒软件厂商
5. **路径问题**：打包后路径可能不同，使用 `sys._MEIPASS` 访问资源

## 🔗 相关资源

- [PyInstaller 文档](https://pyinstaller.org/)
- [PySide6 打包指南](https://doc.qt.io/qtforpython/deployment.html)
- [Python 应用打包最佳实践](https://packaging.python.org/)

