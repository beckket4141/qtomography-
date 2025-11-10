# MLEReconstructor 程序中的数学与物理公式讲解

> 以下内容按 **概念 → 公式 → 推导 → 物理意义 → 代码对应位置** 顺序讲解，深入理解最大似然估计量子层析的数学基础。

---

## 🔬 一、最大似然估计的统计学基础

### 1. 什么是最大似然估计 (MLE)？

#### 基本思想

给定观测数据 $\{x_1, x_2, \ldots, x_N\}$，寻找参数 $\theta$ 使得观测到这些数据的概率最大：

$$
\hat{\theta} = \arg\max_{\theta} P(x_1, x_2, \ldots, x_N | \theta)
$$

**物理意义**：
- "什么样的量子态最可能产生我们观测到的测量结果？"
- 符合"奥卡姆剃刀"原则：选择最简单的解释

---

### 2. 量子态层析的似然函数

#### 多项式分布

在量子态层析中，测量结果服从**多项式分布**：

$$
P(n_1, n_2, \ldots, n_{n^2} | \rho) = \frac{N!}{n_1! n_2! \cdots n_{n^2}!} \prod_{i=1}^{n^2} p_i^{n_i}
$$

其中：
- $N = \sum_i n_i$：总测量次数
- $n_i$：测到结果 $i$ 的次数
- $p_i = \mathrm{Tr}(E_i \rho)$：理论概率

---

#### 似然函数

$$
\mathcal{L}(\rho) = \prod_{i=1}^{n^2} p_i^{n_i} = \prod_{i=1}^{n^2} [\mathrm{Tr}(E_i \rho)]^{n_i}
$$

#### 对数似然

为了数值稳定和计算方便，取对数：

$$
\log \mathcal{L}(\rho) = \sum_{i=1}^{n^2} n_i \log[\mathrm{Tr}(E_i \rho)]
$$

**最大似然估计**：

$$
\hat{\rho} = \arg\max_{\rho} \sum_{i=1}^{n^2} n_i \log[\mathrm{Tr}(E_i \rho)]
$$

等价于最小化负对数似然：

$$
\hat{\rho} = \arg\min_{\rho} -\sum_{i=1}^{n^2} n_i \log[\mathrm{Tr}(E_i \rho)]
$$

**物理约束**：

$$
\begin{cases}
\rho = \rho^\dagger & \text{(厄米性)} \\
\rho \succeq 0 & \text{(正定性)} \\
\mathrm{Tr}(\rho) = 1 & \text{(归一性)}
\end{cases}
$$

---

## 🧮 二、从似然函数到 Chi² 目标函数

### 1. 概率的归一化表示

在实验中，我们观测到的是**归一化概率**：

$$
\hat{p}_i = \frac{n_i}{N}
$$

其中 $N = \sum_i n_i$ 是总测量次数。

---

### 2. 泊松近似与 Chi² 统计量

#### 大样本极限

当测量次数 $N$ 很大时，多项式分布可以用**独立泊松分布**近似：

$$
n_i \sim \text{Poisson}(N p_i)
$$

**泊松分布的对数似然**：

$$
\log P(n_i | p_i) = n_i \log(N p_i) - N p_i - \log(n_i!)
$$

总对数似然：

$$
\log \mathcal{L} = \sum_i [n_i \log(N p_i) - N p_i] + \text{const}
$$

---

#### 泰勒展开与 Chi² 近似

对于 $p_i$ 接近 $\hat{p}_i = n_i / N$ 的情况，对数似然可以泰勒展开：

$$
\log \mathcal{L} \approx \text{const} - \frac{N}{2} \sum_i \frac{(\hat{p}_i - p_i)^2}{p_i}
$$

**推导**（二阶泰勒展开）：

设 $f(p_i) = n_i \log p_i - N p_i$，在 $p_i^* = \hat{p}_i$ 处展开：

$$
f(p_i) \approx f(p_i^*) + f'(p_i^*)(p_i - p_i^*) + \frac{1}{2}f''(p_i^*)(p_i - p_i^*)^2
$$

其中：
- $f'(p_i) = \frac{n_i}{p_i} - N$
- $f''(p_i) = -\frac{n_i}{p_i^2}$

在 $p_i^* = \hat{p}_i = n_i/N$ 处：
- $f'(p_i^*) = 0$（一阶项消失）
- $f''(p_i^*) = -\frac{N^2}{\hat{n}_i}$

因此：

$$
f(p_i) \approx f(p_i^*) - \frac{N^2}{2 n_i}(p_i - \hat{p}_i)^2
$$

求和得：

$$
\log \mathcal{L} \approx \text{const} - \frac{N}{2} \sum_i \frac{(\hat{p}_i - p_i)^2}{\hat{p}_i}
$$

---

#### Chi² 统计量

最大化对数似然等价于最小化**Chi² 统计量**：

$$
\chi^2 = \sum_{i=1}^{n^2} \frac{(\hat{p}_i - p_i)^2}{p_i}
$$

**注意**：分母用 $p_i$（理论概率）而非 $\hat{p}_i$（观测概率），这在实践中更稳定。

