# 测试数据说明

这个目录包含用于测试DensityMatrix类的测试数据。

## 文件结构

- `density_matrices/` - 已知的密度矩阵数据
- `measurement_data/` - 测量数据
- `expected_results/` - 期望结果

## 数据格式

- `.npy` - NumPy数组文件
- `.mat` - MATLAB数据文件
- `.json` - JSON格式数据

## 使用方式

```python
import numpy as np
from qtomography.tests.fixtures.test_data import load_test_matrix

# 加载测试矩阵
matrix = load_test_matrix("2d_pure_state.npy")
rho = DensityMatrix(matrix)
```
