# QTomography GUI 打包完整教程

> 从零开始，详细讲解如何将 QTomography GUI 打包成独立的桌面应用程序

**最后更新**: 2025年11月  
**适用版本**: v1.0.0+

---

## 📋 目录

1. [打包概述](#打包概述)
2. [打包前准备](#打包前准备)
3. [打包步骤详解](#打包步骤详解)
4. [打包后测试](#打包后测试)
5. [创建安装程序](#创建安装程序)
6. [分发和部署](#分发和部署)
7. [常见问题解决](#常见问题解决)
8. [进阶优化](#进阶优化)

---

## 📦 打包概述

### 什么是打包？

打包是将 Python 应用程序及其所有依赖项（包括 Python 解释器、库文件等）打包成一个独立的可执行文件的过程。用户无需安装 Python 或任何依赖，直接运行 `.exe` 文件即可使用。

### 打包后的效果

- ✅ **单文件可执行程序**：一个 `.exe` 文件包含所有内容
- ✅ **无需安装 Python**：用户不需要安装 Python 环境
- ✅ **无需安装依赖**：所有依赖都已打包在内
- ✅ **跨机器运行**：可以在任何 Windows 10+ 机器上运行

### 打包工具选择

本项目使用 **PyInstaller**，原因：
- ✅ 简单易用，配置灵活
- ✅ 支持单文件模式（一个 exe）
- ✅ 自动处理依赖关系
- ✅ 跨平台支持（Windows、macOS、Linux）
- ✅ 社区活跃，文档完善

---

## 🔧 打包前准备

### 1. 检查系统要求

**操作系统**：
- Windows 10 或更高版本
- 至少 2GB 可用磁盘空间（用于构建过程）

**Python 环境**：
- Python 3.9 或更高版本
- 已安装所有项目依赖

### 2. 安装必要工具

#### 2.1 安装 PyInstaller

```bash
pip install pyinstaller
```

验证安装：
```bash
pyinstaller --version
```

#### 2.2 安装项目依赖

确保所有依赖都已安装：

```bash
# 安装所有依赖（包括 GUI）
pip install -r requirements.txt

# 或使用开发模式安装
pip install -e ".[gui,dev]"
```

#### 2.3 验证 GUI 可以正常运行

在打包前，确保 GUI 应用可以正常启动：

```bash
python run_gui.py
```

测试所有主要功能：
- ✅ 打开数据文件
- ✅ 配置参数
- ✅ 执行重构
- ✅ 查看结果
- ✅ 保存配置

### 3. 准备资源文件（可选）

如果需要应用图标：

1. **准备图标文件**：
   - Windows: `.ico` 格式（推荐 256x256 或 512x512）
   - 可以使用在线工具将 PNG 转换为 ICO：https://convertio.co/zh/png-ico/

2. **放置图标文件**：
   ```
   项目根目录/
    └── resources/
        └── icon.ico
   ```

3. **更新配置文件**：
   在 `build_gui.spec` 中修改：
   ```python
   exe = EXE(
       # ... 其他配置 ...
       icon='resources/icon.ico',  # 添加这一行
   )
   ```

---

## 🚀 打包步骤详解

### 方法 1：使用打包脚本（推荐）

这是最简单的方法：

```bash
python build_gui.py
```

**脚本会自动**：
1. 检查 PyInstaller 是否安装
2. 如果未安装，提示是否安装
3. 执行打包过程
4. 显示打包结果

**输出**：
```
============================================================
QTomography GUI 打包工具
============================================================

开始打包 GUI 应用...
使用配置文件: build_gui.spec

============================================================
[SUCCESS] 打包完成！
============================================================

可执行文件位置: dist/QTomography.exe
构建目录: build/
```

### 方法 2：直接使用 PyInstaller

如果你想更精细地控制打包过程：

```bash
pyinstaller build_gui.spec
```

**参数说明**：
- `--clean`: 清理临时文件（推荐）
- `--noconfirm`: 不询问，直接覆盖已存在的文件
- `--debug=all`: 显示详细调试信息（遇到问题时使用）

**完整命令示例**：
```bash
pyinstaller --clean --noconfirm build_gui.spec
```

### 打包过程详解

打包过程通常需要 2-5 分钟，包含以下步骤：

1. **分析阶段** (Analysis)：
   - 扫描所有 Python 文件
   - 识别所有依赖项
   - 生成依赖关系图

2. **收集阶段** (Collecting)：
   - 收集所有需要的文件
   - 复制库文件和数据文件

3. **构建阶段** (Building)：
   - 创建 Python 字节码归档 (PYZ)
   - 创建打包归档 (PKG)
   - 生成可执行文件 (EXE)

4. **完成**：
   - 可执行文件位于 `dist/QTomography.exe`
   - 构建文件位于 `build/` 目录

### 打包输出说明

打包完成后，你会看到以下目录结构：

```
项目根目录/
├── build/                    # 构建临时文件（可删除）
│   └── build_gui/
│       ├── Analysis-00.toc
│       ├── EXE-00.toc
│       └── ...
├── dist/                      # 最终输出目录
│   └── QTomography.exe        # ⭐ 这就是打包后的可执行文件
└── build_gui.spec            # 打包配置文件
```

**重要文件**：
- `dist/QTomography.exe` - **这是你要分发给用户的文件**
- `build/` - 可以删除，只是临时构建文件

---

## 🧪 打包后测试

### 1. 本地测试

#### 1.1 基本启动测试

```bash
# 直接双击运行
dist\QTomography.exe
```

**检查项**：
- [ ] 应用能正常启动（可能需要 3-5 秒）
- [ ] 窗口正常显示
- [ ] 没有错误提示

#### 1.2 功能测试

测试所有主要功能：

**数据加载**：
- [ ] 能打开 CSV 文件
- [ ] 能打开 Excel 文件
- [ ] 文件信息正确显示

**参数配置**：
- [ ] 能修改维度
- [ ] 能选择重构方法
- [ ] 能配置其他参数

**执行重构**：
- [ ] 能执行线性重构
- [ ] 能执行 WLS 重构
- [ ] 进度显示正常
- [ ] 结果正确显示

**结果查看**：
- [ ] 能查看汇总表格
- [ ] 能查看可视化图表
- [ ] 能执行谱分解

**配置保存**：
- [ ] 能保存配置
- [ ] 能加载配置
- [ ] 配置持久化正常

**日志检查**：
- [ ] 日志文件正常生成
- [ ] 日志位置：`~/.qtomography/logs/qtomography_gui.log`

### 2. 干净环境测试

在另一台机器或虚拟机中测试（**确保没有安装 Python**）：

#### 2.1 准备测试环境

1. **创建测试虚拟机**（可选但推荐）：
   - 使用 VirtualBox 或 VMware
   - 安装 Windows 10
   - **不要安装 Python**

2. **或使用另一台机器**：
   - 确保没有安装 Python
   - 确保没有安装相关依赖

#### 2.2 复制和测试

1. **复制文件**：
   ```
   只需复制一个文件：QTomography.exe
   ```

2. **运行测试**：
   - 双击 `QTomography.exe`
   - 测试所有功能
   - 检查是否有错误

3. **检查系统要求**：
   - 可能需要 Visual C++ Redistributable（通常已预装）
   - 如果缺少，会提示安装

### 3. 性能测试

**启动时间**：
- 首次启动：通常 3-5 秒（需要解压）
- 后续启动：通常 1-2 秒

**内存占用**：
- 正常使用：约 200-500 MB
- 处理大数据：可能达到 1 GB

**文件大小**：
- 正常范围：150-200 MB
- 如果超过 300 MB，可能需要优化

---

## 📦 创建安装程序（可选）

虽然单个 `.exe` 文件已经可以分发，但创建安装程序可以提供更好的用户体验。

### Windows 安装程序工具

#### 选项 1：Inno Setup（推荐）

**优点**：
- ✅ 免费开源
- ✅ 简单易用
- ✅ 功能强大
- ✅ 中文支持

**步骤**：

1. **下载安装 Inno Setup**：
   - 访问：https://jrsoftware.org/isinfo.php
   - 下载并安装

2. **创建安装脚本**：
   ```inno
   [Setup]
   AppName=QTomography
   AppVersion=1.0.0
   DefaultDirName={pf}\QTomography
   DefaultGroupName=QTomography
   OutputDir=installer
   OutputBaseFilename=QTomography-Setup
   Compression=lzma2
   SolidCompression=yes

   [Files]
   Source: "dist\QTomography.exe"; DestDir: "{app}"; Flags: ignoreversion

   [Icons]
   Name: "{group}\QTomography"; Filename: "{app}\QTomography.exe"
   Name: "{commondesktop}\QTomography"; Filename: "{app}\QTomography.exe"
   ```

3. **编译安装程序**：
   - 在 Inno Setup 中打开脚本
   - 点击"构建" → "编译"
   - 生成 `QTomography-Setup.exe`

#### 选项 2：NSIS

类似 Inno Setup，但使用不同的脚本语言。

### 安装程序功能

一个好的安装程序应该包括：

- ✅ **安装向导**：引导用户完成安装
- ✅ **开始菜单快捷方式**：方便启动
- ✅ **桌面快捷方式**：快速访问
- ✅ **卸载程序**：方便卸载
- ✅ **版本信息**：显示应用版本

---

## 📤 分发和部署

### 1. 准备分发文件

#### 单文件分发

**最简单的方式**：
- 直接分发 `QTomography.exe`
- 用户下载后直接运行

**优点**：
- ✅ 简单直接
- ✅ 无需安装
- ✅ 便携性强

**缺点**：
- ⚠️ 文件较大（150+ MB）
- ⚠️ 没有卸载程序

#### 安装程序分发

**更专业的方式**：
- 分发 `QTomography-Setup.exe`
- 用户运行安装程序

**优点**：
- ✅ 专业体验
- ✅ 有卸载程序
- ✅ 可以创建快捷方式

### 2. 分发渠道

#### GitHub Releases（推荐）

1. **创建 Release**：
   - 访问 GitHub 仓库
   - 点击 "Releases" → "Draft a new release"
   - 填写版本号和说明

2. **上传文件**：
   - 上传 `QTomography.exe` 或安装程序
   - 添加说明文档

3. **用户下载**：
   - 用户从 Releases 页面下载
   - 自动显示下载次数

#### 其他分发方式

- **网盘**：百度网盘、OneDrive 等
- **文件服务器**：公司内部服务器
- **CDN**：如果有很多用户

### 3. 用户文档

#### 完整用户使用指南

已创建详细的用户使用指南：**[packaging/USER_GUIDE.md](USER_GUIDE.md)**

包含：
- 📖 快速开始指南
- 💻 系统要求和安装说明
- 🖥️ 界面详细介绍
- 📚 完整使用教程（3个教程）
- 🔧 功能详解
- ❓ 常见问题解答
- 🔍 故障排除指南

#### 简单 README.txt（随程序分发）

可以创建一个简单的 `README.txt` 文件随程序一起分发：

**README.txt**（模板）：
```
QTomography GUI v1.0.0
=====================

系统要求：
- Windows 10 或更高版本
- 至少 500 MB 可用磁盘空间

安装说明：
1. 下载 QTomography.exe
2. 双击运行即可（无需安装）

快速开始：
1. 启动程序（首次启动可能需要 3-5 秒）
2. 点击"选择文件"加载数据（CSV 或 Excel）
3. 配置参数（维度、重构方法等）
4. 点击"执行重构"
5. 查看结果（汇总表格和可视化图表）

详细使用指南：
请查看 USER_GUIDE.md 文件（如果已提供）

问题反馈：
- GitHub Issues: https://github.com/yourusername/qtomography/issues
- 邮箱: your.email@example.com

日志文件位置：
C:\Users\<用户名>\.qtomography\logs\qtomography_gui.log

如有问题，请提供日志文件内容以便诊断。
```

---

## ❓ 常见问题解决

### 问题 1：打包后无法启动

**症状**：双击 exe 文件没有反应或立即退出

**可能原因**：
- 缺少隐藏导入
- 路径问题
- 依赖缺失

**解决方案**：

1. **使用控制台模式查看错误**：
   修改 `build_gui.spec`：
   ```python
   console=True,  # 改为 True
   ```
   重新打包，运行时会显示错误信息

2. **检查隐藏导入**：
   在 `build_gui.spec` 的 `hiddenimports` 中添加缺失的模块

3. **查看警告文件**：
   ```
   build/build_gui/warn-build_gui.txt
   ```
   检查是否有缺失的模块警告

### 问题 2：文件过大（>300 MB）

**原因**：
- 包含了不必要的依赖
- 使用了单文件模式

**解决方案**：

1. **排除更多模块**：
   ```python
   excludes=[
       # ... 现有排除项 ...
       'matplotlib.tests',
       'numpy.tests',
       'scipy.tests',
       # 添加更多不需要的模块
   ],
   ```

2. **使用目录模式**（文件更小，但启动更快）：
   ```python
   onefile=False,  # 改为 False
   ```

### 问题 3：启动慢（>10 秒）

**原因**：
- 单文件模式需要解压
- 包含大量依赖

**解决方案**：

1. **使用目录模式**：
   ```python
   onefile=False,
   ```
   启动会更快，但会有多个文件

2. **使用 Nuitka 编译**（性能更好）：
   ```bash
   pip install nuitka
   python -m nuitka --standalone --onefile --windows-disable-console run_gui.py
   ```

### 问题 4：杀毒软件误报

**症状**：杀毒软件报告 exe 文件为病毒

**原因**：
- PyInstaller 打包的文件可能被误报
- 没有代码签名

**解决方案**：

1. **代码签名**（需要证书）：
   ```bash
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com QTomography.exe
   ```

2. **提交到杀毒软件厂商**：
   - 向各大杀毒软件厂商提交样本
   - 申请白名单

3. **在 GitHub Release 中说明**：
   - 说明这是误报
   - 提供源代码链接

### 问题 5：缺少 DLL 或依赖

**症状**：运行时提示缺少某个 DLL

**解决方案**：

1. **安装 Visual C++ Redistributable**：
   - 下载并安装最新版本
   - 通常已预装在 Windows 10+

2. **在 spec 文件中明确包含 DLL**：
   ```python
   binaries=[
       ('path/to/missing.dll', '.'),
   ],
   ```

### 问题 6：日志文件无法写入

**症状**：应用运行但日志文件没有生成

**检查**：
- 日志位置：`~/.qtomography/logs/qtomography_gui.log`
- 检查目录权限
- 检查磁盘空间

**解决方案**：
- 确保用户有写入权限
- 检查磁盘空间
- 查看应用是否有错误提示

---

## 🎯 进阶优化

### 1. 减小文件大小

#### 排除不必要的模块

```python
excludes=[
    'tkinter',
    'matplotlib.tests',
    'numpy.tests',
    'scipy.tests',
    'pytest',
    'IPython',
    'jupyter',
    'notebook',
    'sphinx',
    # 添加更多不需要的模块
],
```

#### 使用 UPX 压缩

已在配置中启用：
```python
upx=True,  # 已启用
```

### 2. 提高启动速度

#### 使用目录模式

```python
onefile=False,  # 改为 False
```

**优点**：
- ✅ 启动更快（无需解压）
- ✅ 文件更小

**缺点**：
- ⚠️ 多个文件（需要一起分发）

#### 使用 Nuitka 编译

```bash
pip install nuitka
python -m nuitka --standalone --onefile --windows-disable-console run_gui.py
```

**优点**：
- ✅ 性能更好（编译为 C++）
- ✅ 启动更快
- ✅ 文件更小

**缺点**：
- ⚠️ 需要 C++ 编译器
- ⚠️ 编译时间更长

### 3. 添加版本信息

创建 `version_info.txt`：

```python
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    # ...
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Your Company'),
        StringStruct('FileDescription', 'QTomography - Quantum State Tomography Tool'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('ProductName', 'QTomography'),
        StringStruct('ProductVersion', '1.0.0.0')
      ])
    ]),
  ]
)
```

在 `build_gui.spec` 中添加：
```python
exe = EXE(
    # ... 其他配置 ...
    version='version_info.txt',
)
```

### 4. 自动化打包流程

创建 `build_and_test.bat`：

```batch
@echo off
echo 开始打包 QTomography GUI...

REM 清理旧的构建文件
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 执行打包
python build_gui.py

REM 检查打包是否成功
if exist dist\QTomography.exe (
    echo.
    echo [SUCCESS] 打包成功！
    echo 文件位置: dist\QTomography.exe
    echo.
    echo 是否现在测试？(Y/N)
    set /p test= 
    if /i "%test%"=="Y" (
        start dist\QTomography.exe
    )
) else (
    echo.
    echo [ERROR] 打包失败！
    pause
)
```

---

## 📚 参考资源

### 官方文档

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [PySide6 部署指南](https://doc.qt.io/qtforpython/deployment.html)

### 相关工具

- [Inno Setup](https://jrsoftware.org/isinfo.php) - Windows 安装程序制作工具
- [Nuitka](https://nuitka.net/) - Python 编译器
- [UPX](https://upx.github.io/) - 可执行文件压缩工具

### 社区资源

- [PyInstaller GitHub Issues](https://github.com/pyinstaller/pyinstaller/issues)
- [Stack Overflow - PyInstaller 标签](https://stackoverflow.com/questions/tagged/pyinstaller)

---

## ✅ 检查清单

### 打包前

- [ ] Python 环境已配置
- [ ] 所有依赖已安装
- [ ] GUI 应用可以正常运行
- [ ] PyInstaller 已安装
- [ ] 资源文件已准备（如需要）

### 打包后

- [ ] 可执行文件已生成
- [ ] 本地测试通过
- [ ] 功能测试通过
- [ ] 干净环境测试通过
- [ ] 性能测试通过

### 分发前

- [ ] 用户文档已准备
- [ ] 安装程序已创建（如需要）
- [ ] 版本信息已更新
- [ ] 分发渠道已准备

---

**最后更新**: 2025年11月  
**维护者**: QTomography 开发团队

如有问题或建议，请提交 [GitHub Issue](https://github.com/yourusername/qtomography/issues)

