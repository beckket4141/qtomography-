# .gitignore 配置指南

> **最后更新**: 2025年11月  
> **项目版本**: v0.7.0

---

## 📋 概述

`.gitignore` 文件是 Git 版本控制系统中用来指定哪些文件和文件夹应该被忽略（不纳入版本控制）的配置文件。

## 🎯 .gitignore 的作用

1. **排除不需要版本控制的文件**：比如临时文件、编译产物、IDE配置文件等
2. **保护敏感信息**：避免将密码、API密钥等敏感文件提交到代码仓库
3. **减少仓库大小**：避免提交大文件或不必要的文件
4. **保持仓库整洁**：只跟踪源代码和必要的配置文件

---

## 📝 当前项目的 .gitignore 配置

项目当前使用的 `.gitignore` 文件位于：`QT_to_Python_1/python/.gitignore`

### 完整配置说明

```gitignore
# ============================================
# Python 相关
# ============================================
__pycache__/          # Python 字节码缓存目录
*.py[cod]             # 编译的 Python 文件（.pyc, .pyo, .pyd）
*$py.class            # Python 类文件
*.so                   # 共享库文件
.Python                # Python 环境标识
build/                 # 构建目录
develop-eggs/          # 开发环境相关
dist/                  # 分发包目录（包含 .whl 和 .tar.gz）
downloads/             # 下载目录
eggs/                  # Python eggs
.eggs/                 # Python eggs 缓存
lib/                   # 库目录
lib64/                 # 64位库目录
parts/                 # 部分构建文件
sdist/                 # 源码分发目录
var/                   # 变量目录
wheels/                # wheel 包目录
*.egg-info/            # Python 包元数据
.installed.cfg         # 安装配置
*.egg                  # Python egg 文件
MANIFEST               # 清单文件

# ============================================
# 虚拟环境
# ============================================
venv/                  # 虚拟环境目录
env/                   # 环境目录
ENV/                   # 环境目录（大写）
env.bak/               # 环境备份
venv.bak/              # 虚拟环境备份
.venv/                 # 虚拟环境目录（隐藏）
.env/                  # 环境变量文件

# ============================================
# Conda 环境
# ============================================
.conda/                # Conda 配置目录
conda-meta/            # Conda 元数据
pkgs/                  # Conda 包目录
envs/                  # Conda 环境目录
.conda-build/          # Conda 构建目录

# ============================================
# IDE 配置文件
# ============================================
.vscode/               # Visual Studio Code 配置
.idea/                 # PyCharm/IntelliJ IDEA 配置
*.swp                  # Vim 交换文件
*.swo                  # Vim 交换文件
*~                     # 备份文件
.DS_Store              # macOS 系统文件
Thumbs.db              # Windows 缩略图数据库

# ============================================
# Jupyter Notebook
# ============================================
.ipynb_checkpoints/    # Jupyter 检查点
*.ipynb                # Jupyter Notebook 文件（如果不需要版本控制）

# ============================================
# pytest 测试框架
# ============================================
.pytest_cache/         # pytest 缓存目录
.coverage              # 覆盖率数据文件
htmlcov/               # HTML 覆盖率报告
.tox/                  # tox 测试环境
.nox/                  # nox 测试环境

# ============================================
# 科学计算相关
# ============================================
*.mat                  # MATLAB 数据文件
*.npy                  # NumPy 数组文件
*.npz                  # NumPy 压缩数组文件
*.h5                   # HDF5 数据文件
*.hdf5                 # HDF5 数据文件

# ============================================
# 测试输出
# ============================================
test_outputs/          # 测试输出目录
test_results/          # 测试结果目录
*.log                  # 日志文件
*.out                  # 输出文件

# ============================================
# 项目特定
# ============================================
results/               # 结果输出目录
outputs/               # 输出目录
temp/                  # 临时目录
*.png                  # PNG 图片文件
*.jpg                  # JPEG 图片文件
*.pdf                  # PDF 文档
*.svg                  # SVG 矢量图
results_demo/records/*.json  # 演示结果 JSON 文件

# ============================================
# 操作系统相关
# ============================================
.DS_Store              # macOS 系统文件
.DS_Store?             # macOS 系统文件（变体）
._*                   # macOS 资源分支
.Spotlight-V100        # macOS Spotlight 索引
.Trashes               # macOS 废纸篓
ehthumbs.db            # Windows 缩略图数据库
Thumbs.db              # Windows 缩略图数据库

# ============================================
# 临时文件
# ============================================
*.tmp                  # 临时文件
*.temp                 # 临时文件
*.bak                  # 备份文件
*.backup               # 备份文件

# ============================================
# 配置文件（可能包含敏感信息）
# ============================================
config.ini             # 配置文件
secrets.json           # 密钥文件
.env.local             # 本地环境变量
.env.production        # 生产环境变量

# ============================================
# 文档生成
# ============================================
docs/_build/           # Sphinx 文档构建目录
site/                  # 静态网站生成目录
demo_output/           # 演示输出目录

# ============================================
# 测试输出目录（配置文件功能测试）
# ============================================
test_default_mode/     # 默认模式测试输出
test_config_mode/      # 配置模式测试输出
test_quick_config/     # 快速配置测试输出
test_override_mode/    # 覆盖模式测试输出
```

