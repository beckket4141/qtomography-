# Density 模块第二阶段问题与改良（归档）

> **状态**：已归档。此文列举的 pytest 失败与修复需求已落实；请参考 docs/implemented/density-module-overview.md 和测试目录中的最新断言。

# 2. Density 模块问题与改良

## 一、测试结论快照
- **测试时间**：2025-09-24 17:06:20（Windows / Python 3.13.3 / pytest 8.4.2）
- **失败用例**：4 项（单元 3 项、集成 1 项）
- **受影响功能面**：`DensityMatrix` 构造参数校验、物理化流程的正半定投影、实/虚部便捷接口

| 失败用例 | 日志摘要 | 影响范围 |
| --- | --- | --- |
| `tests/unit/test_density.py::TestDensityMatrixCreation::test_invalid_input_types` | `ValueError: complex() arg is a malformed string` | 构造函数参数校验路径 |
| `tests/unit/test_density.py::TestPhysicalConstraints::test_ensure_physical_method` | `rho.eigenvalues` 返回 `-4.33680869e-19` | `_make_physical_matrix` 的谱裁剪与归一化 |
| `tests/unit/test_density.py::TestConvenienceFunctions::test_make_physical_function` | 同上 | `make_physical` 复用核心逻辑，外部接口同样受影响 |
| `tests/integration/test_matlab_comparison.py::TestMATLABComparison::test_matrix_operations_comparison` | `imag_part` 与 `np.imag(complex_matrix)` 不一致 | `get_imag_part` 暴露的矩阵与 MATLAB 参考实现差异 |

## 二、失败项逐条分析

### 1. 无效输入类型未抛出期望异常
- **现象**：向构造函数传入字符串 `"not a matrix"` 时，测试期望 `TypeError`，但当前实现先执行 `np.array(matrix, dtype=complex)`，NumPy 在尝试把字符串转换为复数时直接抛出 `ValueError`，导致断言失败。【F:qtomography/domain/density.py†L36-L55】
- **根因**：类型检查发生在数组化之后（`_validate_input`），无法捕获非数组类型带来的异常；同类问题也会出现在标量（例如 `42`）输入上。
- **改良建议**：
  1. 在调用 `np.array` 之前先做显式类型守卫，例如 `if isinstance(matrix, (str, bytes)) or np.isscalar(matrix): raise TypeError(...)`；
  2. 或者将 `np.array` 包装在 `try/except` 中，把来自 NumPy 的 `TypeError` / `ValueError` 统一转换为业务层的 `TypeError`，从而与单元测试期望保持一致。
  3. 若仍需支持列表、嵌套 Python 原生序列，可先尝试 `np.asarray(matrix)`，失败时再抛业务异常，确保错误消息清晰。

### 2. 物理化后仍残留数值级负特征值
- **现象**：`ensure_physical()` 与 `make_physical()` 在处理非物理输入（例如对角元素大于 1 的 2×2 矩阵）后，`rho.eigenvalues` 返回 `[1.0, -4.33680869e-19]`。虽然该值已非常接近 0，但单元测试要求所有特征值严格非负，因此断言失败。
- **根因**：
  - `_make_physical_matrix` 已对谱做 `np.clip(eigenvals, 0.0, None)` 处理，并在重构后再次做 Hermitian 化和归一化；
  - 但最终返回矩阵再经过一次 `eigvalsh` 时，浮点舍入产生 `-4.33680869e-19` 级别的残余负值；
  - `eigenvalues` 属性直接返回 `np.sort(eigenvals)[::-1]`，没有再按容差截断，使得数值噪声暴露给调用者。【F:qtomography/domain/density.py†L100-L115】【F:qtomography/domain/density.py†L142-L175】
- **改良建议**：
  1. 在 `eigenvalues` 属性中按实例级容差做一次后处理：`eigenvals = np.clip(eigenvals, 0.0, None)` 或 `eigenvals[eigenvals < self.tolerance] = 0.0`；
  2. 或者在 `_make_physical_matrix` 返回前增加一次光谱投影，例如对重构后的密度矩阵再次执行 `eigh` 并裁剪；
  3. 将上述逻辑同步到 `make_physical` 便捷函数，保证独立调用时也能获得严格正半定的输出；
  4. 补充回归测试：针对 `-1e-12` 量级的特征值断言 `>= 0`，确保修复长期有效。

### 3. 实/虚部接口与 MATLAB 参考实现不一致
- **现象**：集成测试比较 `DensityMatrix` 与 MATLAB 版本的矩阵操作时，`get_imag_part()` 返回的矩阵对角元素为 0，而预期结果保留输入矩阵中的 `±0.1`。日志显示 Python 端输出 `[[0., -0.3], [0.3, 0.]]`，与 `np.imag(complex_matrix)` 的 `[[0.1, -0.3], [0.3, -0.1]]` 存在明显偏差。
- **根因**：
  - `_make_physical_matrix` 为确保 Hermitian 性，使用 `(matrix + matrix.conj().T) / 2` 平均化输入，这一步会把对角线的虚部强制消除；
  - MATLAB `makephysical.m` 同样执行 `real(diag(diag(rho)))`，因此两个实现的物理结果理论上应一致；
  - 集成测试却直接拿原始输入 `complex_matrix` 与 `get_imag_part()` 比较，导致对角线虚部不匹配。
- **改良建议**：
  1. 若期望接口暴露“物理化后的矩阵”，应调整测试基准，改为与 `rho_complex.matrix` 的虚部比较（单元测试已经这么做）；
  2. 如果业务需要同时保留“原始矩阵”与“物理矩阵”的视图，可在构造函数中缓存原始输入（例如 `self._raw_matrix`），并为 `get_imag_part(raw=False)` 提供开关；
  3. 对外文档需明确说明：`DensityMatrix` 在初始化时会投影到物理态，返回的实部/虚部/幅值均针对投影后的矩阵，以免调用方产生歧义；
  4. 一旦测试基准确定，应在 MATLAB 对比脚本中同步修改，避免再次出现“原始值 vs. 物理值”的混用。

## 三、综合改良路线
1. **输入校验前置**：在 `_validate_input` 之前做好类型守卫，将 NumPy 抛出的底层异常翻译为语义化的业务异常。
2. **谱裁剪一致化**：把容差裁剪从 `_make_physical_matrix` 延伸到所有读取谱的接口，保证任意场景下的特征值都不会因浮点噪声变成负数。
3. **接口语义澄清**：明确 `get_real_part`/`get_imag_part` 等便捷函数返回的是“物理化后的矩阵”，必要时提供原始矩阵访问入口，以兼容 MATLAB 对比测试。
4. **回归测试补充**：新增单元测试覆盖“极小负特征值”“非数组输入”等边界，以锁定上述修复，防止后续回归。

## 四、下一步实施建议
- **短期**：
  - 调整构造函数与 `eigenvalues` 属性，确保当前 4 个失败用例全部通过；
  - 更新集成测试文档，说明物理化对虚部的影响。
- **中期**：
  - 结合 `density_matrix_physicalization_analysis.md` 中的方案，评估是否需要在 `DensityMatrix` 内部保留原始矩阵快照；
  - 审查 `make_physical` 在批量管线中的使用，确认外部模块不会依赖未物理化的矩阵数据。
- **长期**：
  - 在性能测试环境中收集更大维度（≥32）的统计数据，验证新增容差裁剪不会造成性能瓶颈；
  - 同步 MATLAB 对比脚本，使其显式区分“原始输入”“物理输出”，减少跨语言联调成本。
