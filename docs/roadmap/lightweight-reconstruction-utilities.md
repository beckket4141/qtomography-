# 重构器工具函数与轻量化接口设计

_Last updated: 2025-10-07_  
_Status: ✅ 推荐方案_

## 📋 问题分析

### 当前状态
- ✅ `LinearReconstructor` 已完成
- ✅ `MLEReconstructor` 已完成
- 📋 HMLE、Mixed 等还未实现

### 为什么不需要 `BaseReconstructor` 抽象基类？

1. **两个重构器差异巨大**
   - 构造参数不同：`regularization` vs `optimizer/max_iterations`
   - 接口不同：`reconstruct(probs)` vs `reconstruct(probs, initial_density=...)`
   - 返回类型不同：简单 vs 详细结果对象

2. **公共代码极少**
   ```python
   # 实际共享的只有：
   - dimension/tolerance 校验（2行）
   - _normalize_probabilities（10行）
   - ProjectorSet 缓存（1行）
   ```
   为了13行代码引入抽象基类 → **过度设计**

3. **Python 鸭子类型已经够用**
   ```python
   # 不需要显式继承，只要有 reconstruct 方法就能用
   def process_batch(reconstructor, data):
       return [reconstructor.reconstruct(p) for p in data]
   ```

4. **过早抽象有害**
   - 未来重构器（HMLE/Mixed）还没实现，不知道真正的公共模式
   - 现在定义接口可能约束未来设计
   - **"先具体实现，后提取抽象"** 是正确的工程实践

---

## ✅ 推荐方案：轻量化工具 + Protocol

### 1. 提取共享工具函数

```python
# qtomography/domain/reconstruction/utils.py
"""重构器共享工具函数"""

import numpy as np


def normalize_probabilities(
    probabilities: np.ndarray,
    dimension: int,
    tolerance: float = 1e-10
) -> np.ndarray:
    """概率归一化（按前 n 个分量之和归一化）
    
    Args:
        probabilities: 原始测量概率
        dimension: 希尔伯特空间维度
        tolerance: 数值容差
        
    Returns:
        归一化后的概率向量
        
    Raises:
        ValueError: 概率向量长度不匹配或归一化因子过小
    """
    probs = np.asarray(probabilities, dtype=float).reshape(-1)
    expected_len = dimension ** 2
    
    if probs.size != expected_len:
        raise ValueError(
            f"概率向量长度应为 {expected_len}, 实际为 {probs.size}"
        )
    
    leading_sum = np.sum(probs[:dimension])
    if np.isclose(leading_sum, 0.0, atol=tolerance):
        raise ValueError("前 n 个分量之和过小, 无法安全归一化")
    
    return probs / leading_sum


def validate_dimension(dimension: int) -> None:
    """校验维度参数"""
    if not isinstance(dimension, int):
        raise TypeError(f"dimension 必须是整数，实际为 {type(dimension)}")
    if dimension < 2:
        raise ValueError(f"dimension 必须 >= 2，实际为 {dimension}")


def validate_tolerance(tolerance: float) -> None:
    """校验容差参数"""
    if not isinstance(tolerance, (int, float)):
        raise TypeError(f"tolerance 必须是数值，实际为 {type(tolerance)}")
    if tolerance <= 0:
        raise ValueError(f"tolerance 必须 > 0，实际为 {tolerance}")


__all__ = [
    "normalize_probabilities",
    "validate_dimension",
    "validate_tolerance",
]
```

### 2. 使用 Protocol 定义轻量化接口（可选）

```python
# qtomography/domain/reconstruction/protocol.py
"""重构器接口协议定义（鸭子类型约束）"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
import numpy as np
from qtomography.domain.density import DensityMatrix


@runtime_checkable
class ReconstructorProtocol(Protocol):
    """重构器接口协议（鸭子类型）
    
    任何实现了 reconstruct() 方法的类都满足此协议。
    不需要显式继承，用于类型提示和运行时检查。
    """
    
    dimension: int
    
    def reconstruct(
        self,
        probabilities: np.ndarray,
        **kwargs  # 允许子类有不同的额外参数
    ) -> DensityMatrix:
        """重构密度矩阵
        
        Args:
            probabilities: 测量概率向量
            **kwargs: 各重构器特定的参数
            
        Returns:
            重构后的密度矩阵
        """
        ...


__all__ = ["ReconstructorProtocol"]
```

### 3. 重构现有代码

#### 3.1 LinearReconstructor

