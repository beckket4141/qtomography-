# MLEReconstructor 结构概述

> **一句话总结**：MLEReconstructor 通过最大似然估计 (Maximum Likelihood Estimation) 迭代优化重构量子态，物理约束内置，适合高精度、高噪声场景。

---

## 1) 模块定位与职责

### A. 在整体架构中的位置

```
量子层析重构流程
  ↓
测量概率 p_i (实验数据)
  ↓
归一化处理
  ↓
初始猜测（可选：Linear 结果）
  ↓
MLEReconstructor 迭代优化  ← 本模块
  ├─ Cholesky 参数化（保证正定）
  ├─ Chi² 目标函数（拟合测量）
  └─ L-BFGS-B 优化器（无约束优化）
  ↓
物理化处理（DensityMatrix）
  ↓
高精度密度矩阵 ρ
```

### B. 核心职责

| 职责 | 说明 |
|------|------|
| **参数化编码** | Cholesky 分解 + log 变换，自动满足正定约束 |
| **目标函数** | Chi² 最小化 + 可选正则化 |
| **迭代优化** | 使用 scipy.optimize.minimize 寻找最优解 |
| **初始值策略** | 默认使用 Linear 重构结果，或用户自定义 |
| **完整诊断** | 返回优化状态、迭代次数、目标函数值 |

---

## 2) `MLEReconstructor` 类的设计模式

### 设计特点

1. **约束优化 → 无约束优化**：通过 Cholesky 参数化将物理约束编码进参数空间
2. **分离关注点**：编码/解码、目标函数、优化器分离
3. **可配置策略**：支持多种优化器（L-BFGS-B, trust-constr, SLSQP）
4. **鲁棒初始化**：自动从 Linear 结果初始化，失败时用最大混态

---

## 3) 接口结构（按用途分组）

### (a) 构造与初始化

```python
__init__(
    dimension: int,
    *,
    tolerance: float = 1e-10,
    optimizer: str = "L-BFGS-B",
    regularization: Optional[float] = None,
    max_iterations: int = 2000,
    cache_projectors: bool = True,
)
```

**流程**：
```
1. 校验参数
   ├─ dimension >= 2
   ├─ tolerance > 0
   ├─ regularization >= 0 (若提供)
   └─ max_iterations > 0
2. 获取 ProjectorSet
   ├─ cache=True → ProjectorSet.get(dimension)
   └─ cache=False → ProjectorSet(dimension, cache=False)
3. 存储配置参数
```

**关键参数**：
- `dimension`：希尔伯特空间维度 $n$
- `tolerance`：传递给 `DensityMatrix` 的数值容差
- `optimizer`：优化器名称（默认 `L-BFGS-B`，推荐用于无约束问题）
- `regularization`：L2 正则化系数（可选，抑制参数震荡）
- `max_iterations`：最大迭代次数（默认 2000）
- `cache_projectors`：是否复用 `ProjectorSet` 缓存

---

### (b) 重构方法（两种接口）

#### 方法 1: 简洁接口

```python
reconstruct(
    probabilities: np.ndarray,
    initial_density: Optional[DensityMatrix | np.ndarray] = None,
) -> DensityMatrix
```

**用途**：仅返回物理化后的密度矩阵（常用场景）

**示例**：
```python
reconstructor = MLEReconstructor(dimension=2)
density = reconstructor.reconstruct(probabilities)
print(density.matrix)
```

---

#### 方法 2: 完整接口

```python
reconstruct_with_details(
    probabilities: np.ndarray,
    initial_density: Optional[DensityMatrix | np.ndarray] = None,
) -> MLEReconstructionResult
```

**用途**：返回包含优化诊断信息的完整结果对象

**返回结构**（`MLEReconstructionResult` dataclass）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `density` | `DensityMatrix` | 物理化后的密度矩阵（主要结果） |
| `rho_matrix_raw` | `np.ndarray` | 优化结束时的原始矩阵（已归一化） |
| `normalized_probabilities` | `np.ndarray` | 归一化后的测量概率向量 |
| `expected_probabilities` | `np.ndarray` | 由 $\rho$ 计算的理论概率（用于比对） |
| `objective_value` | `float` | 最终目标函数值（Chi²） |
| `success` | `bool` | 优化器是否成功收敛 |
| `status` | `int` | 优化器状态码 |
| `message` | `str` | 优化器返回的信息 |
| `n_iterations` | `int` | 实际迭代次数 |
| `n_function_evaluations` | `int` | 目标函数调用次数 |