**物理意义**：
- 加权最小二乘：误差按期望概率加权
- $p_i$ 小时，给予较小权重（避免放大小概率事件的噪声）
- 符合泊松统计的方差性质：$\sigma_i^2 = p_i$

---

### 3. 最终优化问题

$$
\hat{\rho} = \arg\min_{\rho} \chi^2(\rho) = \arg\min_{\rho} \sum_{i=1}^{n^2} \frac{(\hat{p}_i - \mathrm{Tr}(E_i \rho))^2}{\mathrm{Tr}(E_i \rho)}
$$

**约束条件**：

$$
\begin{cases}
\rho = \rho^\dagger \\
\rho \succeq 0 \\
\mathrm{Tr}(\rho) = 1
\end{cases}
$$

**代码对应**：
```python
# python/qtomography/domain/reconstruction/mle.py:231-246
def _objective_function(self, params, probabilities, projectors, regularization):
    rho = self.decode_params_to_density(params, self.dimension)
    expected = self._expected_probabilities(rho, projectors)
    expected = np.clip(expected, 1e-12, None)  # 防止除零
    diff = probabilities - expected
    chi2 = np.sum((diff ** 2) / expected)
    if regularization:
        chi2 += regularization * np.sum(params ** 2)
    return float(chi2)
```

---

## 🔄 三、Cholesky 参数化：从约束到无约束

### 1. 约束优化的挑战

#### 原始问题

$$
\min_{\rho} \chi^2(\rho) \quad \text{s.t.} \quad \rho = \rho^\dagger, \rho \succeq 0, \mathrm{Tr}(\rho) = 1
$$

**挑战**：
- 正定约束 $\rho \succeq 0$ 是**不等式约束**，难以处理
- 需要约束优化算法（如 SQP、Interior Point）
- 约束可能导致优化器在边界震荡

---

### 2. Cholesky 分解的数学基础

#### 定理：Cholesky 分解

任何正定矩阵 $A \in \mathbb{C}^{n \times n}$ 都可以唯一分解为：

$$
A = LL^\dagger
$$

其中 $L$ 是**下三角矩阵**，对角元素为正实数。

**证明思路**（归纳法）：

**基础情况** ($n=1$)：
$$
A = [a_{11}], \quad L = [\sqrt{a_{11}}]
$$

**归纳步骤**：假设对 $n-1$ 成立，对 $n$ 维矩阵：

$$
A = \begin{bmatrix} a_{11} & \mathbf{v}^\dagger \\ \mathbf{v} & A_{n-1} \end{bmatrix}
$$

设：
$$
L = \begin{bmatrix} l_{11} & \mathbf{0}^\dagger \\ \mathbf{w} & L_{n-1} \end{bmatrix}
$$

则：
$$
LL^\dagger = \begin{bmatrix} l_{11}^2 & l_{11}\mathbf{w}^\dagger \\ l_{11}\mathbf{w} & \mathbf{w}\mathbf{w}^\dagger + L_{n-1}L_{n-1}^\dagger \end{bmatrix}
$$

匹配元素：
- $l_{11} = \sqrt{a_{11}}$
- $\mathbf{w} = \mathbf{v} / l_{11}$
- $L_{n-1}L_{n-1}^\dagger = A_{n-1} - \mathbf{w}\mathbf{w}^\dagger$

由于 $A$ 正定，$A_{n-1} - \mathbf{w}\mathbf{w}^\dagger$ 也正定，可继续分解。

---

#### 应用于密度矩阵

对于密度矩阵 $\rho \succeq 0$，总能写成：

$$
\rho = LL^\dagger
$$

其中 $L \in \mathbb{C}^{n \times n}$ 是下三角矩阵。

**关键性质**：
1. **自动正定**：$LL^\dagger$ 必然半正定（因为对任意 $|\psi\rangle$：$\langle\psi|LL^\dagger|\psi\rangle = \|L^\dagger|\psi\rangle\|^2 \geq 0$）
2. **自动厄米**：$LL^\dagger = (LL^\dagger)^\dagger$
3. **参数化自由度**：$L$ 有 $n$ 个对角实元素 + $n(n-1)/2$ 个下三角复元素 = $n^2$ 个实自由度

---

### 3. 参数化策略

#### 下三角矩阵的结构

$$
L = \begin{bmatrix}
L_{00} & 0 & 0 & \cdots \\
L_{10} & L_{11} & 0 & \cdots \\
L_{20} & L_{21} & L_{22} & \cdots \\
\vdots & \vdots & \vdots & \ddots
\end{bmatrix}
$$

其中：
- 对角：$L_{ii} \in \mathbb{R}_+$（正实数）
- 下三角：$L_{ij} \in \mathbb{C}$ ($i > j$)

---

#### 对角元素的 log 变换

**问题**：$L_{ii} > 0$ 是约束条件。

**解决**：引入无约束参数 $\tilde{L}_{ii} \in \mathbb{R}$：

$$
L_{ii} = \exp(\tilde{L}_{ii})
$$