```python
# qtomography/domain/reconstruction/linear.py
"""线性层析重构器"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet
from .utils import normalize_probabilities, validate_dimension, validate_tolerance


@dataclass
class LinearReconstructionResult:
    """线性重构结果"""
    density: DensityMatrix
    rho_matrix_raw: np.ndarray
    normalized_probabilities: np.ndarray
    residuals: np.ndarray
    rank: int
    singular_values: np.ndarray


class LinearReconstructor:
    """线性层析重构器"""
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        regularization: Optional[float] = None,
        cache_projectors: bool = True,
    ) -> None:
        # 使用共享工具函数校验
        validate_dimension(dimension)
        validate_tolerance(tolerance)
        
        if regularization is not None and regularization < 0:
            raise ValueError("regularization 必须为非负数")
        
        self.dimension = dimension
        self.tolerance = tolerance
        self.regularization = regularization
        self.projector_set = (
            ProjectorSet.get(dimension)
            if cache_projectors
            else ProjectorSet(dimension, cache=False)
        )
    
    def reconstruct(self, probabilities: np.ndarray) -> DensityMatrix:
        """重构密度矩阵（简化接口）"""
        result = self.reconstruct_with_details(probabilities)
        return result.density
    
    def reconstruct_with_details(
        self, probabilities: np.ndarray
    ) -> LinearReconstructionResult:
        """重构密度矩阵（详细接口）"""
        
        # 使用共享工具函数归一化
        probs = normalize_probabilities(
            probabilities, 
            self.dimension, 
            self.tolerance
        )
        
        # ... 其余实现保持不变 ...
```

#### 3.2 MLEReconstructor

```python
# qtomography/domain/reconstruction/mle.py
"""MLE 层析重构器"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet
from .utils import normalize_probabilities, validate_dimension, validate_tolerance


@dataclass
class MLEReconstructionResult:
    """MLE 重构结果"""
    density: DensityMatrix
    rho_matrix_raw: np.ndarray
    normalized_probabilities: np.ndarray
    expected_probabilities: np.ndarray
    objective_value: float
    success: bool
    status: int
    message: str
    n_iterations: int
    n_function_evaluations: int


class MLEReconstructor:
    """MLE 层析重构器"""
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        optimizer: str = "L-BFGS-B",
        regularization: Optional[float] = None,
        max_iterations: int = 2000,
        cache_projectors: bool = True,
    ) -> None:
        # 使用共享工具函数校验
        validate_dimension(dimension)
        validate_tolerance(tolerance)
        
        if regularization is not None and regularization < 0:
            raise ValueError("regularization 必须为非负数")
        if max_iterations <= 0:
            raise ValueError("max_iterations 必须为正整数")
        
        self.dimension = dimension
        self.tolerance = tolerance
        self.optimizer = optimizer
        self.regularization = regularization
        self.max_iterations = max_iterations
        self.projector_set = (
            ProjectorSet.get(dimension)
            if cache_projectors
            else ProjectorSet(dimension, cache=False)
        )
    
    def reconstruct(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> DensityMatrix:
        """重构密度矩阵（简化接口）"""
        result = self.reconstruct_with_details(probabilities, initial_density)
        return result.density
    
    def reconstruct_with_details(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> MLEReconstructionResult:
        """重构密度矩阵（详细接口）"""
        
        # 使用共享工具函数归一化
        probs = normalize_probabilities(
            probabilities,
            self.dimension,
            self.tolerance
        )
        
        # ... 其余实现保持不变 ...
```

### 4. 使用 Protocol 进行类型提示（可选）

```python
# 批处理函数可以使用 Protocol 类型提示
from qtomography.domain.reconstruction.protocol import ReconstructorProtocol

def process_batch(
    reconstructor: ReconstructorProtocol,
    probabilities_list: list[np.ndarray]
) -> list[DensityMatrix]:
    """批量处理，接受任何实现了 reconstruct 的重构器"""
    return [reconstructor.reconstruct(p) for p in probabilities_list]

# 使用
linear_recon = LinearReconstructor(4)
mle_recon = MLEReconstructor(4)

# 两者都满足 ReconstructorProtocol，无需显式继承
results1 = process_batch(linear_recon, data)
results2 = process_batch(mle_recon, data)
```

---

## 📊 方案对比

| 维度 | 抽象基类方案 | 轻量化工具 + Protocol |
|------|-------------|----------------------|
| **代码复用** | ✅ 基类包含共享逻辑 | ✅ 工具函数复用 |
| **类型安全** | ⚠️ `**kwargs` 损失类型信息 | ✅ 各类独立类型清晰 |
| **灵活性** | ❌ 子类受基类约束 | ✅ 完全自由设计 |
| **迁移成本** | ❌ 需修改所有现有代码 | ✅ 仅提取函数即可 |
| **维护成本** | ❌ 基类接口变更影响所有子类 | ✅ 各类独立维护 |
| **扩展性** | ⚠️ 新重构器可能不适合基类 | ✅ 新重构器完全自由 |
| **Python风格** | ⚠️ Java风格的OOP | ✅ Pythonic 鸭子类型 |
| **代码量** | ❌ +200行（基类+迁移+测试） | ✅ +50行（工具函数） |

