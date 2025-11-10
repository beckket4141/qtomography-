# 迭代 ML 量子态层析（RρR 算法）：代码实现与说明

基于文献（Řeháček, Hradil, and Ježek, 2001）的核心原理，以下整理**RρR 算法**（迭代最大似然算法）的完整实现方案，包含代码文件结构、函数详解、运行步骤及非 POVM 测量处理逻辑，优化排版以提升可读性。

## 一、算法核心背景

RρR 算法是实现迭代 ML 量子态层析的简化且高效的方案，核心思想是**通过迭代应用 R 算符优化密度矩阵**，直到收敛。其优势在于：



* 推导不依赖 “测量算符和为单位算符（$\sum \hat{M}_j = \hat{I}$）”，可完美处理 “不完备检测（非 POVM）” 场景；

* 迭代公式简洁，数值实现稳定，能保证重构态的物理有效性（半正定性、迹为 1）。

### 核心迭代公式



1. **密度矩阵更新**：$\rho_{k+1} = \mathcal{N} ( R_k \rho_k R_k )$

   其中 $\mathcal{N}$ 为归一化算符（除以矩阵的迹，确保 $\text{Tr}(\rho_{k+1}) = 1$）。

2. **R 算符定义**：$R_k = \sum_j \left( \frac{n_j}{p_j^{(k)}} \right) \hat{M}_j$

* $\{\hat{M}_j\}$：测量投影算符（非 POVM 场景下，$\sum \hat{M}_j \neq \hat{I}$）；

* $\{n_j\}$：每个投影算符对应的实验计数值（实测数据）；

* $p_j^{(k)} = \text{Tr}(\rho_k \hat{M}_j)$：当前猜测密度矩阵 $\rho_k$ 在 $\hat{M}_j$ 上的理论概率。

## 二、代码文件结构

需创建 2 个关联文件，放在同一目录下：



| 文件名                | 功能说明                                                        |
| ------------------ | ----------------------------------------------------------- |
| `nopovm_design.py` | （用户需提前准备）定义`NoPOVMDesign`类，生成非 POVM 测量的投影算符 $\{\hat{M}_j\}$ |
| `tomo_ml.py`       | （下方提供）实现 RρR 算法，包含迭代重构、实验模拟、保真度计算等核心功能                      |

## 三、完整代码实现（tomo\_ml.py）



