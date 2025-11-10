# LinearReconstructor Implementation Plan

_Last updated: 2025-10-06_

## 1. 背景与目标
- MATLAB 的 `reconstruct_density_matrix_nD.m` 通过求解线性方程组重构密度矩阵：先生成 `n²` 个投影算符 `mu`，将它们展开成测量矩阵 `M`，再解 `M * rho_vector = P`，最终 reshape 成矩阵并调用 `makephysical`。
- Python 侧需要实现 `LinearReconstructor`，与现已完成的 `ProjectorSet`、`DensityMatrix` 配合，保证数值稳定性与物理约束（Hermitian、正半定、迹为 1）。

## 2. 需求拆解
1. **输入处理**
   - 接收观测概率/功率向量 `P`（长度 `n²`）。按照 MATLAB 逻辑，先对原始向量进行归一化：`P_norm = P / sum(P[:n])`。
   - 需要检测 `sum(P[:n])` 是否接近 0，防止溢出/除零。若总量极小，可抛异常或回退到均匀分布（根据配置）。
   - 支持 `numpy.ndarray`、`list` 等输入类型；内部统一为 `np.ndarray(dtype=float)`。

2. **测量矩阵生成**
   - 复用 `ProjectorSet`：`proj_set = ProjectorSet.get(n)`；`M = proj_set.measurement_matrix`。
   - 需确保 `M` 的排列与 `ProjectorSet` 中 `bases/projectors` 的顺序一致，否则重构出的 `rho_vector` 将错位。

3. **线性求解**
   - 直接使用 `numpy.linalg.lstsq(M, P_norm, rcond=None)` 或 `scipy.linalg.lstsq`。返回最小二乘解、残差、秩、奇异值。
   - 若矩阵 `M` 奇异或条件数过大，可在日志/调试信息中提醒；必要时提供可选的正则化/伪逆方案。

4. **重构矩阵**
   - 将 `rho_vector` reshape 成 `(n, n)`，并执行共轭运算（与 MATLAB 保持一致）。
   - 通过 `DensityMatrix` 完成物理化：`rho = DensityMatrix(rho_matrix, tolerance=...)`。必要时可直接调用 `make_physical()` 便捷函数。

5. **输出与附加信息**
   - 返回 `DensityMatrix` 实例，或提供 `LinearReconstructorResult`（包含 `density`, `residuals`, `rank`, `singular_values` 等）以便调试。
   - 允许配置是否保留中间数据（如归一化后的概率、测量矩阵）以便分析。

6. **错误处理**
   - 输入长度不为 `n²`、维度非法、归一化因子近零等情况需要抛出明确异常。
   - 对外暴露的接口需保证异常信息易于定位问题。

## 3. 类设计草案
```python
class LinearReconstructor:
    """线性层析重构器。"""

    def __init__(self, dimension: int, *, tolerance: float = 1e-10,
                 regularization: float | None = None, cache_projectors: bool = True):
        self.dimension = dimension
        self.tolerance = tolerance
        self.regularization = regularization
        self.projector_set = ProjectorSet.get(dimension) if cache_projectors else ProjectorSet(dimension, cache=False)

    def _normalize_probabilities(self, probabilities: np.ndarray) -> np.ndarray: ...

    def reconstruct(self, probabilities: np.ndarray) -> DensityMatrix:
        """执行线性重构并返回物理化的密度矩阵。"""

    def reconstruct_with_details(self, probabilities: np.ndarray) -> LinearReconstructionResult:
        """返回包含残差、奇异值等调试信息的结果对象。"""
```
- `LinearReconstructionResult` 可使用 `dataclass`，字段包括 `density: DensityMatrix`、`rho_matrix_raw: np.ndarray`、`residuals: np.ndarray`、`rank: int`、`singular_values: np.ndarray`。
- `_normalize_probabilities` 单独成函数，便于测试和异常处理。

## 4. 物理正确性保障
- **Hermitian + 正半定 + 迹为 1**：依靠 `DensityMatrix` 类在构造时调用 `_make_physical_matrix`；若希望保留原始矩阵，可同时返回 `rho_matrix_raw`。
- **特征值截断/容差**：继承 `DensityMatrix` 的裁剪策略（`tol = max(tolerance, 1e-12)`）。可允许在构造 `LinearReconstructor` 时传入 `tolerance`，与 `DensityMatrix` 保持一致。
- **归一化安全性**：若归一化分母太小，提前报错或回退，避免放大噪声导致非物理结果。
- **条件数监控**：可在 `reconstruct_with_details` 中返回 `np.linalg.cond(M)` 或 `singular_values`，便于判断重构是否可靠。

## 5. 数值与性能注意
- `M` 的维度随系统维度平方增长（4×4 系统 M 为 16×16），因此线性重构仍可视为中小规模。使用 `numpy.linalg.lstsq` 足够。
- 对多次重构的批处理，可在外层循环中重复使用 `LinearReconstructor` 实例，避免重复获取 `ProjectorSet`。
- 如需进一步加速，可考虑预先计算 `M_pinv = np.linalg.pinv(M)` 并缓存；这部分可以作为扩展配置。

## 6. 测试计划
1. **单元测试 (`python/tests/unit/test_linear_reconstructor.py`)**
   - `dimension=2`，基于解析解验证：
     - 输入概率对应最大混合态（等比例概率） → 输出 `I/2`。
     - 针对标准基投影的数据（如测量 `|0>` 概率为 1，其他为 0） → 重构 `|0><0|`。
   - 归一化边界：构造总概率和为 0 的输入，断言抛出 `ValueError`。
   - 返回详情：`reconstruct_with_details` 给出残差等信息。

2. **集成测试 (`python/tests/integration/test_linear_reconstruction.py`)**
   - 使用 MATLAB 生成的概率 + 密度矩阵对比（需整理参考数据）。
   - 随机生成物理密度矩阵 → 计算理论概率（`projectors[i] : trace(proj_i @ rho)`）→ 加入轻微噪声后重构，验证误差在容差内。
   - 验证跨模块工作流：`ProjectorSet` + `LinearReconstructor` + `DensityMatrix`。

3. **性能测试（可选）**
   - 对 4×4、8×8 系统进行基准测试，记录耗时，确保线性重构在目标维度下可接受。

## 7. 实施步骤
1. 创建 `python/qtomography/domain/reconstruction/linear.py` 并实现 `LinearReconstructor`。
2. 定义 `LinearReconstructionResult` 数据结构，提供残差、奇异值等调试信息。
3. 编写单元测试 `test_linear_reconstructor.py`（覆盖正常/异常场景）。
4. 编写集成测试 `test_linear_reconstruction.py`，对齐 MATLAB 或随机数据。
5. 更新文档：
   - `python/docs/implemented/` 新增/更新模块说明。
   - `python/docs/roadmap/2025-09-24-roadmap-status.md` 标记 P0-1 进展。
6. 如有需要，扩展 CLI/脚本以调用线性重构。

## 8. 后续扩展
- 支持权重/噪声模型（例如最小二乘中的加权矩阵）。
- 与 `MLEReconstructor` 共享接口，使两种重构策略可互换。
- 增加批量重构入口（一次性处理多组概率数据）。
- 记录 `M` 的奇异值、条件数，自动给出警告或调整策略。