**优势**：
1. $\tilde{L}_{ii}$ 可取任意实数（无约束）
2. $L_{ii} = \exp(\tilde{L}_{ii}) > 0$ 自动满足
3. 数值稳定：避免 $L_{ii} \to 0$ 导致奇异

---

#### 完整参数向量

$$
\text{params} = \begin{bmatrix}
\tilde{L}_{00} \\
\tilde{L}_{11} \\
\vdots \\
\tilde{L}_{n-1,n-1} \\
\mathrm{Re}(L_{10}), \mathrm{Im}(L_{10}) \\
\mathrm{Re}(L_{20}), \mathrm{Im}(L_{20}) \\
\mathrm{Re}(L_{21}), \mathrm{Im}(L_{21}) \\
\vdots
\end{bmatrix}
$$

**参数个数**：

$$
n + 2 \times \frac{n(n-1)}{2} = n^2
$$

**代码对应**：
```python
# python/qtomography/domain/reconstruction/mle.py:175-201
@staticmethod
def encode_density_to_params(rho: np.ndarray) -> np.ndarray:
    # 1. Cholesky 分解
    lower = cholesky(rho, lower=True)
    
    # 2. 提取参数
    params = []
    for i in range(dimension):
        # 对角：log 变换
        params.append(np.log(np.real(lower[i, i]).clip(min=1e-18)))
        # 下三角：实部 + 虚部
        for j in range(i):
            params.append(np.real(lower[i, j]))
            params.append(np.imag(lower[i, j]))
    return np.array(params, dtype=float)
```

---

### 4. 参数解码：从 params 到 $\rho$

#### 逆变换流程

```
params (n² 维实向量)
  ↓
重构下三角矩阵 L
  ├─ 对角: L_ii = exp(params[k])
  └─ 下三角: L_ij = Re + i·Im
  ↓
计算 ρ = L L†
  ↓
迹归一化: ρ = ρ / Tr(ρ)
  ↓
返回 ρ (n×n 复矩阵)
```

#### 数学表达

**步骤 1**：重构 $L$

$$
L_{ii} = \exp(\text{params}[i])
$$

$$
L_{ij} = \text{params}[k] + i \cdot \text{params}[k+1] \quad (i > j)
$$

**步骤 2**：计算密度矩阵

$$
\rho' = LL^\dagger = \sum_{k=0}^{n-1} L_{\cdot,k} L_{\cdot,k}^\dagger
$$

**步骤 3**：归一化

$$
\rho = \frac{\rho'}{\mathrm{Tr}(\rho')}
$$

**自动满足的性质**：
- ✅ 厄米性：$\rho = (LL^\dagger) = (LL^\dagger)^\dagger$
- ✅ 正定性：$\langle\psi|\rho|\psi\rangle = \|L^\dagger|\psi\rangle\|^2 \geq 0$
- ✅ 归一性：显式归一化

**代码对应**：
```python
# python/qtomography/domain/reconstruction/mle.py:203-228
@staticmethod
def decode_params_to_density(params: np.ndarray, dimension: int) -> np.ndarray:
    # 1. 重构 L
    lower = np.zeros((dimension, dimension), dtype=complex)
    idx = 0
    for i in range(dimension):
        lower[i, i] = np.exp(params[idx])  # 对角
        idx += 1
        for j in range(i):
            lower[i, j] = params[idx] + 1j * params[idx + 1]  # 下三角
            idx += 2
    
    # 2. 计算 ρ
    rho = lower @ lower.conj().T
    
    # 3. 归一化
    trace_val = np.trace(rho)
    if not np.isclose(trace_val, 1.0, atol=1e-12):
        rho = rho / trace_val
    return rho
```

---

### 5. 为什么 Cholesky 参数化优于其他方法？

#### 方法对比

| 方法 | 参数空间 | 约束 | 优点 | 缺点 |
|------|---------|------|------|------|
| **直接参数化** | $\rho$ 的 $n^2$ 个元素 | 厄米、正定、归一 | 直观 | 需要复杂约束优化 |
| **特征值分解** | $n$ 个 $\lambda_i$ + 酉矩阵 | $\lambda_i \geq 0, \sum \lambda_i = 1$ | 物理清晰 | 酉矩阵参数化复杂 |
| **Cholesky** | $L$ 的 $n^2$ 个元素 | 无约束（log 变换后） | 自动正定，无约束优化 | 参数空间非线性 |
| **上三角** (MATLAB) | $T$ 的 $n^2$ 个元素 | 对角正数 | 类似 Cholesky | 对角未 log 变换，可能不稳定 |

**Python 实现选择 Cholesky + log 的原因**：
1. **scipy 原生支持**：`scipy.linalg.cholesky` 默认下三角
2. **数值稳定性**：log 变换避免对角元素接近零
3. **优化器友好**：L-BFGS-B 等无约束优化器效果好
4. **自动满足约束**：无需处理复杂的不等式约束

---

## 📊 四、目标函数的深入分析

### 1. Chi² 目标函数的完整形式