```
import numpy as np
from scipy.linalg import sqrtm
# 导入非POVM测量设计（需确保nopovm_design.py在同一目录）
from nopovm_design import NoPOVMDesign, build_nopovm_projectors


def iterative_ml_tomo(
    design: NoPOVMDesign,
    counts: np.ndarray,
    max_iter: int = 5000,
    tol: float = 1e-9
) -> np.ndarray:
    """
    使用RρR算法（迭代最大似然）重构量子态密度矩阵
    
    基于Řeháček, Hradil, and Ježek (2001)原理，自动处理非POVM（不完备检测）情况。

    参数:
        design: NoPOVMDesign对象，包含：
                - .projectors: (n_operators, d, d) 数组，存储所有投影算符
                - .dimension: 整数，量子系统的希尔伯特空间维度d
        counts: (n_operators,) 数组，每个投影算符对应的实验计数值
        max_iter: 最大迭代次数（默认5000）
        tol: 收敛判据（两次迭代间ρ的Frobenius范数差，默认1e-9）

    返回:
        (d, d) 复数组，重构后的物理密度矩阵ρ（半正定、迹为1）
    """
    # 1. 提取测量算符与系统维度
    M_j = design.projectors  # 形状：(n_operators, d, d)
    d = design.dimension     # 系统维度（如量子比特d=2）
    n_j = counts             # 实验计数值（形状：(n_operators,)）
    epsilon = 1e-12          # 防止除零的极小值

    # 2. 初始化密度矩阵：完全混合态（物理有效，避免初始非物理解）
    rho = np.eye(d, dtype=complex) / d

    # 3. 迭代优化（RρR核心逻辑）
    for k in range(max_iter):
        rho_prev = rho  # 保存上一轮结果，用于收敛判断

        # (a) 计算当前ρ_k对应的理论概率 p_j = Tr(ρ_k · M_j)
        # 用np.einsum实现批量迹计算，索引解释：
        # 'il,jli->j' → 对每个j，计算 sum_i( sum_l( rho[il] * M_j[j][li] ) )
        p_j = np.einsum('il,jli->j', rho, M_j).real
        # 数值稳定处理：确保p_j不小于epsilon（避免后续除零）
        p_j_stable = np.maximum(p_j, epsilon)

        # (b) 计算R_k算符：sum_j (n_j / p_j_stable) * M_j
        r_j = n_j / p_j_stable  # 权重向量（形状：(n_operators,)）
        # 用np.einsum批量计算加权和，索引解释：
        # 'j,jil->il' → 对每个矩阵元素(il)，计算 sum_j( r_j[j] * M_j[j][il] )
        R = np.einsum('j,jil->il', r_j, M_j)

        # (c) RρR更新：未归一化的新密度矩阵
        rho_unnorm = R @ rho @ R

        # (d) 归一化：确保迹为1（物理态要求）
        trace_val = np.trace(rho_unnorm)
        if trace_val.real < epsilon:
            # 极端情况：迹接近0，重置为混合态（避免数值崩溃）
            rho = np.eye(d, dtype=complex) / d
        else:
            rho = rho_unnorm / trace_val

        # (e) 收敛判断：Frobenius范数差小于tol则停止
        error = np.linalg.norm(rho - rho_prev, 'fro')
        if error < tol:
            # print(f"迭代{k+1}次后收敛")
            break

    # 迭代达上限仍未收敛的警告
    if k == max_iter - 1:
        print(f"警告：已达最大迭代次数{max_iter}，可能未完全收敛")

    return rho


# ------------------------------
# 辅助函数1：模拟非POVM层析实验
# ------------------------------
def simulate_experiment(
    rho_true: np.ndarray,
    design: NoPOVMDesign,
    N_total: int
) -> np.ndarray:
    """
    模拟非POVM测量的实验数据（生成计数值）

    参数:
        rho_true: (d, d) 复数组，真实的量子态密度矩阵
        design: NoPOVMDesign对象，含测量投影算符
        N_total: 整数，总测量次数（所有投影算符的计数值之和）

    返回:
        (n_operators,) 数组，模拟的实验计数值
    """
    M_j = design.projectors
    d = design.dimension

    # 1. 计算未归一化的理论概率 p_j = Tr(rho_true · M_j)
    p_j = np.einsum('il,jli->j', rho_true, M_j).real
    p_j = np.maximum(p_j, 0)  # 数值稳定：确保概率非负

    # 2. 计算总和算符H = sum(M_j)，并归一化概率（非POVM关键步骤）
    H = np.sum(M_j, axis=0)
    total_prob = np.einsum('il,li->', rho_true, H).real  # Tr(rho_true · H)
    if total_prob <= 0:
        raise ValueError("总探测概率为0，无法模拟实验")
    p_j_renorm = p_j / total_prob  # 条件概率（确保sum(p_j_renorm) = 1）

    # 3. 用多项分布生成计数值（模拟真实实验的计数随机性）
    counts = np.random.multinomial(N_total, p_j_renorm)
    return counts


# ------------------------------
# 辅助函数2：计算两个密度矩阵的保真度
# ------------------------------
def calculate_fidelity(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """
    计算量子态保真度 F(rho1, rho2)，衡量重构态与真实态的相似度（取值0~1）

    公式：F(rho1, rho2) = [Tr( sqrt( sqrt(rho1) · rho2 · sqrt(rho1) ) )]^2
    """
    # 数值稳定：确保密度矩阵为厄米矩阵
    rho1 = (rho1 + rho1.conj().T) / 2
    rho2 = (rho2 + rho2.conj().T) / 2

    # 分步计算保真度
    sqrt_rho1 = sqrtm(rho1)
    fidelity_matrix = sqrtm(sqrt_rho1 @ rho2 @ sqrt_rho1)
    fidelity = np.trace(fidelity_matrix).real ** 2

    # 数值截断：避免因计算误差导致保真度略大于1
    return min(fidelity, 1.0)


# ------------------------------
# 运行示例：测试RρR算法
# ------------------------------
if __name__ == "__main__":
    # 1. 模拟参数设置
    DIMENSION = 2          # 系统维度（2=量子比特，可修改）
    N_TOTAL_COUNTS = 50000 # 总测量次数（越大，模拟数据越接近理论值）
    print(f"--- RρR算法模拟（d={DIMENSION}）---\n")

    # 2. 构建非POVM测量设计
    design = build_nopovm_projectors(DIMENSION)
    print(f"非POVM测量设计：共{design.projectors.shape[0]}个投影算符\n")

    # 3. 定义真实量子态（示例：随机纯态）
    psi = np.random.rand(DIMENSION) + 1j * np.random.rand(DIMENSION)
    psi = psi / np.linalg.norm(psi)  # 归一化纯态
    rho_true = np.outer(psi, psi.conj())  # 纯态对应的密度矩阵
    print("真实密度矩阵（rho_true）：")
    print(np.round(rho_true, 3), "\n")

    # 4. 模拟实验：生成计数值
    print(f"模拟实验（总计{N_TOTAL_COUNTS}次测量）...")
    counts = simulate_experiment(rho_true, design, N_TOTAL_COUNTS)
    print("前10个投影算符的模拟计数值：")
    print(counts[:10], "\n")

    # 5. 运行RρR算法重构密度矩阵
    print("开始迭代重构...")
    rho_recon = iterative_ml_tomo(design, counts)
    print("重构完成！\n")

    # 6. 结果验证：输出重构态与保真度
    print("重构密度矩阵（rho_recon）：")
    print(np.round(rho_recon, 3), "\n")

    fidelity = calculate_fidelity(rho_true, rho_recon)
    print("--- 重构结果评估 ---")
    print(f"保真度（Fidelity）：{fidelity * 100:.4f}%")
```

