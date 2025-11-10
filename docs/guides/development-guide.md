# 开发指南

> **最后更新**: 2025年11月  
> **项目版本**: v0.7.0

---

## 📋 目录

- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [提交规范](#提交规范)
- [调试技巧](#调试技巧)
- [性能分析](#性能分析)

---

## 🛠️ 开发环境设置

### 1. 克隆项目

```bash
# 克隆仓库
git clone <repository-url>
cd QT_to_Python_1/python
```

### 2. 创建虚拟环境

```bash
# 使用 venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate      # Windows

# 或使用 conda
conda create -n qtomography python=3.10
conda activate qtomography
```

### 3. 安装开发依赖

```bash
# 安装核心依赖和开发工具
pip install -e ".[dev]"
```

### 4. 配置开发工具

```bash
# 安装 pre-commit 钩子（可选）
pre-commit install

# 配置 IDE（推荐使用 VS Code 或 PyCharm）
# VS Code: 安装 Python 扩展
# PyCharm: 配置项目解释器为虚拟环境
```

---

## 📝 代码规范

### Python 代码风格

项目遵循 **PEP 8** 代码风格规范。

#### 使用 Black 格式化

```bash
# 格式化所有代码
black qtomography/ tests/

# 检查格式（不修改）
black --check qtomography/ tests/
```

#### 使用 Flake8 检查

```bash
# 检查代码风格
flake8 qtomography/ tests/

# 忽略特定错误
flake8 qtomography/ --ignore=E501,W503
```

### 类型注解

项目使用类型注解提高代码可读性。

```python
from typing import Optional, List, Tuple
import numpy as np

def reconstruct(
    probabilities: np.ndarray,
    dimension: int,
    tolerance: Optional[float] = None
) -> DensityMatrix:
    """重构量子态
    
    参数:
        probabilities: 测量概率向量
        dimension: 量子系统维度
        tolerance: 数值容差（可选）
    
    返回:
        重构的密度矩阵
    """
    ...
```

#### 使用 mypy 检查类型

```bash
# 类型检查
mypy qtomography/

# 忽略缺失导入
mypy qtomography/ --ignore-missing-imports
```

### 文档字符串

使用 **Google 风格**的文档字符串。

```python
def reconstruct(probabilities: np.ndarray) -> DensityMatrix:
    """重构量子态密度矩阵。
    
    从测量概率数据重构量子态，确保满足物理约束。
    
    参数:
        probabilities: 测量概率向量，形状为 (d²,)
            d 为量子系统维度
    
    返回:
        重构的密度矩阵对象
    
    异常:
        ValueError: 如果概率向量维度不正确
        RuntimeError: 如果重构失败
    
    示例:
        >>> probs = np.array([0.5, 0.5, 0.25, 0.25])
        >>> reconstructor = LinearReconstructor(dimension=2)
        >>> density = reconstructor.reconstruct(probs)
        >>> print(f"纯度: {density.purity:.4f}")
    """
    ...
```

---

## 🧪 测试指南

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/unit/test_density.py -v

# 运行特定测试函数
pytest tests/unit/test_density.py::test_purity -v

# 运行标记的测试
pytest tests/ -m "not slow" -v
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest tests/ --cov=qtomography --cov-report=html

# 查看覆盖率报告
# 打开 htmlcov/index.html
```

### 编写测试

#### 单元测试示例

```python
import pytest
import numpy as np
from qtomography.domain import DensityMatrix

def test_density_matrix_purity():
    """测试纯态的纯度 = 1"""
    # 纯态：|0⟩⟨0|
    pure_state = np.array([[1, 0], [0, 0]], dtype=complex)
    density = DensityMatrix(pure_state)
    
    assert np.isclose(density.purity, 1.0)

def test_density_matrix_trace():
    """测试密度矩阵的迹 = 1"""
    mixed_state = np.array([[0.7, 0], [0, 0.3]], dtype=complex)
    density = DensityMatrix(mixed_state)
    
    assert np.isclose(density.trace, 1.0)

@pytest.mark.parametrize("dimension", [2, 4, 8])
def test_reconstructor_dimensions(dimension):
    """测试不同维度的重构器"""
    from qtomography.domain import LinearReconstructor
    
    reconstructor = LinearReconstructor(dimension=dimension)
    assert reconstructor.dimension == dimension
```

#### 集成测试示例

```python
import pytest
import numpy as np
from qtomography.app import ReconstructionController

def test_batch_reconstruction():
    """测试批处理重构"""
    controller = ReconstructionController()
    
    # 准备测试数据
    probabilities = np.array([
        [0.5, 0.5, 0.25, 0.25],
        [0.6, 0.4, 0.3, 0.2]
    ])
    
    # 执行批处理
    results = controller.run_batch(
        probabilities,
        dimension=2,
        methods=["linear", "wls"]
    )
    
    assert len(results) == 4  # 2个样本 × 2种方法
    assert all(r.density.trace == pytest.approx(1.0) for r in results)
```

---

## 📤 提交规范

### Git 提交消息格式

使用 **Conventional Commits** 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 类型 (type)

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

#### 示例

```bash
# 新功能
git commit -m "feat(domain): 添加 MLE 重构算法"

# 修复 bug
git commit -m "fix(density): 修复特征值裁剪的数值稳定性问题"

# 文档更新
git commit -m "docs(readme): 更新安装说明"

# 重构
git commit -m "refactor(controller): 重构批处理逻辑"

# 测试
git commit -m "test(domain): 添加密度矩阵单元测试"
```

### 分支命名

- `feature/xxx` - 新功能
- `fix/xxx` - 修复 bug
- `docs/xxx` - 文档更新
- `refactor/xxx` - 重构

---

## 🐛 调试技巧

### 使用调试器

#### VS Code

1. 设置断点
2. 按 `F5` 启动调试
3. 使用调试控制台查看变量

#### PyCharm

1. 设置断点
2. 右键选择 "Debug"
3. 使用调试工具窗口

#### 命令行调试

```bash
# 使用 pdb
python -m pdb script.py

# 在代码中添加断点
import pdb; pdb.set_trace()
```

### 日志调试

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 使用日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 性能分析

```python
import cProfile
import pstats

# 性能分析
profiler = cProfile.Profile()
profiler.enable()

# 执行代码
your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # 打印前10个最耗时的函数
```

---

## ⚡ 性能分析

### 使用 cProfile

```bash
# 分析脚本性能
python -m cProfile -o profile.stats script.py

# 查看分析结果
python -m pstats profile.stats
```

### 使用 line_profiler

```bash
# 安装
pip install line_profiler

# 分析函数
kernprof -l -v script.py
```

### 内存分析

```bash
# 安装
pip install memory_profiler

# 分析内存使用
python -m memory_profiler script.py
```

---

## 🔍 代码审查清单

提交代码前检查：

- [ ] 代码通过所有测试
- [ ] 代码通过 Black 格式化
- [ ] 代码通过 Flake8 检查
- [ ] 代码通过 mypy 类型检查（如果配置）
- [ ] 添加了必要的文档字符串
- [ ] 更新了相关文档
- [ ] 提交消息符合规范

---

## 📚 相关资源

- [PEP 8 风格指南](https://pep8.org/)
- [Google Python 风格指南](https://google.github.io/styleguide/pyguide.html)
- [pytest 文档](https://docs.pytest.org/)
- [Black 文档](https://black.readthedocs.io/)
- [mypy 文档](https://mypy.readthedocs.io/)

---

**最后更新**: 2025年11月  
**维护者**: 项目维护团队