---

## 🎯 推荐策略

### 立即执行（本周）

1. ✅ **创建 `utils.py`**
   - 提取 `normalize_probabilities`
   - 提取 `validate_dimension`、`validate_tolerance`

2. ✅ **重构现有代码**
   - 替换 `LinearReconstructor._normalize_probabilities` 为工具函数
   - 替换 `MLEReconstructor._normalize_probabilities` 为工具函数

3. ✅ **添加单元测试**
   - `tests/unit/test_reconstruction_utils.py`

### 可选（如需类型提示）

4. 🟡 **创建 `protocol.py`**
   - 定义 `ReconstructorProtocol`
   - 用于类型提示，不强制继承

### 未来观察（P2）

5. 📋 **等 HMLE/Mixed 实现后再评估**
   - 观察是否有真正稳定的公共模式
   - 如果3+个重构器都有**相同的流程步骤**，再考虑抽象
   - 此时再引入抽象基类也不迟

---

## 📝 实施步骤

### Step 1: 创建工具函数

```bash
# 创建文件
touch qtomography/domain/reconstruction/utils.py

# 编写工具函数（见上面代码）
```

### Step 2: 修改现有重构器

```python
# 在 linear.py 和 mle.py 中
from .utils import normalize_probabilities, validate_dimension, validate_tolerance

# 替换原有的内部方法调用
probs = normalize_probabilities(probabilities, self.dimension, self.tolerance)
```

### Step 3: 添加测试

```python
# tests/unit/test_reconstruction_utils.py
import numpy as np
import pytest
from qtomography.domain.reconstruction.utils import (
    normalize_probabilities,
    validate_dimension,
    validate_tolerance
)

def test_normalize_probabilities():
    probs = np.array([0.5, 0.5, 0.25, 0.25])
    normalized = normalize_probabilities(probs, dimension=2)
    assert np.allclose(normalized, [1.0, 1.0, 0.5, 0.5])

def test_validate_dimension():
    validate_dimension(2)  # OK
    with pytest.raises(ValueError):
        validate_dimension(1)  # Too small
    with pytest.raises(TypeError):
        validate_dimension(2.5)  # Not int

def test_validate_tolerance():
    validate_tolerance(1e-10)  # OK
    with pytest.raises(ValueError):
        validate_tolerance(-1e-10)  # Negative
```

### Step 4: 更新导出

```python
# qtomography/domain/reconstruction/__init__.py
"""重构相关模块"""

from .linear import LinearReconstructor, LinearReconstructionResult
from .mle import MLEReconstructor, MLEReconstructionResult
from .utils import normalize_probabilities  # 导出工具函数

__all__ = [
    "LinearReconstructor",
    "LinearReconstructionResult",
    "MLEReconstructor",
    "MLEReconstructionResult",
    "normalize_probabilities",
]
```

---

## 🎓 设计原则

### YAGNI (You Aren't Gonna Need It)
> "不要为未来可能需要的功能过度设计"

- ✅ 当前只有2个重构器，鸭子类型足够
- ❌ 不要为"可能"出现的3-5个重构器提前设计抽象

### KISS (Keep It Simple, Stupid)
> "简单是最高级的复杂"

- ✅ 工具函数：13行代码解决问题
- ❌ 抽象基类：200+行代码引入复杂度

### Rule of Three
> "第三次重复时才考虑抽象"

- 🟡 当前：2个重构器，观察中
- 📋 未来：3个重构器落地后再决定

---

## ✅ 结论

**不建议现在添加 `BaseReconstructor` 抽象基类**，理由：

1. ✅ 当前两个重构器差异太大，强行统一得不偿失
2. ✅ Python 鸭子类型天然支持多态，无需显式继承
3. ✅ 公共代码极少（13行），工具函数足以复用
4. ✅ 过早抽象会约束未来设计
5. ✅ 遵循 YAGNI、KISS、Rule of Three 原则

**推荐方案**：
- ✅ 提取共享工具函数（`utils.py`）
- 🟡 可选使用 Protocol 进行类型提示
- 📋 等未来有3+个重构器且公共模式稳定后再评估

**这是更 Pythonic、更务实的工程决策！** 👍

---

**状态**：✅ 推荐方案，立即可实施  
**优先级**：P1（短期优化）  
**预计工作量**：2-3小时

