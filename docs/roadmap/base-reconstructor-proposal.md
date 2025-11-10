# BaseReconstructor 抽象基类设计建议

_Last updated: 2025-10-07_
_Status: 📋 设计提案_

非常好的问题！让我基于您的长期规划给出建议：

## 🎯 **建议：应该添加 BaseReconstructor 抽象基类**

### ✅ **理由分析**

#### 1. **您的未来需求**
```python
# 您计划添加的重构器
- LinearReconstructor (已完成)
- MLEReconstructor (已完成)
- HMLEReconstructor (计划中 - Hybrid MLE)
- MixedReconstructor (计划中 - 混合重构)
- AdaptiveReconstructor (可能 - 自适应重构)
```

当有**3种以上重构策略**时，抽象基类的价值就体现出来了。

#### 2. **设计模式最佳实践**
```python
# 策略模式标准实现
BaseReconstructor (抽象基类)
    ├── LinearReconstructor
    ├── MLEReconstructor
    ├── HMLEReconstructor (Hybrid MLE)
    └── MixedReconstructor
```

这是**策略模式**的经典实现，符合：
- **开闭原则**（OCP）：对扩展开放，对修改关闭
- **里氏替换原则**（LSP）：子类可以替换基类
- **依赖倒置原则**（DIP）：依赖抽象而非具体

#### 3. **实际代码优势**
```python
# 统一的接口约定
def process_batch(reconstructor: BaseReconstructor, probabilities_list):
    """可以接受任何重构器"""
    results = []
    for probs in probabilities_list:
        density = reconstructor.reconstruct(probs)
        results.append(density)
    return results

# 使用时可以灵活切换
reconstructor = LinearReconstructor(4)  # 或 MLEReconstructor(4)
results = process_batch(reconstructor, data)
```

### 🏗️ **推荐的设计方案**

#### **方案1：完整的抽象基类（推荐）**

```python
# qtomography/domain/reconstruction/base.py
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet


class BaseReconstructor(ABC):
    """量子态重构器抽象基类
    
    定义所有重构器必须实现的接口，支持策略模式。
    """
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        cache_projectors: bool = True,
    ):
        """
        Args:
            dimension: 希尔伯特空间维度
            tolerance: 数值容差
            cache_projectors: 是否缓存投影算符
        """
        if dimension < 2:
            raise ValueError("维度必须大于等于 2")
        if tolerance <= 0:
            raise ValueError("tolerance 必须为正数")
        
        self.dimension = dimension
        self.tolerance = tolerance
        self.projector_set = (
            ProjectorSet.get(dimension)
            if cache_projectors
            else ProjectorSet(dimension, cache=False)
        )
    
    @abstractmethod
    def reconstruct(
        self,
        probabilities: np.ndarray,
        **kwargs
    ) -> DensityMatrix:
        """重构密度矩阵（简化接口）
        
        Args:
            probabilities: 测量概率向量
            **kwargs: 各重构器特定的额外参数
            
        Returns:
            重构后的密度矩阵
        """
        pass
    
    @abstractmethod
    def reconstruct_with_details(
        self,
        probabilities: np.ndarray,
        **kwargs
    ):
        """重构密度矩阵（详细接口）
        
        Args:
            probabilities: 测量概率向量
            **kwargs: 各重构器特定的额外参数
            
        Returns:
            包含详细信息的重构结果对象
        """
        pass
    
    def _normalize_probabilities(self, probabilities: np.ndarray) -> np.ndarray:
        """概率归一化（所有重构器共享的逻辑）"""
        probs = np.asarray(probabilities, dtype=float).reshape(-1)
        expected_len = self.dimension ** 2
        if probs.size != expected_len:
            raise ValueError(
                f"概率向量长度应为 {expected_len}, 实际为 {probs.size}"
            )
        
        leading_sum = np.sum(probs[: self.dimension])
        if np.isclose(leading_sum, 0.0, atol=self.tolerance):
            raise ValueError("前 n 个分量之和过小, 无法安全归一化")
        
        return probs / leading_sum
    
    @property
    @abstractmethod
    def method_name(self) -> str:
        """返回重构方法名称（用于日志和报告）"""
        pass
```

#### **修改现有的重构器**

