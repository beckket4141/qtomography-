# 安装指南

> **最后更新**: 2025年11月  
> **项目版本**: v0.7.0  
> **Python 版本要求**: >= 3.9

---

## 📋 目录

- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [开发模式安装](#开发模式安装)
- [可选依赖](#可选依赖)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 🖥️ 系统要求

### 操作系统

- ✅ Windows 10/11
- ✅ Linux (Ubuntu 20.04+, CentOS 7+)
- ✅ macOS 10.15+

### Python 版本

- **最低版本**: Python 3.9
- **推荐版本**: Python 3.10 或更高
- **已测试版本**: Python 3.9, 3.10, 3.11, 3.12, 3.13

### 系统依赖

- **pip**: >= 21.0（推荐使用最新版本）
- **setuptools**: >= 65.0（用于构建包）

---

## 🚀 快速安装

### 方法 1：从源代码安装（推荐）

```bash
# 1. 克隆或下载项目
cd QT_to_Python_1/python

# 2. 安装核心依赖
pip install -r requirements.txt

# 3. 以开发模式安装包
pip install -e .
```

### 方法 2：从 wheel 包安装

```bash
# 如果已有构建好的 wheel 包
pip install dist/qtomography-0.7.0-py3-none-any.whl
```

### 方法 3：从源代码构建安装

```bash
# 构建包
python -m build

# 安装构建的包
pip install dist/qtomography-0.7.0.tar.gz
```

---

## 💻 开发模式安装

开发模式安装允许在修改源代码后立即生效，无需重新安装。

```bash
# 进入项目目录
cd QT_to_Python_1/python

# 开发模式安装（包含核心依赖）
pip install -e .

# 安装开发依赖（测试、格式化、类型检查等）
pip install -e ".[dev]"
```

### 开发模式的优势

- ✅ 修改源代码后立即生效
- ✅ 无需重新安装即可测试更改
- ✅ 保留源代码目录结构
- ✅ 便于调试和开发

---

## 📦 可选依赖

项目支持可选依赖分组，可以根据需要安装。

### 开发工具 (dev)

```bash
pip install -e ".[dev]"
```

**包含**:
- `pytest>=8.0.0` - 测试框架
- `pytest-cov>=4.1.0` - 覆盖率工具
- `pytest-json-report>=1.5.0` - JSON 测试报告
- `black>=24.4.0` - 代码格式化
- `flake8>=6.1.0` - 代码检查
- `mypy>=1.8.0` - 类型检查
- `pre-commit>=3.5.0` - Git 钩子

### 性能优化 (performance)

```bash
pip install -e ".[performance]"
```

**包含**:
- `numba>=0.57.0` - JIT 编译加速

### 高级量子模拟 (quantum)

```bash
pip install -e ".[quantum]"
```

**包含**:
- `qutip>=4.7.0` - 量子工具包

### GUI 支持 (gui)

```bash
pip install -e ".[gui]"
```

**包含**:
- `PySide6>=6.7.0` - Qt GUI 框架

### 安装所有可选依赖

```bash
pip install -e ".[dev,performance,quantum,gui]"
```

---

## ✅ 验证安装

### 1. 检查包是否安装成功

```bash
# 检查包版本
python -c "import qtomography; print('qtomography 安装成功')"

# 或使用 CLI 命令
qtomography --help
```

### 2. 检查核心依赖

```bash
python -c "import numpy, scipy, pandas, matplotlib; print('所有核心依赖安装成功')"
```

### 3. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v
```

### 4. 检查 CLI 工具

```bash
# 查看 CLI 帮助
qtomography --help

# 查看版本信息
qtomography info

# 测试重构命令
qtomography reconstruct --help
```

---

## 🔧 虚拟环境安装（推荐）

### 使用 venv（Python 内置）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装项目
pip install -e .

# 退出虚拟环境
deactivate
```

### 使用 conda

```bash
# 创建 conda 环境
conda create -n qtomography python=3.10

# 激活环境
conda activate qtomography

# 安装项目
pip install -e .

# 退出环境
conda deactivate
```

---

## 🐛 常见问题

### Q1: 安装失败，提示 "No module named 'setuptools'"

**解决方案**:
```bash
pip install --upgrade setuptools wheel
```

### Q2: 安装失败，提示权限错误

**解决方案**:
```bash
# 使用用户安装（推荐）
pip install --user -e .

# 或使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -e .
```

### Q3: 找不到 qtomography 命令

**解决方案**:
```bash
# 确保已安装
pip install -e .

# 检查 Python 路径
python -c "import sys; print(sys.executable)"

# 检查 pip 安装路径
pip show qtomography
```

### Q4: 导入错误 "ModuleNotFoundError: No module named 'qtomography'"

**解决方案**:
```bash
# 确保在正确的目录
cd QT_to_Python_1/python

# 重新安装
pip install -e .

# 检查 Python 路径
python -c "import sys; print('\n'.join(sys.path))"
```

### Q5: 依赖版本冲突

**解决方案**:
```bash
# 升级 pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -e . --force-reinstall
```

### Q6: Windows 上安装 PySide6 失败

**解决方案**:
```bash
# 确保有 Visual C++ 运行时
# 下载并安装: https://aka.ms/vs/17/release/vc_redist.x64.exe

# 或使用预编译的 wheel
pip install PySide6 --only-binary :all:
```

---

## 📊 安装后目录结构

安装成功后，项目结构如下：

```
QT_to_Python_1/python/
├── qtomography/          # 核心包（已安装）
├── tests/                # 测试代码
├── examples/             # 示例代码
├── scripts/              # 工具脚本
├── docs/                 # 文档
├── pyproject.toml        # 项目配置
├── requirements.txt      # 依赖列表
└── README.md            # 项目说明
```

---

## 🔄 更新安装

### 更新到最新版本

```bash
# 拉取最新代码
git pull

# 重新安装
pip install -e . --upgrade
```

### 更新依赖

```bash
# 更新所有依赖到最新兼容版本
pip install -r requirements.txt --upgrade

# 更新开发依赖
pip install -e ".[dev]" --upgrade
```

---

## 🧪 测试安装

### 快速测试

```bash
# 运行快速测试
python -c "
from qtomography.domain import LinearReconstructor, DensityMatrix
import numpy as np

# 测试基本功能
reconstructor = LinearReconstructor(dimension=2)
probs = np.array([0.5, 0.5, 0.25, 0.25])
density = reconstructor.reconstruct(probs)

print(f'✅ 安装成功！')
print(f'   纯度: {density.purity:.4f}')
print(f'   迹: {density.trace:.4f}')
"
```

### 完整测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=qtomography --cov-report=html
```

---

## 📚 相关文档

- [环境配置指南](../../环境配置.txt) - 根目录的环境配置说明
- [README.md](../../README.md) - 项目主文档
- [CLI使用指南](../implemented/cli-usage-guide.md) - 命令行工具使用说明
- [开发指南](development-guide.md) - 开发环境设置（如果存在）

---

**最后更新**: 2025年11月  
**维护者**: 项目维护团队