**示例**：
```python
result = reconstructor.reconstruct_with_details(probabilities)
print(f"收敛: {result.success}")
print(f"迭代次数: {result.n_iterations}")
print(f"Chi²: {result.objective_value:.6f}")
print(f"残差: {np.linalg.norm(result.normalized_probabilities - result.expected_probabilities):.6f}")
```

---

### (c) 参数化编码/解码（核心算法）

#### 编码：密度矩阵 → 实参数向量

```python
@staticmethod
encode_density_to_params(rho: np.ndarray) -> np.ndarray
```

**流程**：
```
1. Cholesky 分解: ρ = L L†
   └─ 若失败，添加小的对角补偿 (ε·I)
2. 提取下三角矩阵 L 的元素
   ├─ 对角元素: log(L_ii)  (保证 > 0)
   └─ 下三角元素: Re(L_ij), Im(L_ij)
3. 返回实参数向量 (n² 维)
```

**参数结构**：
$$
\text{params} = [\log L_{00}, \log L_{11}, \ldots, \log L_{n-1,n-1}, \text{Re}(L_{10}), \text{Im}(L_{10}), \ldots]
$$

**总参数数**：
$$
n + 2 \times \frac{n(n-1)}{2} = n^2
$$

---

#### 解码：实参数向量 → 密度矩阵

```python
@staticmethod
decode_params_to_density(params: np.ndarray, dimension: int) -> np.ndarray
```

**流程**：
```
1. 重构下三角矩阵 L
   ├─ 对角: L_ii = exp(params[...])
   └─ 下三角: L_ij = Re + i·Im
2. 计算 ρ = L L†
3. 迹归一化: ρ = ρ / Tr(ρ)
```

**自动保证**：
- ✅ 正定性：$\rho = LL^\dagger$ 必然半正定
- ✅ 厄米性：$\rho = LL^\dagger$ 自动厄米
- ✅ 归一性：显式归一化 $\mathrm{Tr}(\rho) = 1$

---

### (d) 目标函数（优化目标）

```python
def _objective_function(
    self,
    params: np.ndarray,
    probabilities: np.ndarray,
    projectors: np.ndarray,
    regularization: Optional[float],
) -> float
```

**公式**：
$$
\chi^2 = \sum_{i=1}^{n^2} \frac{(p_i - p_i^{\text{exp}})^2}{p_i^{\text{exp}}} + \lambda \|\text{params}\|^2
$$

其中：
- $p_i$：测量概率
- $p_i^{\text{exp}} = \mathrm{Tr}(E_i \rho)$：理论概率
- $\lambda$：正则化系数（可选）

**实现细节**：
```python
1. 解码参数 → ρ
2. 计算期望概率: p_exp = Tr(E_i ρ)
3. 裁剪: p_exp = max(p_exp, 1e-12)  # 防止除零
4. 计算 Chi²
5. 添加正则化项（若启用）
```

**数值稳定技巧**：
- `np.clip(expected, 1e-12, None)`：防止分母为零
- `optimize=True` in `einsum`：加速迹运算

---

### (e) 初始值策略

```python
def _prepare_initial_density(
    self,
    probabilities: np.ndarray,
    initial_density: Optional[DensityMatrix | np.ndarray],
) -> np.ndarray
```

**策略优先级**：
```
1. 用户提供 initial_density
   └─ 使用用户提供的矩阵
2. 自动初始化（默认）
   ├─ 尝试 Linear 重构
   └─ 失败 → 最大混态 (I/n)
```

**为什么需要好的初始值？**
- MLE 是非凸优化问题
- 可能存在多个局部极小值
- 好的初始值加速收敛，提高成功率

---

### (f) 期望概率计算

```python
@staticmethod
def _expected_probabilities(rho: np.ndarray, projectors: np.ndarray) -> np.ndarray
```

**公式**：
$$
p_i^{\text{exp}} = \mathrm{Tr}(E_i \rho) = \sum_{j,k} (E_i)_{jk} \rho_{kj}
$$

**高效实现**：
```python
np.einsum('aij,ji->a', projectors, rho, optimize=True)
```

**einsum 解释**：
- `'aij,ji->a'`：对每个投影算符 $E_i$ 计算 $\mathrm{Tr}(E_i \rho)$
- `a`：投影算符索引（$n^2$ 个）
- `ij`：矩阵索引
- `optimize=True`：自动优化计算顺序