```python
# qtomography/domain/reconstruction/linear.py
from .base import BaseReconstructor

class LinearReconstructor(BaseReconstructor):
    """线性层析重构器"""
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        regularization: Optional[float] = None,
        cache_projectors: bool = True,
    ):
        super().__init__(dimension, tolerance=tolerance, cache_projectors=cache_projectors)
        if regularization is not None and regularization < 0:
            raise ValueError("regularization 必须为非负数")
        self.regularization = regularization
    
    @property
    def method_name(self) -> str:
        return "linear"
    
    def reconstruct(self, probabilities: np.ndarray) -> DensityMatrix:
        """实现抽象方法"""
        result = self.reconstruct_with_details(probabilities)
        return result.density
    
    def reconstruct_with_details(
        self, probabilities: np.ndarray
    ) -> LinearReconstructionResult:
        """实现抽象方法"""
        # ... 现有实现保持不变
```

```python
# qtomography/domain/reconstruction/mle.py
from .base import BaseReconstructor

class MLEReconstructor(BaseReconstructor):
    """MLE层析重构器"""
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        optimizer: str = "L-BFGS-B",
        regularization: Optional[float] = None,
        max_iterations: int = 2000,
        cache_projectors: bool = True,
    ):
        super().__init__(dimension, tolerance=tolerance, cache_projectors=cache_projectors)
        if regularization is not None and regularization < 0:
            raise ValueError("regularization 必须为非负数")
        if max_iterations <= 0:
            raise ValueError("max_iterations 必须为正整数")
        
        self.optimizer = optimizer
        self.regularization = regularization
        self.max_iterations = max_iterations
    
    @property
    def method_name(self) -> str:
        return "mle"
    
    def reconstruct(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> DensityMatrix:
        """实现抽象方法"""
        result = self.reconstruct_with_details(probabilities, initial_density=initial_density)
        return result.density
    
    def reconstruct_with_details(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> MLEReconstructionResult:
        """实现抽象方法"""
        # ... 现有实现保持不变
```

#### **未来扩展示例**

```python
# qtomography/domain/reconstruction/hmle.py
from .base import BaseReconstructor

class HMLEReconstructor(BaseReconstructor):
    """混合最大似然重构器（Hybrid MLE）
    
    结合线性重构的速度和MLE的精度
    """
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        threshold: float = 0.01,  # 噪声阈值
        cache_projectors: bool = True,
    ):
        super().__init__(dimension, tolerance=tolerance, cache_projectors=cache_projectors)
        self.threshold = threshold
        self.linear = LinearReconstructor(dimension, tolerance=tolerance)
        self.mle = MLEReconstructor(dimension, tolerance=tolerance)
    
    @property
    def method_name(self) -> str:
        return "hmle"
    
    def reconstruct(self, probabilities: np.ndarray) -> DensityMatrix:
        # 先用线性重构
        linear_result = self.linear.reconstruct_with_details(probabilities)
        
        # 判断是否需要MLE精修
        if self._needs_refinement(linear_result):
            return self.mle.reconstruct(probabilities, initial_density=linear_result.density)
        return linear_result.density
    
    def reconstruct_with_details(self, probabilities: np.ndarray):
        # 实现详细版本
        pass
    
    def _needs_refinement(self, linear_result) -> bool:
        """判断是否需要MLE精修"""
        return linear_result.residuals.size > 0 and \
               np.linalg.norm(linear_result.residuals) > self.threshold
```

### 📊 **方案对比**

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **不使用基类** | 简单直接 | 扩展困难，代码重复 | 只有1-2种重构器 |
| **使用抽象基类** | 扩展容易，类型安全 | 初期稍复杂 | ≥3种重构器（您的情况）|
| **Protocol类型** | 灵活，鸭子类型 | 缺少代码复用 | Python 3.8+类型检查 |

### 🎯 **我的建议**

**强烈建议添加 BaseReconstructor 抽象基类**，理由：

1. ✅ **您已计划添加多种重构器**（HMLE、混合重构）
2. ✅ **提供代码复用**：`_normalize_probabilities` 等共享逻辑
3. ✅ **统一接口**：便于批处理、Pipeline 等高级功能
4. ✅ **类型安全**：`BaseReconstructor` 作为类型注解
5. ✅ **符合设计模式**：策略模式的标准实现
6. ✅ **便于测试**：可以写通用的测试基类

### 🚀 **实施建议**

1. **现在就添加**：重构成本小，收益大
2. **保持兼容**：现有代码仅需继承基类，无需修改逻辑
3. **渐进优化**：先迁移共享逻辑到基类，后续再添加新重构器

**这是一个正确的架构决策！** 👍

## 1. 背景与动机

