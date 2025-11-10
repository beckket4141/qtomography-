# 📘 DensityMatrix 程序中的数学与物理公式讲解

> 以下内容按 **概念 → 公式 → 物理意义 → 代码对应位置** 顺序讲解，帮助你把程序背后的量子力学逻辑完全吃透。

---

## 🌕 一、密度矩阵的基本定义与物理条件

### 1. 定义

在量子力学中，一个系统的状态可以由 **密度矩阵（Density Matrix）** 表示：

$$
\rho = \sum_i p_i |\psi_i\rangle \langle \psi_i|
$$

其中：

* $|\psi_i\rangle$：可能出现的纯态
* $p_i$：对应的概率，满足 $p_i \ge 0, \sum_i p_i = 1$

如果系统是纯态 $|\psi\rangle$，那么：

$$
\rho = |\psi\rangle \langle \psi|
$$

此时 $\rho$ 是一个 **秩为 1** 的矩阵（只有一个特征值为 1）。

---

### 2. 物理条件（密度矩阵必须满足）

一个矩阵要能代表真实的量子态，它必须满足三条 **物理约束**：

| 条件 | 数学表达 | 物理意义 |
|------|---------|----------|
| **Hermitian（厄米）** | $\rho = \rho^\dagger$ | 密度矩阵的可观测性（结果为实数） |
| **正半定性（PSD）** | $\forall |\phi\rangle, \langle\phi|\rho|\phi\rangle \ge 0$ | 概率非负 |
| **归一化** | $\mathrm{Tr}(\rho) = 1$ | 总概率为 1 |

在代码中，对应三个方法：

```python
is_hermitian()
is_positive_semidefinite()
is_normalized()
```

---

## 🌕 二、纯度 (Purity)

**公式：**

$$
\text{Purity} = \operatorname{Tr}(\rho^2)
$$

**物理意义：**

* 纯态：$\text{Purity} = 1$
* 混态：$\text{Purity} < 1$
* 最大混合态（完全无信息）：$\text{Purity} = 1/d$，其中 $d$ 是维度

**代码对应：**

```python
@property
def purity(self):
    return float(np.real(np.trace(self._matrix @ self._matrix)))
```

即直接计算 $\mathrm{Tr}(\rho^2)$。

---

## 🌕 三、特征分解与物理化处理

任何厄米矩阵都可以 **特征分解（Spectral Decomposition）** 为：

$$
\rho = V \Lambda V^\dagger
$$

其中：

* $V$：特征向量矩阵
* $\Lambda = \mathrm{diag}(\lambda_1, \lambda_2, \ldots, \lambda_d)$：特征值对角阵

代码中对应：

```python
eigenvals, eigenvecs = eigh(hermitian_matrix)
```

然后进行 "物理化" 处理：

1. **负特征值裁剪（消除数值误差）：**
   
   $$
   \lambda_i = \begin{cases}
   0, & \lambda_i < \text{tol} \\
   \lambda_i, & \text{otherwise}
   \end{cases}
   $$

2. **归一化（迹为 1）：**
   
   $$
   \sum_i \lambda_i = 1
   $$

3. **重构密度矩阵：**
   
   $$
   \rho_{\text{phys}} = V \, \mathrm{diag}(\lambda_i) \, V^\dagger
   $$

---

## 🌕 四、矩阵平方根（Matrix Square Root）

**定义：**

$$
A^{1/2} = V \, \mathrm{diag}(\sqrt{\lambda_i}) \, V^\dagger
$$

其中 $A = V \, \mathrm{diag}(\lambda_i) \, V^\dagger$。

> 💡 这是"通过谱分解定义矩阵函数"的标准做法。

代码对应：

```python
eigenvals, eigenvecs = eigh(matrix)
sqrt_matrix = eigenvecs @ np.diag(np.sqrt(eigenvals)) @ eigenvecs.conj().T
```

这一步在计算 **保真度（Fidelity）** 时非常关键。

---

## 🌕 五、保真度 (Fidelity)

量子态保真度衡量两个态的"相似程度"。

### 公式（Uhlmann Fidelity）：

$$
F(\rho_1, \rho_2) = \left[\operatorname{Tr}\!\left(\sqrt{\sqrt{\rho_1} \, \rho_2 \, \sqrt{\rho_1}}\right)\right]^2
$$

**物理意义：**

* $F = 1$：完全相同的量子态
* $F = 0$：完全正交的量子态
* $0 < F < 1$：部分重叠（量子态相似度）

**代码实现：**

```python
sqrt_rho1 = self.matrix_square_root()
intermediate = sqrt_rho1 @ other.matrix @ sqrt_rho1
sqrt_intermediate = self.matrix_square_root(intermediate)
fidelity_val = np.real(np.trace(sqrt_intermediate)) ** 2
```

结构对应：

$$
\rho_1^{1/2} \, \rho_2 \, \rho_1^{1/2}
\quad \xrightarrow{\text{取平方根}} \quad
\sqrt{\sqrt{\rho_1} \, \rho_2 \, \sqrt{\rho_1}}
\quad \xrightarrow{\text{取迹与平方}} \quad
F
$$

---

## 🌕 六、最大混合态与纯态构造

### 1️⃣ 最大混合态

$$
\rho_{\text{mixed}} = \frac{I}{d}
$$

表示"系统在所有状态上概率相等"，即完全无信息。

代码：