---

## 4) 数学原理

### Cholesky 参数化的优越性

#### 问题：如何保证 $\rho \succeq 0$？

**方法 1：特征值约束**（传统）
$$
\rho = U \Lambda U^\dagger, \quad \lambda_i \geq 0
$$
- ❌ 需要显式约束优化（复杂）
- ❌ 约束可能不光滑

**方法 2：Cholesky 分解**（本实现）
$$
\rho = LL^\dagger
$$
- ✅ 自动满足 $\rho \succeq 0$（无需约束）
- ✅ 参数空间无约束（优化器友好）

---

### 对角元素的 log 变换

#### 为什么对角用 $\log$？

**原始表示**：$L_{ii} \in \mathbb{R}_+$（正数）

**log 变换后**：$\tilde{L}_{ii} = \log L_{ii} \in \mathbb{R}$（全实数）

**优势**：
1. **无约束优化**：参数可以取任意实数
2. **数值稳定**：避免 $L_{ii} \to 0$ 导致的奇异
3. **尺度不变**：log 空间对数值范围更友好

**解码时**：
$$
L_{ii} = \exp(\tilde{L}_{ii}) > 0
$$

---

### Chi² 目标函数的物理意义

$$
\chi^2 = \sum_{i=1}^{n^2} \frac{(p_i^{\text{obs}} - p_i^{\text{exp}})^2}{p_i^{\text{exp}}}
$$

**物理解释**：
- 加权最小二乘：误差按期望概率加权
- 当 $p_i^{\text{exp}}$ 小时，给予较小权重（避免放大噪声）
- 对应泊松统计的最大似然估计

**与标准最小二乘的区别**：
| 方法 | 目标函数 | 适用场景 |
|------|---------|---------|
| 最小二乘 | $\sum (p_i^{\text{obs}} - p_i^{\text{exp}})^2$ | 高斯噪声 |
| Chi² | $\sum \frac{(p_i^{\text{obs}} - p_i^{\text{exp}})^2}{p_i^{\text{exp}}}$ | 泊松噪声（计数统计） |

---

## 5) 典型使用流程

### 场景 1: 默认配置（自动初始化）

```python
from qtomography.domain.reconstruction.mle import MLEReconstructor

# 测量概率（示例：2维系统）
probabilities = np.array([0.8, 0.2, 0.5, 0.5])

# 创建 MLE 重构器
reconstructor = MLEReconstructor(dimension=2)

# 重构（自动用 Linear 结果初始化）
density = reconstructor.reconstruct(probabilities)

# 使用结果
print(density.matrix)
print(f"纯度: {density.purity:.4f}")
```

---

### 场景 2: 自定义初始值

```python
# 使用 Linear 结果作为初始值
from qtomography.domain.reconstruction.linear import LinearReconstructor

linear_recon = LinearReconstructor(dimension=2)
initial_density = linear_recon.reconstruct(probabilities)

# MLE 精修
mle_recon = MLEReconstructor(dimension=2)
density_refined = mle_recon.reconstruct(probabilities, initial_density=initial_density)
```

---

### 场景 3: 完整诊断（检查收敛）

```python
reconstructor = MLEReconstructor(
    dimension=2,
    optimizer="L-BFGS-B",
    max_iterations=5000,
    regularization=1e-6,  # 添加正则化
)

result = reconstructor.reconstruct_with_details(probabilities)

# 检查收敛
print(f"✓ 成功: {result.success}")
print(f"迭代次数: {result.n_iterations}")
print(f"目标函数值: {result.objective_value:.6f}")
print(f"优化器信息: {result.message}")

# 检查拟合质量
residual = np.linalg.norm(result.normalized_probabilities - result.expected_probabilities)
print(f"概率残差: {residual:.6f}")
```

---

### 场景 4: 对比 Linear 与 MLE

```python
# Linear 重构
linear_recon = LinearReconstructor(dimension=2)
density_linear = linear_recon.reconstruct(probabilities)

# MLE 重构（用 Linear 初始化）
mle_recon = MLEReconstructor(dimension=2)
density_mle = mle_recon.reconstruct(probabilities, initial_density=density_linear)

# 对比保真度（假设已知真实态 true_density）
fidelity_linear = density_linear.fidelity(true_density)
fidelity_mle = density_mle.fidelity(true_density)

print(f"Linear 保真度: {fidelity_linear:.4f}")
print(f"MLE 保真度: {fidelity_mle:.4f}")
print(f"提升: {(fidelity_mle - fidelity_linear)*100:.2f}%")
```

