# ProjectorSet Implementation Plan

_Last updated: 2025-10-06_

## 1. 背景与目标
- MATLAB 入口 `generate_projectors_and_operators.m` 为线性重构提供 n 维系统的 `n²` 个测量基底及投影算符。Python 侧需要复刻此逻辑，并提供缓存以支撑批量重构。
- `ProjectorSet` 将成为 `LinearReconstructor` 的核心依赖，后者要用它构建测量矩阵 `M` 并解线性方程，最终生成 `DensityMatrix`。

## 2. 需求拆解
1. **基向量生成**
   - 标准基：`|0>…|n-1>`。
   - 组合基：`(|i> + |j>)/√2` 与 `(|i> - i|j>)/√2`，对应 MATLAB 的两类组合。第三类 `(|i> + i|j>)` 先保留为扩展。
   - 每个基向量均需归一化，最终数量达到 `n²`。

2. **投影算符**
   - 对于每个基向量 `ψ_i`，构造 `|ψ_i><ψ_i|`，得到 Hermitian、迹为 1 的 `n×n` 矩阵。
   - 实现：`projectors[i] = np.outer(basis, basis.conj())`。

3. **测量矩阵 M**
   - 线性重构需要 `M[j, :] = projectors[j].reshape(-1)`，`M` 尺寸 `n² × n²`。
   - `ProjectorSet` 提供属性或方法 `measurement_matrix`，便于 `LinearReconstructor` 使用。

4. **缓存策略**
   - 同一维度的投影集在多次重构中应复用。可选方案：
     - 类方法 `ProjectorSet.get(dimension)` 内部使用 `functools.lru_cache`；
     - 或外部装饰器 `@lru_cache` 放在私有工厂函数。
   - 允许显式清除缓存以便测试／调试。

5. **数据结构**
   - `bases`: shape `(n², n)` 的 `np.ndarray` 或 `List[np.ndarray]`。
   - `projectors`: shape `(n², n, n)`。
   - `measurement_matrix`: shape `(n², n²)`。
   - 允许延迟计算：先生成基向量，投影矩阵 / M 按需懒加载。

## 3. 对外 API 草案
```python
class ProjectorSet:
    """Generate and cache projectors for an n-dimensional system."""

    def __init__(self, dimension: int, *, cache: bool = True):
        self.dimension = dimension
        self._bases = None
        self._projectors = None
        self._measurement_matrix = None
        if cache:
            self._load_from_cache_or_build()
        else:
            self._build()

    @property
    def bases(self) -> np.ndarray: ...

    @property
    def projectors(self) -> np.ndarray: ...

    @property
    def measurement_matrix(self) -> np.ndarray: ...

    @classmethod
    def get(cls, dimension: int) -> "ProjectorSet":
        """Return a cached instance for the given dimension."""
        ...

    @classmethod
    def clear_cache(cls): ...
```
- `_build()` 调用 `_build_bases`、`_build_projectors`。
- 类封装有利于扩展；将来可暴露更多参数（如组合基的类型）。

## 4. 与 LinearReconstructor 的接口
- MATLAB 步骤：
  1. `generate_projectors_and_operators(n)` → projectors `mu`；
  2. 构造 `M`；
  3. 求解 `rho_vector = M \ P`。
- Python 规划：
  - `ProjectorSet.measurement_matrix` 直接提供矩阵 `M`。
  - `LinearReconstructor.reconstruct(probabilities)` 示例：
    ```python
    proj = ProjectorSet.get(n)
    rho_vec, *_ = np.linalg.lstsq(proj.measurement_matrix, probabilities, rcond=None)
    rho_matrix = rho_vec.reshape(n, n)
    rho_matrix = rho_matrix.conj()
    return DensityMatrix(rho_matrix)
    ```
  - 允许外部传入现成的 `ProjectorSet`，便于测试。

## 5. 测试计划
1. **单元测试 (python/tests/unit/test_projectors.py)**
   - `dimension=2`：验证基向量数量、归一化、组合基与 MATLAB 逻辑一致。
   - `dimension=3`：验证 `9` 个投影矩阵 Hermitian、迹为 1。
   - `measurement_matrix` 各行 reshape 回投影矩阵与 `projectors` 相符。
   - 缓存：`ProjectorSet.get(2)` 连续调用返回同实例（或同标识）。
   - 异常：维度 < 2 抛 `ValueError`。

2. **集成测试**
   - 在待实现的 `test_linear_reconstruction.py` 中串联 `ProjectorSet` 和 `LinearReconstructor`，对比 MATLAB 输出。
   - 使用随机密度矩阵 → 计算概率 → 重构 → 验证误差。

## 6. 实施步骤
1. 新增 `projectors.py`，实现 `ProjectorSet`（含缓存）。
2. 编写单元测试并更新 `pytest` 配置（如需导入新测试模块）。
3. 更新 `python/docs/implemented/` 或该文档记录实现细节。
4. 做基础性能评估（生成 `8×8` 投影集耗时），验证可接受。
5. 为 `LinearReconstructor` 预留钩子（后续任务）。

## 7. 后续扩展
- 支持更多测量基（例如 MATLAB 注释掉的 `( |i> + i|j> )`）。
- 统一缓存策略供 MLE 重构复用。
- 在 CLI / 应用层提供配置项。
- 结合结果持久化模块，将生成的投影集用于数据记录。
