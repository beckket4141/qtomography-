from __future__ import annotations

"""非 POVM 测量设计：基于标准基和组合基的信息完备测量集合。

该设计生成 n² 个投影算符：
- 前 n 个：标准基 |0>, |1>, ..., |n-1>
- 后续：组合基 (|i> + |j>)/√2 和 (|i> - i|j>)/√2

这是信息完备的（n² 个测量足以重构 n×n 密度矩阵），但不是量子完备的（非 POVM），
即所有投影算符的和不等于单位矩阵 ∑E_i ≠ I。
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class NoPOVMDesign:
    """非 POVM 测量设计数据类。
    
    该设计使用标准基和组合基生成 n² 个投影算符：
    - 前 n 个：标准基 |0>, |1>, ..., |n-1>
    - 后续：组合基 (|i> + |j>)/√2 和 (|i> - i|j>)/√2
    
    这是信息完备的但不是量子完备的（非 POVM），
    意味着所有投影算符的和不等于单位矩阵。
    
    属性:
        dimension: 希尔伯特空间维度 n
        projectors: (n², n, n) 投影算符数组
        groups: (n²,) 分组标识，全部为 0（单组模式）
        measurement_matrix: (n², n*n) 测量矩阵（展平的投影算符）
    """

    dimension: int
    projectors: np.ndarray  # (n², d, d) 投影算符矩阵
    groups: np.ndarray      # (n²,) 分组标识，全部为 0（单组）
    measurement_matrix: np.ndarray  # (n², d*d) 测量矩阵


def build_nopovm_projectors(dimension: int) -> NoPOVMDesign:
    """构建非 POVM 测量设计。
    
    根据 MATLAB 代码 `generate_projectors_and_operators.m` 实现。
    生成 n² 个投影算符，由标准基和组合基组成。
    
    该设计是信息完备的（n² 个测量足以重构 n×n 密度矩阵），
    但不是量子完备的（∑E_i ≠ I），因此是非 POVM 测量集合。
    
    测量基的构成：
    1. 标准基：|0>, |1>, ..., |n-1>（共 n 个）
    2. 组合基：对于所有满足 i < j 的配对 (i, j)：
       - (|i> + |j>)/√2
       - (|i> - i|j>)/√2
    
    参数:
        dimension: 希尔伯特空间维度 n（必须 >= 2）
        
    返回:
        NoPOVMDesign，包含：
        - projectors: (n², n, n) 投影算符数组
        - groups: (n²,) 分组数组，全部为 0（单组模式）
        - measurement_matrix: (n², n*n) 展平的投影算符矩阵
        
    异常:
        ValueError: 当 dimension < 2 时抛出
        
    注意:
        MATLAB 代码使用 1-based 索引，Python 使用 0-based 索引。
        MATLAB 的 for i=1:n-1, j=i+1:n 对应 Python 的 for i in range(d-1), j in range(i+1, d)。
        但基态索引直接对应，无需偏移（MATLAB 注释中的 |i-1> 对应 Python 的 |i>）。
    """
    d = int(dimension)
    if d < 2:
        raise ValueError("维度必须 >= 2")

    bases = []
    norm = 1.0 / np.sqrt(2.0)  # 归一化因子 1/√2

    # 1. 标准基态 |0>, |1>, ..., |n-1>
    # 对应 MATLAB: for i = 0:n-1, basis(i+1) = 1
    for i in range(d):
        basis = np.zeros(d, dtype=complex)
        basis[i] = 1.0
        bases.append(basis)

    # 2. 组合基态：(|i> + |j>)/√2 和 (|i> - i|j>)/√2
    # 对应 MATLAB: for i = 1:n-1, for j = i+1:n
    # MATLAB 注释写的是 |i-1> 和 |j-1>，但实际代码使用的是索引 i 和 j
    # 由于 MATLAB 是 1-based 索引，所以实际对应 Python 的 |i> 和 |j>（0-based）
    for i in range(d - 1):
        for j in range(i + 1, d):
            # 组合基态: (|i> + |j>)/√2
            # 对应 MATLAB: basis_plus(i) = 1, basis_plus(j) = 1
            basis_plus = np.zeros(d, dtype=complex)
            basis_plus[i] = norm
            basis_plus[j] = norm
            bases.append(basis_plus)

            # 组合基态: (|i> - i|j>)/√2
            # 对应 MATLAB: basis_minus_i(i) = 1, basis_minus_i(j) = -1i
            basis_minus_i = np.zeros(d, dtype=complex)
            basis_minus_i[i] = norm
            basis_minus_i[j] = -1j * norm
            bases.append(basis_minus_i)

    # 3. 将基态转换为投影算符 P_i = |ψ_i><ψ_i|
    # 对应 MATLAB: projectors{i} = bases{i} * bases{i}'
    projectors = []
    for basis in bases:
        P = np.outer(basis, basis.conj())
        projectors.append(P)

    # 4. 堆叠为数组并构建测量矩阵
    projectors_arr = np.stack(projectors, axis=0)  # (n², n, n)
    groups_arr = np.zeros(len(projectors_arr), dtype=int)  # 单组模式（全部为 0）
    meas = projectors_arr.reshape(projectors_arr.shape[0], -1)  # (n², n*n)

    return NoPOVMDesign(
        dimension=d,
        projectors=projectors_arr,
        groups=groups_arr,
        measurement_matrix=meas
    )
