# DensityMatrix 重构使用指南

## 概述

DensityMatrix 类经过重构，现在支持三种物理化策略，实现了职责分离和问题透明化。

## 核心概念

### 物理化策略

1. **`within_tol`**（默认）：容差内物理化
   - 处理数值稳定性问题
   - 对显著非物理输入发出警告
   - 适合大多数使用场景

2. **`project`**：强制物理投影
   - 将所有非物理输入投影到物理空间
   - 确保输出始终是物理的
   - 适合最终交付场景

3. **`none`**：不处理
   - 保持原始输入不变
   - 用于调试和问题诊断
   - 风险自担

## 使用示例

### 基本使用

```python
import numpy as np
from qtomography.domain.density import DensityMatrix

# 创建密度矩阵（默认策略）
matrix = np.array([[0.6, 0.3], [0.3, 0.4]], dtype=complex)
dm = DensityMatrix(matrix)
print(f"是否物理: {dm.is_physical()}")
print(f"特征值: {dm.eigenvalues}")
```

### 强制物理投影

```python
# 处理非物理输入
non_physical_matrix = np.array([[0.8, 0.5], [0.5, -0.3]], dtype=complex)

# 强制投影到物理空间
dm_physical = DensityMatrix(non_physical_matrix, enforce="project")
print(f"投影后是否物理: {dm_physical.is_physical()}")
print(f"投影后特征值: {dm_physical.eigenvalues}")
```

### 调试模式

```python
# 调试模式：保持原始输入
dm_debug = DensityMatrix(non_physical_matrix, enforce="none")
print(f"原始特征值: {dm_debug.eigenvalues}")
print(f"是否物理: {dm_debug.is_physical()}")  # 可能为 False
```

### 诊断信息

```python
# 获取详细的物理性诊断
diagnostics = dm.physical_diagnostics()
print("诊断信息:")
for key, value in diagnostics.items():
    print(f"  {key}: {value}")
```

### 强制投影工具

```python
# 使用类方法进行强制投影
projected_matrix = DensityMatrix.project_to_physical(non_physical_matrix)
print(f"投影后矩阵:\n{projected_matrix}")

# 带诊断信息的投影
projected_matrix, diag = DensityMatrix.project_to_physical(
    non_physical_matrix, return_diag=True
)
print(f"诊断信息: {diag}")
```

## 重构器集成

### LinearReconstructor

```python
from qtomography.domain.reconstruction.linear import LinearReconstructor

# 使用不同的物理化策略
reconstructor = LinearReconstructor(
    dimension=2,
    density_enforce="project",  # 强制物理投影
    density_warn=True,
    density_strict=False
)

result = reconstructor.reconstruct_with_details(probabilities)
print(f"重构结果是否物理: {result.density.is_physical()}")
```

### MLEReconstructor

```python
from qtomography.domain.reconstruction.mle import MLEReconstructor

# MLE 通常产生物理结果，但可以强制保证
reconstructor = MLEReconstructor(
    dimension=2,
    density_enforce="project",  # 强制物理投影
    density_warn=True,
    density_strict=False
)

result = reconstructor.reconstruct_with_details(probabilities)
print(f"MLE 结果是否物理: {result.density.is_physical()}")
```

## 最佳实践

### 1. 选择适当的策略

- **开发阶段**：使用 `within_tol`，通过警告发现问题
- **生产环境**：使用 `project`，确保输出物理性
- **调试问题**：使用 `none`，查看原始输入

### 2. 处理警告

```python
import warnings

# 捕获警告
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    dm = DensityMatrix(non_physical_matrix, enforce="within_tol")
    
    if w:
        print(f"收到警告: {w[0].message}")
        # 根据警告决定是否使用强制投影
        dm = DensityMatrix(non_physical_matrix, enforce="project")
```

### 3. 严格模式

```python
# 严格模式：对显著非物理输入抛出异常
try:
    dm = DensityMatrix(non_physical_matrix, enforce="within_tol", strict=True)
except ValueError as e:
    print(f"检测到非物理输入: {e}")
    # 使用强制投影
    dm = DensityMatrix(non_physical_matrix, enforce="project")
```

### 4. 批量处理

```python
def process_matrices(matrices, enforce="within_tol"):
    """批量处理矩阵"""
    results = []
    for matrix in matrices:
        try:
            dm = DensityMatrix(matrix, enforce=enforce, strict=True)
            results.append(dm)
        except ValueError:
            # 非物理输入，使用强制投影
            dm = DensityMatrix(matrix, enforce="project")
            results.append(dm)
    return results
```

## 迁移指南

### 从旧版本迁移

旧代码无需修改，默认行为保持不变：

```python
# 旧代码（仍然有效）
dm = DensityMatrix(matrix, tolerance=1e-10)

# 等价于新代码
dm = DensityMatrix(matrix, tolerance=1e-10, enforce="within_tol")
```

### 逐步迁移

1. **第一阶段**：保持现有代码不变
2. **第二阶段**：在新功能中使用新参数
3. **第三阶段**：根据需要调整现有代码的策略

## 常见问题

### Q: 什么时候使用 `project` 策略？

A: 当需要确保输出始终是物理的时，比如：
- 最终交付给用户的结果
- 需要物理性保证的后续计算
- 处理已知可能非物理的输入

### Q: 警告信息太多怎么办？

A: 可以：
- 设置 `warn=False` 关闭警告
- 使用 `strict=True` 将警告转为异常
- 使用 `project` 策略避免警告

### Q: 如何判断输入是否可能非物理？

A: 使用诊断工具：

```python
dm = DensityMatrix(matrix, enforce="none")
diag = dm.physical_diagnostics()
if not diag["is_physical_within_tol"]:
    print("输入可能非物理，建议使用 project 策略")
```

## 总结

DensityMatrix 重构提供了：
- **清晰的职责分离**：数值稳定性 vs 物理投影
- **问题透明性**：不掩盖外部算法问题
- **灵活的配置**：三种策略可选
- **完善的诊断**：详细的物理性指标
- **向后兼容**：现有代码无需修改

选择合适的策略，让系统既稳定又透明！