### 1.1 当前状态
- ✅ 已完成 `LinearReconstructor`
- ✅ 已完成 `MLEReconstructor`
- 📋 计划添加 `HMLEReconstructor`（混合最大似然）
- 📋 计划添加 `MixedReconstructor`（混合重构）
- 📋 可能添加 `AdaptiveReconstructor`（自适应重构）

### 1.2 问题分析
当前两个重构器虽然遵循相同的接口约定，但没有继承关系：
- ❌ 代码重复：`_normalize_probabilities` 等逻辑重复实现
- ❌ 类型不统一：无法使用统一的类型注解
- ❌ 扩展困难：添加新重构器需要重新实现共享逻辑
- ❌ 测试冗余：无法编写通用的测试基类

### 1.3 设计目标
引入 `BaseReconstructor` 抽象基类，实现：
- ✅ **代码复用**：共享逻辑下沉到基类
- ✅ **统一接口**：明确的契约定义
- ✅ **类型安全**：统一的类型注解
- ✅ **易于扩展**：新重构器仅需实现核心逻辑
- ✅ **符合设计模式**：策略模式的标准实现

## 2. 设计方案

### 2.1 抽象基类设计

```python
# qtomography/domain/reconstruction/base.py
"""重构器抽象基类，定义统一接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet


class BaseReconstructor(ABC):
    """量子态重构器抽象基类
    
    定义所有重构器必须实现的接口，支持策略模式。
    
    设计原则：
    - 抽象方法：reconstruct()、reconstruct_with_details()、method_name
    - 共享逻辑：_normalize_probabilities()、基础初始化
    - 模板方法：可选的钩子方法供子类扩展
    """
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        cache_projectors: bool = True,
    ) -> None:
        """
        初始化重构器基础参数
        
        Args:
            dimension: 希尔伯特空间维度 n
            tolerance: 数值容差
            cache_projectors: 是否缓存投影算符
            
        Raises:
            ValueError: 参数不合法时抛出
        """
        if dimension < 2:
            raise ValueError("维度必须大于等于 2")
        if tolerance <= 0:
            raise ValueError("tolerance 必须为正数")
        
        self.dimension = dimension
        self.tolerance = tolerance
        self.projector_set = (
            ProjectorSet.get(dimension)
            if cache_projectors
            else ProjectorSet(dimension, cache=False)
        )
    
    @abstractmethod
    def reconstruct(
        self,
        probabilities: np.ndarray,
        **kwargs
    ) -> DensityMatrix:
        """重构密度矩阵（简化接口）
        
        Args:
            probabilities: 测量概率向量，长度为 dimension²
            **kwargs: 各重构器特定的额外参数
                - initial_density: 初始密度矩阵（MLE使用）
                - regularization: 正则化参数（可选）
            
        Returns:
            重构后的物理密度矩阵
            
        Raises:
            ValueError: 输入概率向量不合法时抛出
        """
        pass
    
    @abstractmethod
    def reconstruct_with_details(
        self,
        probabilities: np.ndarray,
        **kwargs
    ):
        """重构密度矩阵（详细接口）
        
        Args:
            probabilities: 测量概率向量
            **kwargs: 各重构器特定的额外参数
            
        Returns:
            包含详细信息的重构结果对象
            - LinearReconstructionResult（线性重构）
            - MLEReconstructionResult（MLE重构）
            - 其他子类定义的结果对象
            
        Raises:
            ValueError: 输入不合法时抛出
        """
        pass
    
    @property
    @abstractmethod
    def method_name(self) -> str:
        """返回重构方法名称
        
        用于日志记录、结果标注等场景。
        
        Returns:
            方法名称字符串，如 "linear"、"mle"、"hmle"
        """
        pass
    
    # ------------------------------------------------------------------
    # 共享逻辑方法
    # ------------------------------------------------------------------
    
    def _normalize_probabilities(self, probabilities: np.ndarray) -> np.ndarray:
        """概率归一化（所有重构器共享的逻辑）
        
        按照 MATLAB 流程，使用前 n 个分量之和进行归一化。
        
        Args:
            probabilities: 原始测量概率
            
        Returns:
            归一化后的概率向量
            
        Raises:
            ValueError: 概率向量长度不匹配或归一化因子过小
        """
        probs = np.asarray(probabilities, dtype=float).reshape(-1)
        expected_len = self.dimension ** 2
        if probs.size != expected_len:
            raise ValueError(
                f"概率向量长度应为 {expected_len}, 实际为 {probs.size}"
            )
        
        leading_sum = np.sum(probs[: self.dimension])
        if np.isclose(leading_sum, 0.0, atol=self.tolerance):
            raise ValueError("前 n 个分量之和过小, 无法安全归一化")
        
        return probs / leading_sum
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(dimension={self.dimension}, method={self.method_name})"
    
    def __repr__(self) -> str:
        """详细表示"""
        return (f"{self.__class__.__name__}(\n"
                f"  dimension={self.dimension},\n"
                f"  tolerance={self.tolerance},\n"
                f"  method={self.method_name}\n"
                f")")


__all__ = ["BaseReconstructor"]
```