```python
np.eye(dimension) / dimension
```

---

### 2️⃣ 纯态

$$
\rho_{\text{pure}} = |\psi\rangle \langle \psi|
$$

代码：

```python
matrix = np.outer(state_vector, state_vector.conj())
```

---

## 🌕 七、Hermitian 对称化（数值稳定性）

计算时由于浮点误差，矩阵可能略微偏离 Hermitian。

通过对称化修正：

$$
A_H = \frac{A + A^\dagger}{2}
$$

把矩阵强制投影回 Hermitian 空间。

代码：

```python
hermitian_matrix = (matrix + matrix.conj().T) / 2
```

---

## 🌕 八、迹归一化 (Trace Normalization)

确保最终密度矩阵满足 $\mathrm{Tr}(\rho) = 1$：

$$
\rho \leftarrow \frac{\rho}{\operatorname{Tr}(\rho)}
$$

代码：

```python
rho_physical /= np.trace(rho_physical)
```

---

## 🌕 九、容差与负特征值裁剪（数值物理的经验法）

在数值计算中，Hermitian 矩阵的特征值可能出现微小负数：

$$
\lambda_i = -10^{-15}
$$

这是浮点舍入误差，不代表物理上负概率。

因此设置容差阈值：

$$
\text{tol} = \max(\text{用户设置}, 10^{-12})
$$

并裁剪：

$$
\lambda_i = \max(\lambda_i, 0)
$$

代码对应：

```python
eigenvals = np.where(eigenvals < tol, 0.0, eigenvals)
```

---

## 🌕 十、典型例子：纯度与保真度直觉

### 场景 1: 同一纯态

$$
\begin{aligned}
\rho_1 &= |0\rangle\langle0| \\
\rho_2 &= |0\rangle\langle0| \\
F &= 1 \\
\mathrm{Purity} &= 1
\end{aligned}
$$

**意义**：完全相同的纯态，保真度为 1。

---

### 场景 2: 正交纯态

$$
\begin{aligned}
\rho_1 &= |0\rangle\langle0| \\
\rho_2 &= |1\rangle\langle1| \\
F &= 0 \\
\mathrm{Purity} &= 1
\end{aligned}
$$

**意义**：两个正交的纯态，保真度为 0（完全不重叠）。

---

### 场景 3: 混合态 vs 纯态

$$
\begin{aligned}
\rho_1 &= \frac{I}{2} \quad \text{(最大混合态)} \\
\rho_2 &= |0\rangle\langle0| \quad \text{(纯态)} \\
F &= \frac{1}{2} \\
\mathrm{Purity}(\rho_1) &= \frac{1}{2}, \quad \mathrm{Purity}(\rho_2) = 1
\end{aligned}
$$

**意义**：混合态与纯态的重叠程度为 50%。

---

### 场景 4: 最大混合态 vs 自己

$$
\begin{aligned}
\rho_1 &= \frac{I}{2} \\
\rho_2 &= \frac{I}{2} \\
F &= 1 \\
\mathrm{Purity} &= \frac{1}{2}
\end{aligned}
$$

**意义**：同一个混合态，保真度为 1，但纯度小于 1。

---

## 🌕 十一、程序中数学流程总图

```
输入矩阵 M
  ↓
Hermitian 化： (M + M†)/2
  ↓
谱分解： M = V Λ V†
  ↓
特征值裁剪： λ_i < tol → 0
  ↓
归一化： Σλ_i = 1
  ↓
重构密度矩阵： ρ = V diag(λ_i) V†
  ↓
可选：再次 Hermitian + 迹归一
  ↓
可计算指标：
      ├─ Purity = Tr(ρ²)
      ├─ Fidelity = [Tr(√(√ρ₁ ρ₂ √ρ₁))]²
      └─ Eigenvalues / Phase / Amplitude
```

---

## ✅ 总结

> 这段程序的数学核心，是围绕密度矩阵三大物理约束构建的一套稳定的"谱投影"工具集。

### 核心操作

| 操作 | 公式 | 作用 |
|------|------|------|
| Hermitian 对称化 | $(A + A^\dagger)/2$ | 消除浮点误差 |
| 特征分解 | $A = V \Lambda V^\dagger$ | 提取特征值和特征向量 |
| 负谱裁剪 | $\lambda_i \ge 0$ | 保证正半定性 |
| 迹归一化 | $\mathrm{Tr}(\rho) = 1$ | 保证概率归一 |
| 纯度 | $\mathrm{Tr}(\rho^2)$ | 衡量量子态的纯度 |
| 保真度 | $F = [\mathrm{Tr}(\sqrt{\sqrt{\rho_1}\rho_2\sqrt{\rho_1}})]^2$ | 衡量两个态的相似度 |

### 保证结果

这些操作保证：**任何输入矩阵都能被"修正"为一个真实、可观测、物理合法的量子态。**

---

## 📚 扩展阅读

如果你希望了解：

1. **这些公式在量子层析中如何使用？**
   - 测量概率与密度矩阵的关系：$p_i = \mathrm{Tr}(E_i \rho)$
   - MLE/HMLE 在重构过程中的联系

2. **更多量子信息理论基础？**
   - von Neumann 熵
   - Schmidt 分解
   - 纠缠度量

可以参考项目中的其他文档或相关量子信息学教材。

---

**文档版本**: v1.1  
**最后更新**: 2025年10月7日  
**作者**: AI Assistant