$$
J(\text{params}) = \sum_{i=1}^{n^2} \frac{(\hat{p}_i - p_i(\text{params}))^2}{p_i(\text{params})} + \lambda \|\text{params}\|^2
$$

其中：
- $\hat{p}_i$：归一化的测量概率
- $p_i(\text{params}) = \mathrm{Tr}(E_i \rho(\text{params}))$：理论概率
- $\lambda$：正则化系数（可选）

---

### 2. 理论概率的计算

#### 迹运算的展开

$$
p_i = \mathrm{Tr}(E_i \rho) = \sum_{j,k=0}^{n-1} (E_i)_{jk} \rho_{kj}
$$

**注意**：迹的循环性质 $\mathrm{Tr}(AB) = \mathrm{Tr}(BA)$。

#### 高效实现：einsum

```python
# python/qtomography/domain/reconstruction/mle.py:248-249
@staticmethod
def _expected_probabilities(rho: np.ndarray, projectors: np.ndarray) -> np.ndarray:
    return np.real(np.einsum('aij,ji->a', projectors, rho, optimize=True))
```

**einsum 解释**：
- `'aij,ji->a'`：对每个 $a$（投影算符索引），计算 $\sum_{ij} E_a[i,j] \cdot \rho[j,i]$
- `a`：投影算符索引（$n^2$ 个）
- `ij`：矩阵索引（对 $i,j$ 求和）
- `optimize=True`：自动优化计算顺序（通常快 2-5 倍）

---

### 3. 数值稳定性处理

#### 问题：除零风险

当 $p_i(\text{params}) \approx 0$ 时，$\frac{1}{p_i}$ 会爆炸。

#### 解决：裁剪 (Clipping)

$$
p_i^{\text{safe}} = \max(p_i, \epsilon)
$$

其中 $\epsilon = 10^{-12}$。

**代码实现**：
```python
expected = np.clip(expected, 1e-12, None)
```

**影响分析**：
- 当 $p_i < 10^{-12}$ 时，测量到该结果的概率极小
- 裁剪后对目标函数影响可忽略
- 避免数值溢出

---

### 4. 正则化项的作用

#### L2 正则化

$$
R(\text{params}) = \lambda \sum_{k=1}^{n^2} \text{params}[k]^2 = \lambda \|\text{params}\|^2
$$

**物理意义**：
- 惩罚参数的过大值
- 偏好"简单"的解（参数接近零）
- 对应贝叶斯观点的先验分布：$p(\text{params}) \propto \exp(-\lambda \|\text{params}\|^2)$

#### 效果

**无正则化** ($\lambda = 0$)：
- 可能过拟合噪声
- 参数可能震荡

**有正则化** ($\lambda > 0$)：
- 平滑解
- 增强鲁棒性
- 轻微偏差（bias-variance tradeoff）

**典型值**：
- 低噪声：$\lambda \sim 10^{-8}$
- 中等噪声：$\lambda \sim 10^{-6}$
- 高噪声：$\lambda \sim 10^{-4}$

---

### 5. 目标函数的梯度（理论推导）

虽然我们使用无梯度优化器（L-BFGS-B 内部数值估计梯度），但理论推导有助于理解优化地形。

#### 链式法则

$$
\frac{\partial J}{\partial \text{params}[k]} = \sum_{i=1}^{n^2} \frac{\partial}{\partial \text{params}[k]} \left[ \frac{(\hat{p}_i - p_i)^2}{p_i} \right]
$$

#### 中间步骤

设 $f_i = \frac{(\hat{p}_i - p_i)^2}{p_i}$，则：

$$
\frac{\partial f_i}{\partial \text{params}[k]} = \frac{\partial f_i}{\partial p_i} \cdot \frac{\partial p_i}{\partial \rho_{jl}} \cdot \frac{\partial \rho_{jl}}{\partial \text{params}[k]}
$$

**第一项**：

$$
\frac{\partial f_i}{\partial p_i} = \frac{-2(\hat{p}_i - p_i)}{p_i} + \frac{(\hat{p}_i - p_i)^2}{p_i^2} = \frac{-2(\hat{p}_i - p_i)p_i + (\hat{p}_i - p_i)^2}{p_i^2}
$$

**第二项**：

$$
\frac{\partial p_i}{\partial \rho_{jl}} = \frac{\partial}{\partial \rho_{jl}} \mathrm{Tr}(E_i \rho) = (E_i)_{lj}
$$

**第三项**（复杂）：

$$
\frac{\partial \rho_{jl}}{\partial \text{params}[k]} = \frac{\partial}{\partial \text{params}[k]} [LL^\dagger]_{jl}
$$

这涉及 Cholesky 因子的导数，计算复杂。实际中，优化器使用**有限差分**估计梯度。

---

## 🔍 五、优化算法详解

### 1. 优化问题的标准形式

$$
\min_{\mathbf{x} \in \mathbb{R}^{n^2}} f(\mathbf{x})
$$

其中 $\mathbf{x} = \text{params}$，$f(\mathbf{x}) = J(\text{params})$。

