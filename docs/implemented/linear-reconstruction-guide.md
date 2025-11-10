# Linear Reconstruction Usage Guide

_Last updated: 2025-10-06_

## 1. 模块概览
- `qtomography.domain.reconstruction.linear.LinearReconstructor` 负责将测量概率向量映射为密度矩阵，算法对应 MATLAB 的 `reconstruct_density_matrix_nD.m`。
- `LinearReconstructionResult` 提供重构的调试信息（归一化概率、残差、奇异值等）。
- `ProjectorSet` 生成并缓存测量矩阵 `M`，保证两端对齐。

## 2. Python 端用法示例
```python
import numpy as np
from qtomography.domain.reconstruction.linear import LinearReconstructor

# 测量数据：长度 n² 的概率或功率向量
dimension = 4
probabilities = np.array([...], dtype=float)

reconstructor = LinearReconstructor(dimension, tolerance=1e-9)
density = reconstructor.reconstruct(probabilities)          # 仅获取物理化后的密度矩阵
result = reconstructor.reconstruct_with_details(probabilities)  # 同时拿到残差、奇异值等

print("重构后的密度矩阵:\n", density.matrix)
```
常见参数：
- `tolerance`：传递给 `DensityMatrix` 的容差，默认 1e-10。
- `regularization`：可选的岭回归系数；当测量噪声较大或矩阵病态时，可设置为正数。

## 3. MATLAB 数据准备
为了对齐 MATLAB 与 Python 结果，提供脚本 `matlab/linear_compare_excel.m`：
1. 将所有 `.m` 文件放在 `QT_to_Python_1/matlab/`（已整理）。
2. 在 MATLAB 中运行：
   ```matlab
   cd('QT_to_Python_1/matlab');
   linear_compare_excel;
   ```
3. 脚本会读取 `4维bell.xlsx` 和 `16维bell15913.xlsx`，逐列调用 `reconstruct_density_matrix_nD`，输出 `rho_matlab_alignment_dim4.mat` 与 `rho_matlab_alignment_dim16.mat`。
4. 每个 `.mat` 存有 `results{col}`（对应 Excel 第 `col` 列）和 `dimension`。

## 4. Python 对齐分析脚本
若需快速查看单个文件的差异，可运行 `python/liner_compare_mat.py`：
```
PYTHONPATH=python python python/liner_compare_mat.py
```
该脚本读取 `01.csv` 与 `rho_MATLAB_liner.mat`，输出 Frobenius 范数、保真度、特征值等指标。

## 5. Pytest 自动化对齐
### 单独运行 Excel 对齐测试
执行：
```
python python/run_excel_alignment_tests.py
```
脚本会设置 `PYTHONPATH` 并调用 `pytest python/tests/integration/test_linear_reconstruction_excel.py -v`，对 4 维与 16 维 Excel 的所有列逐一比对。

测试逻辑：
- 读取 Excel，通过 `LinearReconstructor` 生成 Python 密度矩阵。
- 载入 MATLAB 对齐后的 `rho_matlab_alignment_dim*.mat`。
- 计算 Frobenius 范数差（4 维容差 2e-2，16 维容差 5e-2）。
- 若差异超出容差，则报告失败。

### 整套测试
依旧可运行：
```
python python/run_tests.py
```
该脚本会依次执行单元测试、性能测试、MATLAB 对照测试等，并在 `python/test_results/` 生成报告。

## 6. Excel 数据格式说明
- `n` 维系统的 Excel 文件行数须为 `n²`，每列表示一个测量态的概率/功率向量。
- 若使用新的 Excel 文件，请保证列顺序与 MATLAB 的 `generate_projectors_and_operators.m` 一致，否则需重新同步测量矩阵。
- MATLAB 脚本会自动将列向量转置为行向量，以匹配 `reconstruct_density_matrix_nD` 的输入。

## 7. 容差与调试建议
- 对齐测试使用的容差考虑了浮点误差与测量噪声，可根据实际数据质量调整。
- 如需更严格比较，可在测试或脚本中附加保真度、迹距离、特征值差等指标。
- 若 `numpy.linalg.lstsq` 返回空残差数组，说明方程组完全可解；若残差较大，可检查输入归一化或考虑启用 `regularization`。

## 8. 常用文件与入口
| 文件 | 作用 |
| --- | --- |
| `python/qtomography/domain/reconstruction/linear.py` | 线性重构核心实现 |
| `matlab/linear_compare_excel.m` | MATLAB 批量对齐并保存 `.mat` |
| `python/liner_compare_mat.py` | 单个案例的对齐分析脚本 |
| `python/run_excel_alignment_tests.py` | 一键执行 Excel 对齐测试 |
| `python/tests/integration/test_linear_reconstruction_excel.py` | 4 维、16 维 Excel → MATLAB 对齐的 pytest 用例 |

完成以上流程后，即可确认 Python 重构链路与 MATLAB 在多个维度、多个态上的输出一致，是后续 MLE 重构或更复杂算法的可靠基线。