## 四、代码运行步骤



1. **准备依赖文件**

   将生成非 POVM 投影算符的代码（含`NoPOVMDesign`类和`build_nopovm_projectors`函数）保存为`nopovm_design.py`，与`tomo_ml.py`放在同一文件夹。

2. **运行代码**

   打开终端，切换到代码所在目录，执行命令：



```
python tomo\_ml.py
```



1. **输出说明**

   运行后将依次输出：

* 非 POVM 测量设计的投影算符数量；

* 真实密度矩阵（随机纯态）；

* 模拟实验的计数值（前 10 个）；

* 重构密度矩阵；

* 保真度（通常 > 99%，证明重构精度高）。

## 五、关键解析：RρR 算法如何处理非 POVM 测量？

非 POVM 测量的核心特点是 “投影算符和$H = \sum \hat{M}_j \neq \hat{I}$”，导致理论概率$\sum p_j = \text{Tr}(\rho H) \neq 1$，但 RρR 算法通过以下逻辑自然适配：



| 核心问题          | 算法处理机制                                                                                                 |
| ------------- | ------------------------------------------------------------------------------------------------------ |
| 1. 理论概率不归一    | 算法不要求$\sum p_j = 1$，仅通过$R$算符的权重（$n_j / p_j$）匹配 “计数值比例”，无需提前归一化$p_j$；                                   |
| 2. 无需依赖 H 算符  | 重构过程中不计算$H = \sum \hat{M}_j$，仅通过迭代寻找 “$R\rho = \rho$” 的不动点，自动收敛到物理态；                                   |
| 3. 实验模拟需 H 算符 | 仅`simulate_experiment`函数需$H$：将理论概率$p_j$归一化为条件概率（$p_j / \text{Tr}(\rho H)$），确保从多项分布抽样的合理性，但重构算法本身无需$H$。 |

简言之，RρR 算法通过 “概率比例匹配” 和 “迭代不动点优化”，绕过了非 POVM 测量的 “闭包缺失” 问题，始终能输出半正定、迹为 1 的物理态。

> （注：文档部分内容可能由 AI 生成）