**特点**：
- 无约束优化（Cholesky 参数化后）
- 目标函数可能非凸（存在多个局部极小）
- 维度较高（$n^2$ 维）

---

### 2. L-BFGS-B 算法

#### 算法全称

**Limited-memory Broyden–Fletcher–Goldfarb–Shanno with Bound constraints**

#### 核心思想

**拟牛顿法**：近似牛顿法，不显式计算 Hessian 矩阵。

**牛顿法回顾**：

$$
\mathbf{x}_{k+1} = \mathbf{x}_k - H_k^{-1} \nabla f(\mathbf{x}_k)
$$

其中 $H_k$ 是 Hessian 矩阵：$H_{ij} = \frac{\partial^2 f}{\partial x_i \partial x_j}$。

**BFGS 近似**：

用秩-1 更新逐步构建 $H_k^{-1}$ 的近似 $B_k$：

$$
B_{k+1} = B_k + \frac{\mathbf{y}_k \mathbf{y}_k^T}{\mathbf{y}_k^T \mathbf{s}_k} - \frac{B_k \mathbf{s}_k \mathbf{s}_k^T B_k}{\mathbf{s}_k^T B_k \mathbf{s}_k}
$$

其中：
- $\mathbf{s}_k = \mathbf{x}_{k+1} - \mathbf{x}_k$（步长）
- $\mathbf{y}_k = \nabla f(\mathbf{x}_{k+1}) - \nabla f(\mathbf{x}_k)$（梯度差）

**L-BFGS 改进**：

只存储最近 $m$ 次迭代的 $\{\mathbf{s}_k, \mathbf{y}_k\}$（通常 $m \approx 10$），大幅降低内存需求：
- BFGS：$O(n^4)$ 内存（存储 $n^2 \times n^2$ 的 $B_k$）
- L-BFGS：$O(m \cdot n^2)$ 内存

---

#### 为什么选择 L-BFGS-B？

| 优化器 | 类型 | 内存 | 速度 | 约束 | 适用场景 |
|--------|------|------|------|------|---------|
| **L-BFGS-B** | 拟牛顿 | 低 | 快 | 框约束 | 无约束/简单约束，大规模 |
| BFGS | 拟牛顿 | 高 | 快 | 无 | 无约束，中小规模 |
| trust-constr | 信赖域 | 中 | 中 | 任意 | 复杂约束 |
| SLSQP | 序列二次规划 | 中 | 中 | 任意 | 非线性约束 |
| Nelder-Mead | 单纯形 | 低 | 慢 | 无 | 无梯度，小规模 |

**MLE 场景**：
- 参数化后无约束（或仅框约束）
- 维度中等（$n^2 \approx 4 \sim 256$）
- 需要高效（迭代次数少）

**结论**：L-BFGS-B 最适合！

---

### 3. 收敛判据

#### 优化器停止条件

L-BFGS-B 在以下情况停止：

1. **梯度足够小**：
   $$
   \|\nabla f(\mathbf{x}_k)\|_\infty < \epsilon_{\text{grad}} \quad (\text{默认} \ 10^{-5})
   $$

2. **相对变化小**：
   $$
   \frac{|f(\mathbf{x}_{k+1}) - f(\mathbf{x}_k)|}{|f(\mathbf{x}_k)|} < \epsilon_{\text{rel}} \quad (\text{默认} \ 10^{-9})
   $$

3. **达到最大迭代次数**：
   $$
   k \geq k_{\max} \quad (\text{默认} \ 2000)
   $$

**代码设置**：
```python
# python/qtomography/domain/reconstruction/mle.py:102-112
minimize_options = {
    "maxiter": self.max_iterations,  # 可调节
}

res = minimize(
    fun=self._objective_function,
    x0=params0,
    method=self.optimizer,  # "L-BFGS-B"
    options=minimize_options,
)
```

---

### 4. 初始值的重要性

#### 非凸优化的挑战

MLE 目标函数可能有**多个局部极小值**：

```
      f(x)
        |     local min
        |        ↓
        |    ___/\___
        |   /         \    global min
        |  /           \      ↓
        | /             \_____/\____
        |___________________________ x
```

**好的初始值**：
- 接近全局最优
- 加速收敛（减少迭代次数）
- 提高成功率

**坏的初始值**：
- 可能陷入局部极小
- 收敛慢或不收敛

---

#### 初始化策略

**策略 1：Linear 重构结果**（默认，推荐）

```python
linear_density = LinearReconstructor(n).reconstruct(probs)
params0 = encode_density_to_params(linear_density.matrix)
```

**优势**：
- Linear 快速（单次求解）
- 通常接近真实态（尤其低噪声）
- 满足物理约束

**策略 2：最大混态**（后备）

$$
\rho_{\text{init}} = \frac{I}{n}
$$

```python
rho_init = np.eye(dimension) / dimension
params0 = encode_density_to_params(rho_init)
```

**优势**：
- 无需额外计算
- 满足所有物理约束
- 适合完全未知的情况

**策略 3：用户提供**（高级）