### 2.2 LinearReconstructor 迁移

```python
# qtomography/domain/reconstruction/linear.py
"""线性层析重构器，实现 MATLAB `reconstruct_density_matrix_nD.m` 的 Python 对应版本。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from qtomography.domain.density import DensityMatrix
from .base import BaseReconstructor


@dataclass
class LinearReconstructionResult:
    """线性重构运行产生的完整结果。"""
    
    density: DensityMatrix
    rho_matrix_raw: np.ndarray
    normalized_probabilities: np.ndarray
    residuals: np.ndarray
    rank: int
    singular_values: np.ndarray


class LinearReconstructor(BaseReconstructor):
    """线性层析重构器。
    
    使用最小二乘法求解线性方程组，可选择岭回归正则化。
    """
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        regularization: Optional[float] = None,
        cache_projectors: bool = True,
    ) -> None:
        super().__init__(dimension, tolerance=tolerance, cache_projectors=cache_projectors)
        
        if regularization is not None and regularization < 0:
            raise ValueError("regularization 必须为非负数")
        
        self.regularization = regularization
    
    @property
    def method_name(self) -> str:
        """返回方法名称"""
        return "linear"
    
    def reconstruct(self, probabilities: np.ndarray) -> DensityMatrix:
        """实现抽象方法：重构密度矩阵（简化接口）"""
        result = self.reconstruct_with_details(probabilities)
        return result.density
    
    def reconstruct_with_details(
        self, probabilities: np.ndarray
    ) -> LinearReconstructionResult:
        """实现抽象方法：重构密度矩阵（详细接口）"""
        
        # 使用基类的归一化方法
        probs = self._normalize_probabilities(probabilities)
        measurement_matrix = self.projector_set.measurement_matrix
        
        # ... 其余实现保持不变 ...
```

### 2.3 MLEReconstructor 迁移

```python
# qtomography/domain/reconstruction/mle.py
"""最大似然 (MLE) 层析重构实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.optimize import minimize
from scipy.linalg import cholesky

from qtomography.domain.density import DensityMatrix
from .base import BaseReconstructor


@dataclass
class MLEReconstructionResult:
    """MLE重构的完整输出。"""
    
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


class MLEReconstructor(BaseReconstructor):
    """最大似然估计层析重构器。
    
    使用 Cholesky 参数化 + L-BFGS-B 优化器。
    """
    
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
        super().__init__(dimension, tolerance=tolerance, cache_projectors=cache_projectors)
        
        if regularization is not None and regularization < 0:
            raise ValueError("regularization 必须为非负数")
        if max_iterations <= 0:
            raise ValueError("max_iterations 必须为正整数")
        
        self.optimizer = optimizer
        self.regularization = regularization
        self.max_iterations = max_iterations
    
    @property
    def method_name(self) -> str:
        """返回方法名称"""
        return "mle"
    
    def reconstruct(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> DensityMatrix:
        """实现抽象方法：重构密度矩阵（简化接口）"""
        result = self.reconstruct_with_details(probabilities, initial_density=initial_density)
        return result.density
    
    def reconstruct_with_details(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> MLEReconstructionResult:
        """实现抽象方法：重构密度矩阵（详细接口）"""
        
        # 使用基类的归一化方法
        probs_normalized = self._normalize_probabilities(probabilities)
        
        # ... 其余实现保持不变 ...
```

### 2.4 未来扩展示例：HMLEReconstructor

