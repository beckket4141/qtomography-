# MLE Reconstruction Usage Guide

_Last updated: 2025-10-07_

## 1. 模块概览
- `qtomography.domain.reconstruction.mle.MLEReconstructor` 实现最大似然估计 (MLE) 的密度矩阵重构，参考 MATLAB `reconstruct_density_matrix_nD_MLE.m`。
- 重构流程采用 Cholesky 参数化确保正定性，并调用 `DensityMatrix` 兜底保证物理约束。
- 主要对外接口：`reconstruct(probabilities, initial_density=None)` 与 `reconstruct_with_details(...)`。

## 2. Python 端示例
```python
import numpy as np
from qtomography.domain.reconstruction.mle import MLEReconstructor

# 测量概率向量，长度为 n²
probabilities = np.array([...], dtype=float)

mle = MLEReconstructor(dimension=4, tolerance=1e-9)
# 仅获取最终密度矩阵
density = mle.reconstruct(probabilities)

# 如需调试信息
details = mle.reconstruct_with_details(probabilities)
print("目标函数 chi²:", details.objective_value)
print("理论概率:", details.expected_probabilities)
```

可选参数：
- `optimizer`: 传递给 `scipy.optimize.minimize` 的算法，默认 `"L-BFGS-B"`。
- `regularization`: 岭正则系数，用于噪声较大的情况。
- `max_iterations`: 最大迭代次数，默认 2000。
- `initial_density`: 初始密度矩阵，可传 `DensityMatrix`、`ndarray`，或留空使用线性重构 / 恒等矩阵。

## 3. 与线性重构的配合
- `MLEReconstructor` 会自动尝试使用线性重构作为初始值（失败时退回到最大混合态）。
- 若已手动运行线性重构，可直接将 `density.matrix` 传给 `initial_density`，提升收敛速度与稳定性。
- `reconstruct_with_details` 会提供 `expected_probabilities`，方便与输入概率对比，检查拟合程度。

## 4. 内部参数化说明
- 使用下三角 Cholesky 因子 `T`，参数向量长度为 `n²`：
  * 对角元素使用 `exp` 确保正值；
  * 下三角非对角采用实部、虚部拆分；
  * 重构密度矩阵为 `rho = T T† / Tr(T T†)`。
- `encode_density_to_params` / `decode_params_to_density` 方法已公开，可独立测试或作为外部工具使用。

## 5. 测试与对齐
- 单元测试：`python/tests/unit/test_mle_reconstructor.py`，覆盖参数互逆、纯态重构、噪声场景等。
- 集成测试：`python/tests/integration/test_mle_reconstructor_integration.py`，验证在无噪声与含噪声情况下的表现。
- 如需与 MATLAB 对齐，可在 MATLAB 端复用 `linear_compare_excel.m` 的生成方式，然后建立对应的 pytest 或脚本做比对。

## 6. 调试建议
- 若优化器返回 `success=False`，可查看 `message`、`status`、`objective_value` 了解原因。
- 调整 `regularization`、`max_iterations`、初始密度矩阵等参数，可以显著影响收敛速度和稳定性。
- 建议保留 `details.expected_probabilities` 与原始概率比较，以判断拟合质量；必要时可使用保真度或迹距离进一步评估。

## 7. 后续扩展方向
- 支持权重 / 噪声模型（Poisson、Gaussian 等）
- 提供梯度 / 雅可比解析表达，加速高维 MLE
- 批量 MLE 重构接口，以及和线性重构的统一调度 `ReconstructionPipeline`
- 与 Bell 态分析模块联动，输出保真度、纯度等指标

当线性重构用于初始估计时，MLE 重构可以在噪声存在情况下进一步优化结果，是后续结果持久化、Bell 态分析等模块的关键基础之一。