---

## 6) 数据流（重构过程）

```
输入概率 p (n² 维)
  ↓
_normalize_probabilities()
  └─ p_norm = p / sum(p[0:n])
  ↓
_prepare_initial_density()
  ├─ 用户提供 → 使用
  ├─ 默认 → Linear 重构
  └─ 失败 → I/n
  ↓
encode_density_to_params(ρ_init)
  ├─ Cholesky: ρ = L L†
  ├─ 对角: log(L_ii)
  └─ 下三角: Re, Im
  → params0 (n² 维)
  ↓
scipy.optimize.minimize
  ├─ 迭代更新 params
  ├─ 每次迭代:
  │   ├─ decode_params_to_density(params)
  │   ├─ 计算 p_exp = Tr(E_i ρ)
  │   └─ 计算 Chi²
  └─ 收敛 → params_opt
  ↓
decode_params_to_density(params_opt)
  └─ ρ_opt
  ↓
DensityMatrix(ρ_opt, tolerance)
  ├─ 厄米化（通常已满足）
  ├─ 正定化（通常已满足）
  └─ 归一化（显式保证）
  ↓
返回 MLEReconstructionResult
  ├─ density
  ├─ rho_matrix_raw
  ├─ objective_value
  ├─ n_iterations
  └─ ...
```

---

## 7) 一眼看懂的"盒图"

```
[ MLEReconstructor ]
  |
  |-- state:
  |     ├─ dimension: int
  |     ├─ tolerance: float
  |     ├─ optimizer: str ("L-BFGS-B")
  |     ├─ regularization: Optional[float]
  |     ├─ max_iterations: int
  |     └─ projector_set: ProjectorSet
  |
  |-- interface:
  |     ├─ reconstruct(p, init?)              → DensityMatrix
  |     └─ reconstruct_with_details(p, init?) → MLEReconstructionResult
  |
  |-- parameterization:
  |     ├─ encode_density_to_params(ρ)  → params (Cholesky + log)
  |     └─ decode_params_to_density(p)  → ρ (逆操作)
  |
  |-- optimization:
  |     ├─ _objective_function(params)  → Chi²
  |     ├─ _expected_probabilities(ρ)   → p_exp
  |     └─ scipy.optimize.minimize      → params_opt
  |
  |-- initialization:
  |     └─ _prepare_initial_density()
  |          ├─ User provided
  |          ├─ Linear (default)
  |          └─ I/n (fallback)
  |
  |-- output:
        └─ MLEReconstructionResult
             ├─ density: DensityMatrix
             ├─ rho_matrix_raw: np.ndarray
             ├─ objective_value: float
             ├─ success: bool
             ├─ n_iterations: int
             └─ ...
```

---

## 8) 典型例子：2维系统

### 输入数据

```python
dimension = 2
probabilities = np.array([0.8, 0.2, 0.5, 0.5])
```

### 归一化

```python
leading_sum = 0.8 + 0.2 = 1.0
p_norm = [0.8, 0.2, 0.5, 0.5]
```

---

### 初始化（Linear 重构）

假设 Linear 重构给出：
$$
\rho_{\text{init}} = \begin{bmatrix} 0.8 & 0 \\ 0 & 0.2 \end{bmatrix}
$$

### Cholesky 分解

$$
\rho = LL^\dagger = \begin{bmatrix} \sqrt{0.8} & 0 \\ 0 & \sqrt{0.2} \end{bmatrix} \begin{bmatrix} \sqrt{0.8} & 0 \\ 0 & \sqrt{0.2} \end{bmatrix}
$$

### 参数编码

$$
\text{params} = [\log(\sqrt{0.8}), \log(\sqrt{0.2})] \approx [-0.112, -0.805]
$$

（下三角无元素，因为 $n=2$ 时只有对角）

---

### 优化迭代（简化示意）

| 迭代 | params | Chi² |
|------|--------|------|
| 0 | [-0.112, -0.805] | 0.0001 |
| 1 | [-0.113, -0.804] | 0.00008 |
| ... | ... | ... |
| 15 | [-0.114, -0.803] | 0.00001 ✓ |