```python
# qtomography/domain/reconstruction/hmle.py
"""混合最大似然重构器（Hybrid MLE）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from qtomography.domain.density import DensityMatrix
from .base import BaseReconstructor
from .linear import LinearReconstructor, LinearReconstructionResult
from .mle import MLEReconstructor, MLEReconstructionResult


@dataclass
class HMLEReconstructionResult:
    """HMLE重构的完整输出。"""
    
    density: DensityMatrix
    linear_result: LinearReconstructionResult
    mle_result: Optional[MLEReconstructionResult]
    used_mle: bool
    refinement_reason: str


class HMLEReconstructor(BaseReconstructor):
    """混合最大似然重构器
    
    策略：
    1. 先使用线性重构快速求解
    2. 根据残差判断是否需要 MLE 精修
    3. 如需精修，使用线性结果作为 MLE 初值
    """
    
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        residual_threshold: float = 0.01,
        cache_projectors: bool = True,
    ) -> None:
        super().__init__(dimension, tolerance=tolerance, cache_projectors=cache_projectors)
        
        self.residual_threshold = residual_threshold
        self.linear = LinearReconstructor(
            dimension, 
            tolerance=tolerance,
            cache_projectors=cache_projectors
        )
        self.mle = MLEReconstructor(
            dimension,
            tolerance=tolerance,
            cache_projectors=cache_projectors
        )
    
    @property
    def method_name(self) -> str:
        """返回方法名称"""
        return "hmle"
    
    def reconstruct(self, probabilities: np.ndarray) -> DensityMatrix:
        """实现抽象方法：重构密度矩阵（简化接口）"""
        result = self.reconstruct_with_details(probabilities)
        return result.density
    
    def reconstruct_with_details(
        self, probabilities: np.ndarray
    ) -> HMLEReconstructionResult:
        """实现抽象方法：重构密度矩阵（详细接口）"""
        
        # 第一步：线性重构
        linear_result = self.linear.reconstruct_with_details(probabilities)
        
        # 第二步：判断是否需要 MLE 精修
        needs_refinement, reason = self._needs_refinement(linear_result)
        
        if needs_refinement:
            # 使用线性结果作为初值，进行 MLE 优化
            mle_result = self.mle.reconstruct_with_details(
                probabilities,
                initial_density=linear_result.density
            )
            return HMLEReconstructionResult(
                density=mle_result.density,
                linear_result=linear_result,
                mle_result=mle_result,
                used_mle=True,
                refinement_reason=reason
            )
        else:
            return HMLEReconstructionResult(
                density=linear_result.density,
                linear_result=linear_result,
                mle_result=None,
                used_mle=False,
                refinement_reason="residual below threshold"
            )
    
    def _needs_refinement(self, linear_result: LinearReconstructionResult) -> tuple[bool, str]:
        """判断是否需要 MLE 精修
        
        Returns:
            (needs_refinement, reason)
        """
        if linear_result.residuals.size == 0:
            return False, "no residuals"
        
        residual_norm = np.linalg.norm(linear_result.residuals)
        if residual_norm > self.residual_threshold:
            return True, f"residual_norm={residual_norm:.6f} > threshold={self.residual_threshold}"
        
        return False, f"residual_norm={residual_norm:.6f} acceptable"


__all__ = ["HMLEReconstructor", "HMLEReconstructionResult"]
```

## 3. 使用示例

### 3.1 统一接口使用

```python
from qtomography.domain.reconstruction import BaseReconstructor, LinearReconstructor, MLEReconstructor

def process_batch(
    reconstructor: BaseReconstructor,
    probabilities_list: list[np.ndarray]
) -> list[DensityMatrix]:
    """批量处理，可接受任何重构器"""
    results = []
    for probs in probabilities_list:
        density = reconstructor.reconstruct(probs)
        results.append(density)
    return results

# 使用时可以灵活切换
reconstructor = LinearReconstructor(4)  # 或 MLEReconstructor(4)
results = process_batch(reconstructor, data)
```

### 3.2 策略选择

```python
def get_reconstructor(
    method: str,
    dimension: int,
    **kwargs
) -> BaseReconstructor:
    """工厂方法：根据方法名创建重构器"""
    if method == "linear":
        return LinearReconstructor(dimension, **kwargs)
    elif method == "mle":
        return MLEReconstructor(dimension, **kwargs)
    elif method == "hmle":
        return HMLEReconstructor(dimension, **kwargs)
    else:
        raise ValueError(f"未知的重构方法: {method}")

# 使用
reconstructor = get_reconstructor("hmle", dimension=4)
density = reconstructor.reconstruct(probabilities)
```

### 3.3 类型注解

```python
from typing import List
from qtomography.domain.reconstruction import BaseReconstructor

def compare_methods(
    reconstructors: List[BaseReconstructor],
    probabilities: np.ndarray
) -> dict[str, DensityMatrix]:
    """对比多种重构方法"""
    results = {}
    for recon in reconstructors:
        density = recon.reconstruct(probabilities)
        results[recon.method_name] = density
    return results

# 使用
reconstructors = [
    LinearReconstructor(4),
    MLEReconstructor(4),
    HMLEReconstructor(4)
]
comparison = compare_methods(reconstructors, probabilities)
```