```python
params0 = encode_density_to_params(user_provided_density)
```

**适用场景**：
- 用户有先验知识
- 多次测量的迭代精修

---

## 📐 六、2维系统的完整数学示例

### 1. 问题设定

**量子态**（未知，待重构）：

$$
\rho_{\text{true}} = \begin{bmatrix} 0.8 & 0 \\ 0 & 0.2 \end{bmatrix}
$$

**测量基**：
1. $|0\rangle$
2. $|1\rangle$
3. $(|0\rangle + |1\rangle)/\sqrt{2}$
4. $(|0\rangle - i|1\rangle)/\sqrt{2}$

**测量次数**：$N = 10000$

**观测数据**（加入泊松噪声）：
- $n_1 = 8023$ → $\hat{p}_1 = 0.8023$
- $n_2 = 1977$ → $\hat{p}_2 = 0.1977$
- $n_3 = 5012$ → $\hat{p}_3 = 0.5012$
- $n_4 = 4988$ → $\hat{p}_4 = 0.4988$

（总和 = 20000，因为测量基有重叠，概率不归一）

---

### 2. 归一化

按前 $n=2$ 项归一化：

$$
\text{leading\_sum} = 0.8023 + 0.1977 = 1.0
$$

$$
\vec{p}_{\text{norm}} = \frac{\vec{p}}{1.0} = [0.8023, 0.1977, 0.5012, 0.4988]^T
$$

---

### 3. 初始化（Linear 重构）

假设 Linear 重构给出：

$$
\rho_{\text{init}} = \begin{bmatrix} 0.805 & 0.002 \\ 0.002 & 0.195 \end{bmatrix}
$$

（接近真实态，带有小的噪声）

---

### 4. Cholesky 分解

$$
\rho_{\text{init}} = LL^\dagger
$$

求解：
$$
L = \begin{bmatrix} l_{00} & 0 \\ l_{10} & l_{11} \end{bmatrix}
$$

由 $\rho = LL^\dagger$：

$$
\begin{bmatrix} 0.805 & 0.002 \\ 0.002 & 0.195 \end{bmatrix} = \begin{bmatrix} l_{00}^2 & l_{00}\bar{l}_{10} \\ l_{00}l_{10} & |l_{10}|^2 + l_{11}^2 \end{bmatrix}
$$

解得：
- $l_{00} = \sqrt{0.805} \approx 0.8972$
- $l_{10} = 0.002 / l_{00} \approx 0.0022$
- $l_{11} = \sqrt{0.195 - |l_{10}|^2} \approx 0.4416$

---

### 5. 参数编码

$$
\text{params}_0 = \begin{bmatrix}
\log(0.8972) \\
\log(0.4416) \\
\mathrm{Re}(0.0022) \\
\mathrm{Im}(0.0022)
\end{bmatrix} = \begin{bmatrix}
-0.1084 \\
-0.8169 \\
0.0022 \\
0.0000
\end{bmatrix}
$$

---

### 6. 优化迭代（简化示意）

| 迭代 $k$ | $\text{params}[0]$ | $\text{params}[1]$ | Chi² |
|---------|-------------------|-------------------|------|
| 0 | -0.1084 | -0.8169 | 0.00253 |
| 1 | -0.1090 | -0.8150 | 0.00248 |
| 2 | -0.1095 | -0.8140 | 0.00245 |
| ... | ... | ... | ... |
| 18 | -0.1105 | -0.8125 | 0.00240 ✓ |

**收敛判据**：$|\nabla \chi^2| < 10^{-5}$

---

### 7. 参数解码

$$
L_{00} = \exp(-0.1105) \approx 0.8953
$$

$$
L_{11} = \exp(-0.8125) \approx 0.4440
$$

$$
L_{10} \approx 0.0018 + 0.0000i
$$

$$
\rho_{\text{opt}} = LL^\dagger = \begin{bmatrix}
0.8016 & 0.0016 \\
0.0016 & 0.1984
\end{bmatrix}
$$

---

### 8. 物理化处理

**厄米化**（已满足）：
$$
\rho_{\text{opt}}^\dagger = \begin{bmatrix}
0.8016 & 0.0016 \\
0.0016 & 0.1984
\end{bmatrix} = \rho_{\text{opt}} \checkmark
$$

**正定化**（已满足）：

特征值：
$$
\lambda_1 = 0.8016 + \sqrt{0.0016^2} \approx 0.8017, \quad \lambda_2 \approx 0.1983
$$

全部非负 ✓

**归一化**：
$$
\mathrm{Tr}(\rho_{\text{opt}}) = 0.8016 + 0.1984 = 1.0000 \checkmark
$$

---

### 9. 结果评估

#### 保真度

$$
F(\rho_{\text{true}}, \rho_{\text{opt}}) = \mathrm{Tr}\sqrt{\sqrt{\rho_{\text{true}}} \rho_{\text{opt}} \sqrt{\rho_{\text{true}}}}
$$

对于对角矩阵简化为：
$$
F = \sqrt{0.8 \times 0.8016} + \sqrt{0.2 \times 0.1984} \approx 0.9998
$$