（实际对此例，Linear 已接近最优，MLE 改进很小）

---

### 解码参数

$$
L_{00} = \exp(-0.114) \approx 0.892
$$
$$
L_{11} = \exp(-0.803) \approx 0.448
$$

$$
\rho_{\text{opt}} = \begin{bmatrix} 0.892^2 & 0 \\ 0 & 0.448^2 \end{bmatrix} \approx \begin{bmatrix} 0.796 & 0 \\ 0 & 0.201 \end{bmatrix}
$$

### 归一化

$$
\mathrm{Tr}(\rho) = 0.796 + 0.201 = 0.997 \approx 1
$$

（已接近 1，微调后精确归一）

---

## 9) 与 MATLAB 版本对齐

### 参数化方法

**MATLAB 原始实现**：
- 使用上三角矩阵 $T$：$\rho = TT^\dagger$
- 对角元素直接存储（无 log）

**Python 实现（改进）**：
- 使用下三角矩阵 $L$：$\rho = LL^\dagger$
- 对角元素用 $\log$ 变换

**改进原因**：
1. `scipy.linalg.cholesky` 默认返回下三角
2. log 变换增强数值稳定性
3. 更符合无约束优化范式

---

### 目标函数

**MATLAB**：Chi² 最小化（相同）

**Python**：Chi² + 可选 L2 正则化（增强）

---

## 10) 性能与适用场景

### 计算复杂度

| 操作 | 复杂度 | 备注 |
|------|--------|------|
| 参数编码（Cholesky） | $O(n^3)$ | 每次初始化 |
| 参数解码 | $O(n^3)$ | 每次迭代 |
| 期望概率计算 | $O(n^4)$ | einsum 优化 |
| 优化迭代 | $O(k \times n^4)$ | $k$ 是迭代次数 |

**总复杂度**：$O(k \times n^4)$，其中 $k \approx 10 \sim 100$

---

### 典型运行时间（参考）

| 维度 | Linear | MLE (k≈20) | MLE (k≈100) |
|------|--------|-----------|------------|
| 2维 | ~1ms | ~30ms | ~150ms |
| 4维 | ~10ms | ~300ms | ~1.5s |
| 8维 | ~100ms | ~5s | ~25s |
| 16维 | ~2s | ~2min | ~10min |

**注意**：实际时间依赖于：
- 初始值质量（Linear 初始化通常 20 次迭代内收敛）
- 优化器选择（L-BFGS-B 快于 trust-constr）
- 数据噪声水平

---

### 适用场景对比

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 快速验证 | Linear | 速度快，无需初始化 |
| 高精度重构 | MLE | 物理约束内置，理论最优 |
| 高噪声数据 | MLE + regularization | Chi² 对泊松噪声鲁棒 |
| 批量处理 | Linear → MLE (筛选) | Linear 快速筛选，MLE 精修关键样本 |
| 实时应用 | Linear | MLE 迭代慢 |
| 论文级精度 | MLE | 符合标准量子层析流程 |

---

## 11) 使用建议

### ✅ 推荐做法

```python
# 1. 默认配置（适合大多数场景）
reconstructor = MLEReconstructor(dimension=2)

# 2. 用 Linear 初始化（加速收敛）
linear_density = LinearReconstructor(2).reconstruct(probs)
mle_density = reconstructor.reconstruct(probs, initial_density=linear_density)

# 3. 完整诊断（检查收敛）
result = reconstructor.reconstruct_with_details(probs)
if not result.success:
    print(f"警告：未收敛，{result.message}")
    print(f"考虑增加 max_iterations 或改用其他优化器")

# 4. 高噪声配置
reconstructor = MLEReconstructor(
    dimension=4,
    regularization=1e-6,  # 抑制参数震荡
    max_iterations=5000,
)
```

---

### ❌ 不推荐做法

```python
# 1. 不检查收敛就使用结果
density = reconstructor.reconstruct(probs)
# 应该用 reconstruct_with_details 检查 success

# 2. 用非物理初始值
init = np.random.rand(2, 2)  # 可能非厄米/非正定/非归一
mle_density = reconstructor.reconstruct(probs, initial_density=init)

# 3. 过大的正则化系数
reconstructor = MLEReconstructor(dimension=2, regularization=0.1)  # 过度抑制

# 4. 盲目增加迭代次数
reconstructor = MLEReconstructor(max_iterations=100000)
# 若 2000 次未收敛，可能是初始值或数据问题，不应只增加迭代
```

