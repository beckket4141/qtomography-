# GUI 打包检查清单

在打包 GUI 应用之前，请完成以下检查：

## ✅ 打包前检查

### 1. 代码完整性
- [ ] 所有 GUI 功能已测试通过
- [ ] 没有硬编码的绝对路径
- [ ] 所有依赖都已正确声明（requirements.txt / pyproject.toml）
- [ ] 没有未提交的临时文件或调试代码

### 2. 依赖检查
- [ ] 核心依赖：numpy, scipy, pandas, matplotlib, PySide6
- [ ] 可选依赖已明确标注（如 numba, qutip）
- [ ] 所有依赖版本已固定（避免兼容性问题）

### 3. 资源文件
- [ ] 检查是否需要图标文件（.ico / .icns）
- [ ] 检查是否有数据文件需要打包
- [ ] 检查是否有配置文件模板需要包含

### 4. 路径处理
- [ ] 配置文件路径使用用户目录（`~/.qtomography/`）✅ 已确认
- [ ] 日志文件路径使用相对路径或用户目录 ✅ 已确认
- [ ] 文件选择对话框使用 Qt 标准对话框 ✅ 已确认
- [ ] 没有使用 `__file__` 获取资源路径（打包后会失效）

### 5. 版本信息
- [ ] 更新 `pyproject.toml` 中的版本号
- [ ] 更新 `README.md` 中的版本信息
- [ ] 考虑在 GUI 中添加"关于"对话框显示版本

## 🔧 打包步骤

### 步骤 1：准备环境
```bash
# 确保在干净的虚拟环境中
python -m venv venv_packaging
venv_packaging\Scripts\activate  # Windows
# 或
source venv_packaging/bin/activate  # Linux/macOS

# 安装所有依赖
pip install -r requirements.txt
pip install pyinstaller
```

### 步骤 2：测试应用
```bash
# 确保 GUI 能正常运行
python run_gui.py
```

### 步骤 3：执行打包
```bash
# 使用打包脚本（推荐）
python build_gui.py

# 或直接使用 PyInstaller
pyinstaller build_gui.spec
```

### 步骤 4：测试打包结果
- [ ] 在 `dist/` 目录中找到可执行文件
- [ ] 双击运行，检查是否能正常启动
- [ ] 测试主要功能：
  - [ ] 打开数据文件
  - [ ] 配置参数
  - [ ] 执行重构
  - [ ] 查看结果
  - [ ] 保存配置
- [ ] 检查日志文件是否正常生成
- [ ] 检查配置文件是否正常保存

### 步骤 5：清理测试
- [ ] 在另一台机器或虚拟机中测试（确保没有 Python 环境）
- [ ] 检查文件大小是否合理（通常 200-500MB）
- [ ] 检查启动时间（首次启动可能较慢）

## ⚠️ 常见问题

### 问题 1：打包后无法启动
**可能原因**：
- 缺少隐藏导入
- 路径问题

**解决方案**：
- 检查 `build_gui.spec` 中的 `hiddenimports`
- 使用 `--debug=all` 参数查看详细错误

### 问题 2：文件过大
**可能原因**：
- 包含了不必要的依赖
- 使用了单文件模式

**解决方案**：
- 检查 `excludes` 列表
- 考虑使用目录模式（`onefile=False`）

### 问题 3：启动慢
**可能原因**：
- 单文件模式需要解压
- 包含大量依赖

**解决方案**：
- 使用目录模式
- 或使用 Nuitka 编译

### 问题 4：杀毒软件误报
**可能原因**：
- PyInstaller 打包的文件可能被误报

**解决方案**：
- 代码签名（需要证书）
- 提交到杀毒软件厂商白名单
- 使用 Nuitka 编译

## 📝 打包后处理

### 1. 创建安装程序（可选）
- Windows: 使用 Inno Setup 或 NSIS
- macOS: 创建 .dmg 镜像
- Linux: 创建 AppImage 或 Snap

### 2. 准备分发
- [ ] 准备用户文档
- [ ] 准备系统要求说明
- [ ] 准备安装/使用指南
- [ ] 考虑创建 GitHub Release

### 3. 版本管理
- [ ] 创建 Git tag（如 `v1.0.0-gui-release`）
- [ ] 更新 CHANGELOG
- [ ] 在 GitHub 创建 Release 并上传可执行文件

## 🎯 推荐工作流

1. **开发阶段**：使用 `python run_gui.py` 直接运行
2. **测试阶段**：在开发环境中充分测试
3. **打包阶段**：使用 `build_gui.py` 打包
4. **验证阶段**：在干净环境中测试打包结果
5. **分发阶段**：创建安装程序或直接分发可执行文件