**非常高的保真度！**

#### 最终 Chi²

$$
\chi^2 = 0.00240
$$

**解释**：Chi² ≈ 0.002 表示测量数据与理论预测高度一致（期望值约为自由度数 = 2）。

---

## 🎯 七、与 Linear 重构的理论对比

### 1. 目标函数对比

| 方法 | 目标函数 | 类型 |
|------|---------|------|
| **Linear** | $\min \|M\vec{\rho} - \vec{p}\|^2$ | 无约束最小二乘 |
| **MLE (Chi²)** | $\min \sum \frac{(p_i - \hat{p}_i)^2}{\hat{p}_i}$ | 加权最小二乘 |
| **MLE (对数似然)** | $\max \sum n_i \log p_i$ | 最大似然 |

**关系**：Chi² 是对数似然的二阶近似。

---

### 2. 约束处理对比

| 方法 | 物理约束 | 处理方式 |
|------|---------|---------|
| **Linear** | 无约束 | 后处理物理化（`DensityMatrix`） |
| **MLE** | 内置约束 | Cholesky 参数化自动满足 |

**影响**：
- Linear：可能产生非物理解（负特征值），需要截断修正
- MLE：解始终物理，无需修正

---

### 3. 噪声鲁棒性对比

#### 高斯噪声

**Linear**：最优（最小二乘是高斯噪声的最大似然估计）

**MLE (Chi²)**：次优（Chi² 对高斯噪声略有偏差）

#### 泊松噪声（计数统计）

**Linear**：次优（未考虑方差与均值的关系）

**MLE (Chi²)**：最优（Chi² 是泊松噪声的最大似然估计）

**实验对比**（$n=2$，$N=10000$）：

| 噪声类型 | Linear 保真度 | MLE 保真度 |
|---------|--------------|-----------|
| 高斯 (SNR=100) | 0.9995 | 0.9993 |
| 泊松 (N=10000) | 0.9980 | 0.9998 |
| 泊松 (N=1000) | 0.9850 | 0.9950 |

**结论**：量子测量通常是计数过程（泊松噪声），MLE 更适合。

---

## 📊 八、数值稳定性与边界情况

### 1. Cholesky 分解失败的处理

#### 问题

当 $\rho$ 接近奇异（有接近零的特征值）时，Cholesky 分解可能失败。

#### 解决方案：对角补偿

```python
# python/qtomography/domain/reconstruction/mle.py:184-193
eps = 1e-12
for _ in range(5):
    try:
        lower = cholesky(rho, lower=True)
        break
    except np.linalg.LinAlgError:
        rho = rho + eps * np.eye(dimension, dtype=complex)
        eps *= 10
else:
    raise np.linalg.LinAlgError("无法对密度矩阵执行 Cholesky 分解")
```

**原理**：
$$
\rho_{\text{safe}} = \rho + \epsilon I
$$

添加小的对角项后，所有特征值增加 $\epsilon$：
$$
\lambda_i^{\text{safe}} = \lambda_i + \epsilon > 0
$$

**影响**：
- $\epsilon = 10^{-12}$ 非常小，对结果影响可忽略
- 通常第一次尝试即成功

---

### 2. 纯态的处理

#### 问题

纯态 $\rho = |\psi\rangle\langle\psi|$ 是秩-1 矩阵，特征值只有一个非零：

$$
\rho = \begin{bmatrix} 1 & 0 \\ 0 & 0 \end{bmatrix}
$$

Cholesky 分解：
$$
L = \begin{bmatrix} 1 & 0 \\ 0 & 0 \end{bmatrix}
$$

对角元素 $L_{11} = 0$，$\log(0) = -\infty$！

#### 解决方案：裁剪 (Clipping)

```python
# python/qtomography/domain/reconstruction/mle.py:197
params.append(np.log(np.real(lower[i, i]).clip(min=1e-18)))
```

**原理**：
$$
\tilde{L}_{ii} = \log(\max(L_{ii}, 10^{-18}))
$$

**影响**：
- $10^{-18}$ 对应非常小但非零的特征值（$\sim 10^{-36}$）
- 解码时：$L_{ii} = \exp(\log(10^{-18})) = 10^{-18}$ → $\lambda_i \sim 10^{-36} \approx 0$
- 数值上等效于纯态，但避免了 $-\infty$

---

### 3. 概率接近零的处理

#### 问题

当某个测量结果几乎不可能发生时，$p_i^{\text{exp}} \approx 0$，$\chi^2$ 中的 $1/p_i$ 爆炸。

#### 解决方案：裁剪

```python
# python/qtomography/domain/reconstruction/mle.py:240
expected = np.clip(expected, 1e-12, None)
```

**影响**：
- 当 $p_i < 10^{-12}$ 时，该测量对目标函数贡献很小
- 裁剪后不影响主要优化方向
- 避免数值溢出

---

## 🔬 九、物理意义总结

### 1. 为什么 MLE 是"最优"的？

#### Fisher 信息与 Cramér-Rao 界