## 4. 测试策略

### 4.1 基类测试

```python
# tests/unit/test_base_reconstructor.py
import pytest
from qtomography.domain.reconstruction.base import BaseReconstructor

class DummyReconstructor(BaseReconstructor):
    """测试用的虚拟重构器"""
    
    @property
    def method_name(self):
        return "dummy"
    
    def reconstruct(self, probabilities, **kwargs):
        # 简单实现
        pass
    
    def reconstruct_with_details(self, probabilities, **kwargs):
        # 简单实现
        pass

def test_base_initialization():
    recon = DummyReconstructor(4)
    assert recon.dimension == 4
    assert recon.tolerance == 1e-10

def test_normalize_probabilities():
    recon = DummyReconstructor(2)
    probs = np.array([0.5, 0.5, 0.25, 0.25])
    normalized = recon._normalize_probabilities(probs)
    assert np.allclose(normalized, [1.0, 1.0, 0.5, 0.5])
```

### 4.2 通用接口测试

```python
# tests/unit/test_reconstructor_interface.py
import pytest
from qtomography.domain.reconstruction import LinearReconstructor, MLEReconstructor

@pytest.fixture(params=[LinearReconstructor, MLEReconstructor])
def reconstructor(request):
    """参数化fixture：测试所有重构器"""
    return request.param(dimension=2)

def test_reconstruct_interface(reconstructor):
    """测试所有重构器的统一接口"""
    probs = np.array([0.5, 0.5, 0.25, 0.25])
    density = reconstructor.reconstruct(probs)
    
    assert density.dimension == 2
    assert density.is_physical()
    assert np.isclose(density.trace, 1.0)

def test_method_name(reconstructor):
    """测试方法名称属性"""
    assert isinstance(reconstructor.method_name, str)
    assert len(reconstructor.method_name) > 0
```

## 5. 实施步骤

### 5.1 阶段1：创建基类（P0）
1. 创建 `base.py` 文件
2. 实现 `BaseReconstructor` 抽象基类
3. 编写基类单元测试

### 5.2 阶段2：迁移现有重构器（P0）
1. 修改 `LinearReconstructor` 继承基类
2. 修改 `MLEReconstructor` 继承基类
3. 移除重复的 `_normalize_probabilities` 实现
4. 更新单元测试

### 5.3 阶段3：更新导出和文档（P0）
1. 更新 `__init__.py` 导出 `BaseReconstructor`
2. 更新 UML 图
3. 更新使用文档

### 5.4 阶段4：添加新重构器（P1）
1. 实现 `HMLEReconstructor`
2. 实现 `MixedReconstructor`
3. 编写对应测试

## 6. 优势总结

### 6.1 设计模式优势
- ✅ **策略模式**：符合 OOP 设计原则
- ✅ **开闭原则**：对扩展开放，对修改关闭
- ✅ **里氏替换**：子类可以替换基类
- ✅ **依赖倒置**：依赖抽象而非具体

### 6.2 工程优势
- ✅ **代码复用**：共享逻辑统一管理
- ✅ **类型安全**：统一的类型注解
- ✅ **易于扩展**：新重构器实现成本低
- ✅ **测试友好**：通用测试覆盖所有实现

### 6.3 维护优势
- ✅ **接口明确**：抽象方法定义清晰
- ✅ **文档集中**：基类文档说明设计理念
- ✅ **重构安全**：接口变更影响明确

## 7. 风险与对策

### 7.1 潜在风险
- ⚠️ **迁移成本**：现有代码需要修改
- ⚠️ **复杂度增加**：多一层抽象

### 7.2 对策
- ✅ **渐进迁移**：先迁移共享逻辑，保持兼容
- ✅ **充分测试**：确保迁移前后行为一致
- ✅ **文档完善**：清晰说明设计理念

## 8. 结论

**强烈建议实施此方案**，理由：

1. ✅ 您已计划添加多种重构器（HMLE、混合重构）
2. ✅ 当前两种重构器已有共享逻辑
3. ✅ 抽象基类是标准的 OOP 实践
4. ✅ 迁移成本低，收益大
5. ✅ 为未来扩展奠定良好基础

**建议立即实施，采用渐进式迁移策略。**

---

**状态：设计提案完成，待审批实施。**