---

## 12) 常见问题与调试

### Q1: 优化器未收敛（success=False）

**可能原因**：
- 初始值不佳
- 数据严重不一致
- `max_iterations` 太小

**解决方案**：
```python
# 1. 检查初始值
linear_result = LinearReconstructor(2).reconstruct_with_details(probs)
print(f"Linear 残差: {np.linalg.norm(linear_result.residuals):.6f}")

# 2. 增加迭代次数
reconstructor = MLEReconstructor(dimension=2, max_iterations=5000)

# 3. 尝试不同优化器
for opt in ["L-BFGS-B", "trust-constr", "SLSQP"]:
    result = MLEReconstructor(2, optimizer=opt).reconstruct_with_details(probs)
    print(f"{opt}: success={result.success}, Chi²={result.objective_value:.6f}")
```

---

### Q2: Chi² 值很大

**阈值参考**：
- Chi² < 1：优秀（接近理论分布）
- 1 < Chi² < 10：良好
- Chi² > 10：可能存在系统误差

**解决方案**：
```python
result = reconstructor.reconstruct_with_details(probs)
print(f"Chi²: {result.objective_value:.4f}")

if result.objective_value > 10:
    print("数据可能存在系统误差或测量不完备")
    # 检查概率归一化
    print(f"概率总和: {result.normalized_probabilities.sum():.6f}")
```

---

### Q3: 迭代次数过多

**原因**：
- 初始值远离最优
- 目标函数地形复杂（多个局部极小）

**解决方案**：
```python
# 使用更好的初始值
linear_density = LinearReconstructor(2, regularization=1e-6).reconstruct(probs)
result = reconstructor.reconstruct_with_details(probs, initial_density=linear_density)
print(f"迭代次数: {result.n_iterations}")
```

---

### Q4: Cholesky 分解失败

**错误信息**：`无法对密度矩阵执行 Cholesky 分解`

**原因**：
- 初始密度矩阵非正定
- 数值误差导致接近奇异

**解决方案**：
```python
# encode_density_to_params 已内置自动修复（添加对角补偿）
# 若仍失败，检查初始值
print(f"特征值: {np.linalg.eigvals(initial_density)}")
# 应全部 >= 0
```

---

## 13) 扩展阅读

### 相关概念

- **Cholesky 分解**：正定矩阵的三角分解
- **无约束优化**：L-BFGS-B, BFGS, Conjugate Gradient
- **约束优化**：trust-constr, SLSQP, COBYLA
- **泊松似然**：计数数据的统计模型
- **L-曲线**：正则化参数选择方法

### 相关代码

- `LinearReconstructor`：提供初始值 → [linear的结构概述.md](./linear的结构概述.md)
- `DensityMatrix`：物理化处理 → [density的结构概述.md](./density的结构概述.md)
- `ProjectorSet`：提供投影算符 → [projector的结构概述.md](./projector的结构概述.md)
- `scipy.optimize.minimize`：优化引擎

---

## ✅ 总结

> MLEReconstructor 是一个**"物理约束内置、迭代优化、高精度"**的量子态重构器，适合对精度要求高的场景。

### 核心价值

| 功能 | 价值 |
|------|------|
| **Cholesky 参数化** | 自动满足正定约束，无需显式约束优化 |
| **Chi² 目标** | 适配泊松统计，对计数噪声鲁棒 |
| **自动初始化** | 默认用 Linear 结果，加速收敛 |
| **完整诊断** | 提供迭代次数、收敛状态、目标函数值 |

### 使用原则

1. **先 Linear 后 MLE**：Linear 快速验证，MLE 精修
2. **检查收敛**：用 `reconstruct_with_details` 检查 `success`
3. **好的初始值**：用 Linear 结果初始化（典型 20 次迭代收敛）
4. **噪声用正则化**：`regularization=1e-6` 起步

---

**文档版本**: v1.0  
**最后更新**: 2025年10月7日  
**作者**: AI Assistant  
**相关文档**: 
- [linear的结构概述.md](./linear的结构概述.md)
- [density的结构概述.md](./density的结构概述.md)
- [projector的结构概述.md](./projector的结构概述.md)
- [density公式教学.md](./density公式教学.md)
- [projector公式教学.md](./projector公式教学.md)
- [linear公式教学.md](./linear公式教学.md)