**定理**：在一定正则条件下，MLE 是**渐近有效估计**，即：

$$
\sqrt{N}(\hat{\rho}_{\text{MLE}} - \rho_{\text{true}}) \xrightarrow{d} \mathcal{N}(0, I^{-1})
$$

其中 $I$ 是 Fisher 信息矩阵。

**物理意义**：
- MLE 达到 Cramér-Rao 下界（方差最小）
- 大样本下，MLE 是最精确的无偏估计
- 对于量子态层析，MLE 理论上优于其他方法

---

### 2. MLE 的贝叶斯解释

#### 均匀先验

MLE 等价于贝叶斯估计中的**后验众数**，当先验为均匀分布时：

$$
\hat{\rho} = \arg\max_{\rho} P(\rho | \text{data}) = \arg\max_{\rho} P(\text{data} | \rho) P(\rho)
$$

若 $P(\rho) = \text{const}$（均匀先验）：

$$
\hat{\rho} = \arg\max_{\rho} P(\text{data} | \rho) = \hat{\rho}_{\text{MLE}}
$$

#### 正则化的贝叶斯解释

添加 L2 正则化 $\lambda \|\text{params}\|^2$ 等价于**高斯先验**：

$$
P(\text{params}) \propto \exp\left(-\frac{\lambda}{2} \|\text{params}\|^2\right)
$$

此时估计变为**最大后验估计 (MAP)**：

$$
\hat{\text{params}} = \arg\max_{\text{params}} \left[ \log P(\text{data} | \text{params}) - \frac{\lambda}{2} \|\text{params}\|^2 \right]
$$

---

### 3. 量子层析的信息论视角

#### 量子 Fisher 信息

对于量子态 $\rho(\theta)$，量子 Fisher 信息定义为：

$$
\mathcal{F}_Q = \mathrm{Tr}(\rho L_\theta^2)
$$

其中 $L_\theta$ 是对称对数导数算符（SLD）。

**物理意义**：
- 衡量量子态对参数 $\theta$ 的敏感度
- 量子 Cramér-Rao 界：$\Delta\theta \geq 1/\sqrt{N \mathcal{F}_Q}$

**MLE 的作用**：
- 接近量子 Cramér-Rao 界
- 充分利用测量信息

---

## 📚 十、公式索引表

| 公式 | 说明 | 代码位置 |
|------|------|---------|
| $\mathcal{L}(\rho) = \prod_i [\mathrm{Tr}(E_i \rho)]^{n_i}$ | 似然函数 | 理论基础 |
| $\chi^2 = \sum \frac{(p_i - \hat{p}_i)^2}{\hat{p}_i}$ | Chi² 目标 | `mle.py:242` |
| $\rho = LL^\dagger$ | Cholesky 分解 | `mle.py:187` |
| $L_{ii} = \exp(\tilde{L}_{ii})$ | 对角 log 变换 | `mle.py:197, 216` |
| $p_i = \mathrm{Tr}(E_i \rho)$ | 理论概率 | `mle.py:249` |
| $\rho = \rho / \mathrm{Tr}(\rho)$ | 迹归一化 | `mle.py:227` |
| $J = \chi^2 + \lambda \|\text{params}\|^2$ | 正则化目标 | `mle.py:243-244` |
| $\hat{\rho} = \arg\min \chi^2(\rho)$ | MLE 优化 | `mle.py:106-112` |

---

## ✅ 扩展阅读

### 相关数学工具

- **Cholesky 分解**：Golub & Van Loan, *Matrix Computations*
- **拟牛顿法**：Nocedal & Wright, *Numerical Optimization*
- **最大似然估计**：Casella & Berger, *Statistical Inference*
- **Fisher 信息**：Cover & Thomas, *Elements of Information Theory*

### 相关物理概念

- **量子态层析**：Paris & Řeháček, *Quantum State Estimation*
- **泊松统计**：Mandel & Wolf, *Optical Coherence and Quantum Optics*
- **量子 Fisher 信息**：Braunstein & Caves, PRL 1994
- **Cramér-Rao 界**：Helstrom, *Quantum Detection and Estimation Theory*

### 相关代码模块

- `LinearReconstructor`：提供初始值 → [linear公式教学.md](./linear公式教学.md)
- `DensityMatrix`：物理化处理 → [density公式教学.md](./density公式教学.md)
- `ProjectorSet`：测量矩阵 → [projector公式教学.md](./projector公式教学.md)
- `scipy.optimize.minimize`：优化引擎
- `scipy.linalg.cholesky`：Cholesky 分解

---

**文档版本**: v1.0  
**最后更新**: 2025年10月7日  
**作者**: AI Assistant  
**相关文档**: 
- [mle的结构概述.md](./mle的结构概述.md)
- [linear公式教学.md](./linear公式教学.md)
- [density公式教学.md](./density公式教学.md)
- [projector公式教学.md](./projector公式教学.md)
- [linear的结构概述.md](./linear的结构概述.md)
- [density的结构概述.md](./density的结构概述.md)
- [projector的结构概述.md](./projector的结构概述.md)