---

## 🔍 配置说明

### 为什么忽略这些文件？

#### 1. Python 编译文件

- `__pycache__/`、`*.pyc`：Python 自动生成的字节码，不需要版本控制
- `*.egg-info/`：包安装信息，会在安装时自动生成

#### 2. 构建产物

- `build/`、`dist/`：构建和分发目录，可以从源代码重新生成
- `*.egg`、`*.whl`：打包文件，可以从源代码重新构建

#### 3. 测试和覆盖率

- `.pytest_cache/`：pytest 缓存，提高测试速度
- `.coverage`、`htmlcov/`：覆盖率数据，可以重新生成

#### 4. 项目输出

- `demo_output/`：演示输出目录，包含大量结果文件
- `test_*_mode/`：测试输出目录，包含临时测试结果
- `*.png`、`*.jpg`、`*.pdf`：生成的图片和文档，可以从代码重新生成

#### 5. 敏感信息

- `config.ini`、`secrets.json`：可能包含 API 密钥、数据库密码等敏感信息
- `.env.*`：环境变量文件，可能包含敏感配置

---

## 📚 常见场景

### 场景 1：需要提交测试数据

如果某些测试数据需要版本控制，可以：

```gitignore
# 忽略所有 .mat 文件
*.mat

# 但保留特定的测试数据
!tests/fixtures/test_data.mat
```

### 场景 2：需要提交示例图片

如果某些示例图片需要版本控制：

```gitignore
# 忽略所有图片
*.png
*.jpg

# 但保留示例图片
!examples/images/*.png
!docs/images/*.png
```

### 场景 3：需要提交日志

如果某些日志需要版本控制：

```gitignore
# 忽略所有日志
*.log

# 但保留重要日志
!logs/important.log
```

---

## ⚠️ 注意事项

### 1. 已跟踪的文件

如果文件已经被 Git 跟踪，即使添加到 `.gitignore` 也不会自动忽略。需要先移除：

```bash
# 移除已跟踪的文件（但保留本地文件）
git rm --cached <file>

# 移除已跟踪的目录（但保留本地目录）
git rm -r --cached <directory>
```

### 2. 敏感信息已提交

如果敏感信息已经提交到仓库：

1. **立即更改密钥/密码**
2. **从 Git 历史中移除**（需要重写历史，谨慎操作）
3. **使用 `git filter-branch` 或 `git filter-repo` 工具**

### 3. 团队协作

确保团队成员都使用相同的 `.gitignore` 配置，避免提交不必要的文件。

---

## 🔧 验证 .gitignore 配置

### 检查哪些文件会被忽略

```bash
# 查看被忽略的文件
git status --ignored

# 查看详细的忽略信息
git check-ignore -v <file>
```

### 测试特定文件是否被忽略

```bash
# 测试文件是否会被忽略
git check-ignore -v path/to/file

# 如果输出为空，说明文件不会被忽略
# 如果输出规则，说明文件会被忽略
```

---

## 📖 相关资源

- [Git 官方文档 - gitignore](https://git-scm.com/docs/gitignore)
- [GitHub .gitignore 模板](https://github.com/github/gitignore)
- [Python .gitignore 最佳实践](https://github.com/github/gitignore/blob/main/Python.gitignore)

---

## 🎯 项目特定说明

### 当前项目忽略的文件类型

1. **测试输出**：`test_*_mode/`、`test_results/` - 测试生成的临时文件
2. **演示输出**：`demo_output/` - 演示脚本生成的输出
3. **构建产物**：`dist/`、`*.egg-info/` - 可以从源代码重新生成
4. **覆盖率报告**：`htmlcov/`、`.coverage` - 可以重新生成
5. **日志文件**：`*.log`、`logs/` - 运行时生成的日志

### 需要版本控制的文件

以下文件**应该**被版本控制：

- ✅ 源代码（`qtomography/`、`tests/`、`scripts/`）
- ✅ 配置文件（`pyproject.toml`、`requirements.txt`）
- ✅ 文档（`docs/`、`README.md`）
- ✅ 示例代码（`examples/`）
- ✅ 测试代码（`tests/`）

---

**最后更新**: 2025年11月  
**维护者**: 项目维护团队
