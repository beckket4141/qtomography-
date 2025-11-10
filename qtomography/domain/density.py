"""
密度矩阵类 - 量子态层析中的核心数据结构

对应MATLAB函数：
- makephysical.m -> ensure_physical()
- 密度矩阵的基本操作和验证

重构说明（2024）：
- 新增 enforce 策略：within_tol（默认）、project、none
- 职责分离：数值稳定性处理 vs 强制物理投影
- 问题透明：显著非物理输入发出警告，不掩盖外部算法问题
- 诊断工具：physical_diagnostics() 提供详细物理性指标
- 向后兼容：现有代码无需修改
"""

import numpy as np
import warnings
from typing import Optional, Union, Tuple, Literal
from scipy.linalg import eigh

'''
1. 当前误差来源（与现实现对齐）
主要误差来源：
    1) 特征值分解（scipy.linalg.eigh）：即便在 Hermitian 矩阵上，仍存在浮点舍入误差。
       典型量级约 ~1e-15；在谱近简并或病态情况下可能放大到 ~1e-12。

    2) 重构与矩阵乘法的累计误差：V @ diag(λ) @ V† 以及保真度/平方根中的多次乘法会累积误差，
       常见量级约 ~1e-12 到 ~1e-9，取决于矩阵条件数与维度。

    3) Hermitian 对称化投影：(A + A†) / 2 将非厄米噪声压回 Hermitian 子空间，
       本身引入的改动不超过原噪声量级，但会改变个别元素的实/虚部分布。

    4) 特征值裁剪与容差策略：使用 tol = max(self.tolerance, 1e-12) 并将小于 tol 的特征值置 0，
       可抑制 -1e-19 级的微负值；同时可能将极小正特征值也钳为 0，带来 ≤ 1e-12 量级的谱稀疏偏置。

    5) 归一化漂移与再归一化：重构与对称化后再次归一化以确保 Tr(ρ)=1，
       会把前述微小误差分摊至各本征分量，典型影响在 ~1e-12。

    6) 多次算子调用的误差复合：matrix_square_root 与 fidelity 中多次 eigh 与乘法叠加误差；
       在常见低维（2~4）场景下整体仍表现稳定。
'''

class DensityMatrix:
    """
    密度矩阵类，封装量子态层析中的密度矩阵操作
    
    密度矩阵必须满足的物理条件：
    1. Hermitian性：ρ = ρ†
    2. 正半定性：所有特征值 ≥ 0
    3. 归一化：Tr(ρ) = 1
    """
    
    # ============================================================================
    # 1. 类定义和类属性
    # ============================================================================
    
    # 类级默认参数（子类可覆盖)容差敏感度调整系数
    k_factor: float = 50.0
    
    # ============================================================================
    # 2. 构造与初始化
    # ============================================================================
    
    def __init__(self, matrix: np.ndarray, *, tolerance: float = 1e-10, 
                 enforce: Literal["within_tol", "project", "none"] = "within_tol",
                 strict: bool = False, warn: bool = True):
        """
        初始化密度矩阵
        
        Args:
            matrix: 密度矩阵数据，必须是方阵
            tolerance: 数值比较的容差
            enforce: 物理化策略
                - "within_tol": 容差内物理化（默认，数值稳定性处理）
                - "project": 强制物理投影（处理所有非物理输入）
                - "none": 不处理（调试模式，保持原始输入）
            strict: 是否对显著非物理输入抛出异常
            warn: 是否对显著非物理输入发出警告
        """
        # 三级守卫： np.array 只能创建矩形数组，而 np.ndarray 在这里主要是作为类型标识符使用,np.ndarray 有且仅在判断对象为 np.array 的时候才 True
        # 1) 一级守卫:显式类型守卫：提前拒绝明显无效的输入（字符串/字节串、标量）
        if isinstance(matrix, (str, bytes)) or np.isscalar(matrix):
            raise TypeError("输入必须是numpy数组")

        # 2) 二级守卫:数组化时的异常归一化：将底层 TypeError/ValueError 统一映射为 TypeError
        try:
            self._matrix = np.array(matrix, dtype=complex)  # 弱私有属性
        except (TypeError, ValueError) as e:
            raise ValueError(f"输入数据无法转换为有效的密度矩阵: {e}")
        #NumPy, SciPy, Pandas 等都使用弱私有； 测试的时候可以方便地检查内部状态
        #也可以通过在公共接口里面返回的是self._matrix.copy()来保护原始数据

        # 3) 三级守卫,校验经过np.array转换(张量数组)后的self._matrix是否是1.矩阵(2维张量)2.方阵3.非空
        self._validate_input() # 目的:只要创建了DensityMatrix类就会自动先执行验证输入!

        # 设置参数
        self.tolerance = tolerance
        self.enforce = enforce
        self.strict = strict
        self.warn = warn
        
        # 根据策略处理矩阵
        if enforce == "none":
            self._matrix = self._matrix  # 不处理，保持原始输入
        elif enforce == "within_tol":
            self._matrix = self._sanitize_within_tol(self._matrix)
        elif enforce == "project":
            self._matrix = self.__class__.project_to_physical(self._matrix, tolerance=tolerance)
        else:
            raise ValueError(f"Unsupported enforce mode: {enforce!r}")
        '''
        # 如果后续计算破坏了物理性，需要手动修复
        dm._matrix = some_computation_result
        dm.sanitize_within_tol()  # 手动调用公共方法
        # 或者
        dm._matrix = dm._make_physical_matrix(dm._matrix)  # 直接调用核心方法
        '''

    def _validate_input(self) -> None:
        """验证输入矩阵的基本格式"""
        if not isinstance(self._matrix, np.ndarray):
            raise TypeError("输入必须是numpy数组")
        
        if self._matrix.ndim != 2:
            raise ValueError("密度矩阵必须是2维张量(矩阵)")
        
        if self._matrix.shape[0] != self._matrix.shape[1]:
            raise ValueError("密度矩阵必须是方阵")
        
        if self._matrix.shape[0] == 0:
            raise ValueError("密度矩阵不能为空")
    
    # ============================================================================
    # 3. 属性访问器（Properties）
    # ============================================================================
    
    @property
    def matrix(self) -> np.ndarray:
        """获取密度矩阵数据"""
        return self._matrix.copy()
    
    @property
    def dimension(self) -> int:
        """获取密度矩阵的维度"""
        return self._matrix.shape[0]
    
    @property
    def trace(self) -> complex:
        """计算密度矩阵的迹"""
        return np.trace(self._matrix)
    
    @property
    def purity(self) -> float:
        """计算密度矩阵的纯度 Tr(ρ²)"""
        return float(np.real(np.trace(self._matrix @ self._matrix)))
    
    @property
    def eigenvalues(self) -> np.ndarray:
        """获取密度矩阵的特征值（按降序排列）"""
        # 确保 Hermitian 性
        H = (self._matrix + self._matrix.conj().T) / 2
        
        # 统一特征值分解（只取特征值）
        eigenvals, _ = type(self)._heig(H)
        
        # 自适应容差
        tol = self._auto_tol_inst(H)
        
        # 裁剪容差内的负特征值
        eigenvals = np.where(eigenvals < tol, 0.0, eigenvals)
        
        # 降序排列
        return np.sort(eigenvals)[::-1]
    
    # ============================================================================
    # 4. 物理性检查方法
    # ============================================================================
    
    def is_hermitian(self, tol: Optional[float] = None, *, use_auto: bool = True) -> bool:
        """
        检查密度矩阵是否为Hermitian矩阵
        
        使用相对残差判断：||A - A†|| / (||A|| + eps) <= tol_rel
        
        Args:
            tol: 相对阈值（外部定义），为None时使用默认1e-6
            use_auto: 是否启用自适应容差（对Hermitian性检查通常无意义，此处忽略）
            
        Returns:
            是否为Hermitian矩阵
        """
        A = self._matrix
        rel = np.linalg.norm(A - A.conj().T) / (np.linalg.norm(A) + 1e-30)
        tol_rel = 1e-6 if tol is None else float(tol)
        # 对厄米性，use_auto 一般没有意义（自适应与维度/范数相关的绝对阈值不适用于相对残差），此处忽略 use_auto
        return bool(rel <= tol_rel)
    
    def is_positive_semidefinite(self, tol: Optional[float] = None, *, use_auto: bool = True) -> bool:
        """
        检查密度矩阵是否为正半定矩阵
        
        判断最小特征值：min_eig(H) >= -tol_eff
        
        Args:
            tol: 绝对阈值（外部定义），为None时采用自适应容差
            use_auto: 是否启用自适应容差，若True则tol_eff = max(tol, auto_tol)
            
        Returns:
            是否为正半定矩阵
        """
        H = (self._matrix + self._matrix.conj().T) / 2
        vals, _ = type(self)._heig(H)
        # 绝对阈值
        tol_eff = 0.0 if tol is None else float(tol)
        if use_auto:
            tol_eff = max(tol_eff, self._auto_tol_inst(H))
        elif tol is None:
            # 外部没给，但调用者禁用了自适应，为了避免不确定，退回自适应
            tol_eff = self._auto_tol_inst(H)
        return bool(vals.min() >= -tol_eff)
    
    def is_normalized(self, tol: Optional[float] = None, *, use_auto: bool = True) -> bool:
        """
        检查密度矩阵是否归一化（迹为1）
        
        判断迹的偏差：|Tr(ρ) - 1| <= tol_eff
        
        Args:
            tol: 绝对阈值（外部定义），为None时采用自适应容差
            use_auto: 是否启用自适应容差，若True则tol_eff = max(tol, auto_tol)
            
        Returns:
            是否归一化
        """
        H = (self._matrix + self._matrix.conj().T) / 2
        tr_real = float(np.trace(self._matrix).real)
        tol_eff = 0.0 if tol is None else float(tol)
        if use_auto:
            tol_eff = max(tol_eff, self._auto_tol_inst(H))
        elif tol is None:
            tol_eff = self._auto_tol_inst(H)
        return bool(abs(tr_real - 1.0) <= tol_eff)
    
    def is_physical(self, tol: Optional[float] = None, *, use_auto: bool = True) -> bool:
        """
        检查密度矩阵是否满足所有物理条件（综合检查）
        
        同时检查：min_eig(H) >= -tol_eff 且 |Tr(ρ)-1| <= tol_eff
        
        Args:
            tol: 绝对阈值（外部定义），为None时采用自适应容差
            use_auto: 是否启用自适应容差，若True则tol_eff = max(tol, auto_tol)
            
        Returns:
            是否满足所有物理条件
        """
        H = (self._matrix + self._matrix.conj().T) / 2
        vals, _ = type(self)._heig(H)
        tr_real = float(np.trace(self._matrix).real)

        tol_eff = 0.0 if tol is None else float(tol)
        if use_auto:
            tol_eff = max(tol_eff, self._auto_tol_inst(H))
        elif tol is None:
            tol_eff = self._auto_tol_inst(H)

        return bool((vals.min() >= -tol_eff) and (abs(tr_real - 1.0) <= tol_eff))
    
    def physical_diagnostics(self, tol: Optional[float] = None, *, use_auto: bool = True) -> dict:
        """
        返回密度矩阵的物理性诊断信息
        
        Args:
            tol: 绝对阈值（外部定义），为None时采用自适应容差
            use_auto: 是否启用自适应容差，若True则tol_eff = max(tol, auto_tol)
            
        Returns:
            包含物理性指标的字典
        """
        H = (self._matrix + self._matrix.conj().T) / 2
        vals, _ = type(self)._heig(H)
        
        # 使用与检查方法一致的容差处理逻辑
        tol_eff = 0.0 if tol is None else float(tol)
        if use_auto:
            tol_eff = max(tol_eff, self._auto_tol_inst(H))
        elif tol is None:
            tol_eff = self._auto_tol_inst(H)
        
        # Hermitian性相对残差
        herm_res = np.linalg.norm(self._matrix - self._matrix.conj().T) / (np.linalg.norm(self._matrix) + 1e-30)
        
        return {
            "min_eig": float(vals.min()),
            "max_eig": float(vals.max()),
            "trace": float(np.trace(self._matrix).real),
            "trace_imag": float(np.trace(self._matrix).imag),
            "hermitian_residual": float(herm_res),
            "hermitian_residual_abs": float(np.linalg.norm(self._matrix - self._matrix.conj().T)),
            "tol_eff": float(tol_eff),
            "is_hermitian": self.is_hermitian(tol=tol, use_auto=use_auto),
            "is_positive_semidefinite": self.is_positive_semidefinite(tol=tol, use_auto=use_auto),
            "is_normalized": self.is_normalized(tol=tol, use_auto=use_auto),
            "is_physical": self.is_physical(tol=tol, use_auto=use_auto),
            "enforce_mode": self.enforce
        }
    
    # ============================================================================
    # 5. 物理化处理方法
    # ============================================================================
    
    def sanitize_within_tol(self) -> np.ndarray:
        """
        容差内物理化处理（数值稳定性处理）
        
        
        通过以下步骤确保物理性：
        1. 特征值分解
        2. 将容差内负特征值设为0
        3. 重新归一化使迹为1
        4. 确保Hermitian性
        5. 添加数值稳定性处理
        """
        self._matrix = self._sanitize_within_tol(self._matrix)
        return self._matrix
    
    def ensure_physical(self) -> np.ndarray:
        """向后兼容的别名方法（已弃用）"""
        import warnings
        warnings.warn(
            "ensure_physical is deprecated, use sanitize_within_tol",
            DeprecationWarning,
            stacklevel=2
        )
        return self.sanitize_within_tol()
    
    @classmethod
    def project_to_physical(cls, matrix: np.ndarray, *, tolerance: float = 1e-10, 
                           return_diag: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, dict]]:
        """
        强制投影到物理密度矩阵空间。
        
        将任意矩阵投影到满足物理约束的密度矩阵：
        - Hermitian: ρ = ρ†
        - 正半定: 所有特征值 ≥ 0
        - 归一化: Tr(ρ) = 1
        
        Args:
            matrix: 输入矩阵
            tolerance: 数值容差
            return_diag: 是否返回诊断信息
            
        Returns:
            物理化的密度矩阵，或 (矩阵, 诊断信息) 元组
        """
        mat = np.asarray(matrix, dtype=complex)
        
        # Hermitian 化
        H = (mat + mat.conj().T) / 2
        
        # 统一特征值分解
        vals, vecs = cls._heig(H)
        
        # 强制：所有负特征值→0
        vals = np.where(vals < 0.0, 0.0, vals)
        
        # 自适应容差（使用类方法）
        tol = cls._auto_tol(H, tolerance)
        
        # 归一化
        s = float(vals.sum())
        vals = (np.ones_like(vals)/len(vals)) if s <= tol else (vals/s)
        
        # 列缩放重构（避免 np.diag 临时阵）
        rho = (vecs * vals) @ vecs.conj().T
        rho = (rho + rho.conj().T) / 2
        
        # 最终归一化
        tr = float(np.trace(rho).real)
        rho = (np.eye(len(vals), dtype=complex)/len(vals)) if tr <= 0 else (rho / tr)
        
        if not return_diag:
            return rho
            
        # 返回诊断信息（统一使用类方法）
        vals_in, _ = cls._heig(H)
        min_eig_in = float(vals_in.min())
        return rho, {
            "min_eig_in": min_eig_in,
            "tol": float(tol),
            "projection_applied": min_eig_in < 0
        }
    
    # ============================================================================
    # 6. 数值计算方法
    # ============================================================================
    
    def fidelity(self, other: 'DensityMatrix') -> float:
        """
        计算与另一个密度矩阵的保真度
        
        对应MATLAB的fidelity.m函数
        公式：F(ρ₁, ρ₂) = [Tr(√(√ρ₁ ρ₂ √ρ₁))]²
        """
        if not isinstance(other, DensityMatrix):
            raise TypeError("输入必须是DensityMatrix类型")
        
        if self.dimension != other.dimension:
            raise ValueError("两个密度矩阵的维度必须相同")
        
        # 计算 √ρ₁
        sqrt_rho1 = self.matrix_square_root()
        
        # 计算 √ρ₁ ρ₂ √ρ₁
        intermediate = sqrt_rho1 @ other.matrix @ sqrt_rho1
        
        # 计算 √(√ρ₁ ρ₂ √ρ₁)
        sqrt_intermediate = self.matrix_square_root(intermediate)
        
        # 计算迹的平方
        fidelity_val = np.real(np.trace(sqrt_intermediate)) ** 2
        
        # 精确到小数点后8位（对应MATLAB的round(F, 8)）
        return round(float(fidelity_val), 8)
    
    def matrix_square_root(self, matrix: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算矩阵的平方根
        
        对应MATLAB的matrix_square_root.m函数
        使用特征值分解方法
        """
        if matrix is None:
            matrix = self._matrix
        
        # 先进行Hermitian 化以减小数值误差
        hermitian_matrix = (matrix + matrix.conj().T) / 2

        # 特征值分解（统一封装）
        eigenvals, eigenvecs = type(self)._heig(hermitian_matrix)
        # 自适应容差
        tol = self._auto_tol_inst(hermitian_matrix)
        # 裁剪容差内本征值
        eigenvals = np.where(eigenvals < tol, 0.0, eigenvals)
        sqrt_eigenvals = np.sqrt(eigenvals)

        # 列缩放重构并保持 Hermitian 性
        sqrt_matrix = (eigenvecs * sqrt_eigenvals) @ eigenvecs.conj().T
        sqrt_matrix = (sqrt_matrix + sqrt_matrix.conj().T) / 2

        return sqrt_matrix
    
    # ============================================================================
    # 7. 数据提取方法
    # ============================================================================
    
    def get_real_part(self) -> np.ndarray:
        """获取密度矩阵的实部"""
        return np.real(self._matrix)
    
    def get_imag_part(self) -> np.ndarray:
        """获取密度矩阵的虚部"""
        return np.imag(self._matrix)
    
    def get_amplitude(self) -> np.ndarray:
        """获取密度矩阵的振幅"""
        return np.abs(self._matrix)
    
    def get_phase(self) -> np.ndarray:
        """获取密度矩阵的相位"""
        return np.angle(self._matrix)
    
    # ============================================================================
    # 8. 特殊方法（Magic Methods）
    # ============================================================================
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"DensityMatrix(dim={self.dimension}, purity={self.purity:.6f})"
    
    def __repr__(self) -> str:
        """详细表示"""
        return (f"DensityMatrix(\n"
                f"  dimension={self.dimension},\n"
                f"  purity={self.purity:.6f},\n"
                f"  trace={self.trace:.6f},\n"
                f"  is_physical={self.is_physical()}\n"
                f")")
    
    def __eq__(self, other) -> bool:  # 将类DensityMatrix的 "==" 逻辑改成下面这个, 包括 in; set()操作都会默认这个"=="
        """相等性比较"""
        if not isinstance(other, DensityMatrix):
            return False
        return np.allclose(self._matrix, other._matrix, atol=self.tolerance)
    
    # ============================================================================
    # 9. 工厂方法（Class Methods）
    # ============================================================================
    
    @classmethod  # 不需要类中的实例,就能直接调用--通过DensityMatrix.from_array()来直接调用,而不需要先定义a = DensityMatrix(matrix) 再a.from_array()
                # 目的：创建新实例，所以不需要现有实例
    def from_array(cls, array: np.ndarray, 
                   tolerance: float = 1e-10,
                   enforce: Literal["within_tol", "project", "none"] = "within_tol",
                   strict: bool = False, warn: bool = True) -> 'DensityMatrix':
        """从数组创建密度矩阵（透传策略与告警）""" # 这个数组是np数组
        return cls(array, tolerance=tolerance, enforce=enforce, strict=strict, warn=warn) # cls就是DensityMatrix类本身
        # 当调用 DensityMatrix.from_array(array) 时
        # cls 就是 DensityMatrix 类
        # 所以 cls(array, tolerance) 等价于 DensityMatrix(array, tolerance)
        # 现在看起来简单
        # 但将来可能需要预处理   价值在于:1.提供清晰的接口; 2.支持继承(使用 cls 而不是硬编码类名); 3.未来扩展：可以添加预处理逻辑;4.代码可读性：语义更清晰
    
    @classmethod
    def from_linear_reconstruction(cls, rho_vector: np.ndarray, dimension: int, 
                                 tolerance: float = 1e-10, 
                                 enforce: Literal["within_tol", "project", "none"] = "within_tol",
                                 strict: bool = False, warn: bool = True,
                                 order: Literal["C", "F"] = "C") -> 'DensityMatrix':
        """
        从线性重构结果创建密度矩阵
        
        对应MATLAB中reconstruct_density_matrix_nD.m的步骤：
        1. 将向量重塑为矩阵（行优先顺序）
        2. 取共轭
        3. 应用物理约束
        
        注意：线性重构本身不保证物理性，建议使用 enforce="project" 进行强制投影
        
        Args:
            rho_vector: 线性重构的向量结果
            dimension: 矩阵维度
            tolerance: 数值容差
            enforce: 物理化策略
            strict: 是否对显著非物理输入抛出异常
            warn: 是否对显著非物理输入发出警告
            order: 数组重塑顺序，"C"为行优先（默认），"F"为列优先
        """
        # 将向量重塑为矩阵（固定行优先顺序）
        rho_matrix = np.array(rho_vector, dtype=complex).reshape(dimension, dimension, order=order)
        
        # 取共轭（对应MATLAB的conj(rho_matrix)）
        rho_matrix = np.conj(rho_matrix)
        
        # 创建密度矩阵对象（使用指定的物理化策略）
        return cls(rho_matrix, tolerance=tolerance, enforce=enforce, strict=strict, warn=warn)
    
    @classmethod
    def maximally_mixed(cls, dimension: int,
                        tolerance: float = 1e-10,
                        enforce: Literal["within_tol", "project", "none"] = "within_tol",
                        strict: bool = False, warn: bool = True) -> 'DensityMatrix':
        """创建最大混合态密度矩阵（透传策略与告警）"""
        matrix = np.eye(dimension, dtype=complex) / dimension
        return cls(matrix, tolerance=tolerance, enforce=enforce, strict=strict, warn=warn)
    
    @classmethod
    def pure_state(cls, state_vector: np.ndarray,
                   tolerance: float = 1e-10,
                   enforce: Literal["within_tol", "project", "none"] = "within_tol",
                   strict: bool = False, warn: bool = True) -> 'DensityMatrix':
        """从纯态向量创建密度矩阵（透传策略与告警）"""
        if state_vector.ndim != 1:
            raise ValueError("态向量必须是一维数组")
        v = np.asarray(state_vector, dtype=complex).reshape(-1, 1)
        matrix = v @ v.conj().T
        # 如需：matrix /= np.trace(matrix).real
        return cls(matrix, tolerance=tolerance, enforce=enforce, strict=strict, warn=warn)

    # ============================================================================
    # 10. 内部工具方法（Private Methods）
    # ============================================================================
    
    @classmethod
    def _auto_tol(cls, A: np.ndarray, user_tol: float) -> float:
        """
        自适应容差计算（类方法版本）
        
        根据矩阵维度和范数自动调整容差，避免固定容差在不同场景下的问题：
        - 高维矩阵：数值误差累积，需要更宽松的容差
        - 大范数矩阵：相对误差可能更大
        - 小范数矩阵：容差可能过紧
        
        公式：tol = max(user_tol, k * n * ε * max(1, ||A||₂))
        
        Args:
            A: 输入矩阵（通常是Hermitian化后的矩阵）
            user_tol: 用户指定的容差
            
        Returns:
            自适应容差值
        """
        eps = np.finfo(float).eps            # 2.22e-16 机器精度
        n = A.shape[0]                       # 矩阵维度
        k = float(cls.k_factor)              # 读取类属性，子类可改
        norm2 = np.linalg.norm(A, 2)         # 2-范数/谱范数近似
        
        return max(float(user_tol), k * n * eps * max(1.0, norm2))
    
    def _auto_tol_inst(self, A: np.ndarray) -> float:
        """
        实例便捷封装：使用实例的 tolerance 调用类方法
        
        Args:
            A: 输入矩阵
            
        Returns:
            自适应容差值
        """
        return type(self)._auto_tol(A, self.tolerance)
    
    @classmethod
    def _heig(cls, H: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        统一Hermitian特征值分解封装（类方法版本）
        
        所有特征值分解统一走此路径，确保行为一致性和性能优化：
        - lower=True: 只使用下三角，更高效
        - check_finite=False: 跳过逐元素检查，上游已把关
        
        Args:
            H: Hermitian矩阵（或已做 (A + A†)/2 处理）
            
        Returns:
            (eigenvals, eigenvecs): 特征值和特征向量
        """
        vals, vecs = eigh(H, lower=True, check_finite=False)
        return np.real(vals), vecs
    
    def _sanitize_within_tol(self, matrix: np.ndarray, *, diagnostic: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, dict]]:
        """
        容差内物理化处理（数值稳定性处理）。
        仅修正容差范围内的数值误差，对显著非物理输入发出警告。

        参数:
            matrix: 原始矩阵 (可能含轻微数值误差)
            diagnostic: 若为 True，返回额外的物理性指标 (dict)

        返回:
            rho_sanitized: 容差内物理化的密度矩阵
        """

        # ---------------------------------------------------------
        # 1️⃣ Hermitian 化输入，抑制浮点噪声
        # ---------------------------------------------------------
        H = (matrix + matrix.conj().T) / 2

        # ---------------------------------------------------------
        # 2️⃣ 统一特征值分解
        # ---------------------------------------------------------
        eigenvals, eigenvecs = type(self)._heig(H)

        # ---------------------------------------------------------
        # 3️⃣ 自适应容差
        # ---------------------------------------------------------
        tol = self._auto_tol_inst(H)

        # ---------------------------------------------------------
        # 4️⃣ 预诊断（不更改输入矩阵）
        # ---------------------------------------------------------
        # 检查 Hermitian 性
        herm_res = np.linalg.norm(matrix - matrix.conj().T) / (np.linalg.norm(matrix) + 1e-30)
        
        # 检查迹
        tr = np.trace(matrix)
        tr_dev = abs(tr.real - 1.0)
        tr_im = abs(tr.imag)
        
        # 显著非物理检查
        if (herm_res > 1e-6 or tr_dev > 1e-6 or tr_im > 1e-9):
            msg = (f"[DensityMatrix] 输入偏离物理约束: Herm={herm_res:.2e}, "
                   f"dTr={tr_dev:.2e}, ImTr={tr_im:.2e}. "
                   f"若需强制投影请使用 enforce='project' 或 project_to_physical().")
            if self.strict:
                raise ValueError(msg)
            if self.warn:
                warnings.warn(msg, RuntimeWarning, stacklevel=2)

        # ---------------------------------------------------------
        # 5️⃣ 检查最小特征值并分类处理
        # ---------------------------------------------------------
        min_eig = float(eigenvals.min())
        if min_eig < -10 * tol and not np.isclose(min_eig, 0.0, atol=tol):
            # 如果出现显著负值（超过容差一个数量级）
            msg = (f"[DensityMatrix] 显著负特征值 min_eig={min_eig:.3e} < -10*tol({tol:.1e}); "
                   "构造不强制洗白，请检查算法或使用 enforce='project'.")
            if self.strict:
                raise ValueError(msg)
            if self.warn:
                warnings.warn(msg, RuntimeWarning, stacklevel=2)

        # 容差范围内裁剪 (数值卫生修复)
        eigenvals = np.where(eigenvals < tol, 0.0, eigenvals)

        # ---------------------------------------------------------
        # 6️⃣ 重新归一化使 Tr(ρ)=1
        # ---------------------------------------------------------
        trace_val = np.sum(eigenvals)
        if trace_val <= tol:
            # 所有特征值接近0 → 退化为最大混合态 I/n
            eigenvals = np.ones(self.dimension, dtype=float) / self.dimension
        else:
            eigenvals /= trace_val

        # ---------------------------------------------------------
        # 7️⃣ 列缩放重构（避免 np.diag 临时阵）
        # ---------------------------------------------------------
        rho_physical = (eigenvecs * eigenvals) @ eigenvecs.conj().T
        rho_physical = (rho_physical + rho_physical.conj().T) / 2

        # ---------------------------------------------------------
        # 8️⃣ 再次归一化以消除数值漂移
        # ---------------------------------------------------------
        trace_rho = float(np.real(np.trace(rho_physical)))
        if trace_rho <= 0:
            rho_physical = np.eye(self.dimension, dtype=complex) / self.dimension
        else:
            rho_physical /= trace_rho

        # ---------------------------------------------------------
        # 9️⃣ 可选: 返回诊断信息
        # ---------------------------------------------------------
        if diagnostic:
            max_eig = np.max(eigenvals)
            trace_error = abs(trace_rho - 1.0)
            hermitian_error = np.linalg.norm(rho_physical - rho_physical.conj().T)
            return rho_physical, {
                "min_eig": float(min_eig),
                "max_eig": float(max_eig),
                "trace_error": float(trace_error),
                "hermitian_error": float(hermitian_error),
                "tol": float(tol),
            }

        return rho_physical
    
    def _make_physical_matrix(self, matrix: np.ndarray, *, diagnostic: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, dict]]:
        """
        向后兼容的别名方法（已弃用）
        
        请使用 _sanitize_within_tol 或 project_to_physical
        """
        import warnings
        warnings.warn(
            "_make_physical_matrix is deprecated, use _sanitize_within_tol or project_to_physical",
            DeprecationWarning,
            stacklevel=2
        )
        return self._sanitize_within_tol(matrix, diagnostic=diagnostic)
    

# ============================================================================
# 11. 便捷函数（Module-level Functions）
# ============================================================================

def make_physical(matrix: np.ndarray, tolerance: float = 1e-10) -> np.ndarray:
    """
    便捷函数：使矩阵满足物理条件（已弃用）
    
    推荐使用：
    - DensityMatrix(matrix, tolerance=tolerance).matrix
    - DensityMatrix.project_to_physical(matrix, tolerance=tolerance)
    
    对应MATLAB的makephysical.m函数
    """
    import warnings
    warnings.warn(
        "make_physical is deprecated, use DensityMatrix(matrix, tolerance=tolerance).matrix "
        "or DensityMatrix.project_to_physical(matrix, tolerance=tolerance)",
        DeprecationWarning,
        stacklevel=2
    )
    dm = DensityMatrix(matrix, tolerance=tolerance)
    return dm.matrix


def compute_fidelity(rho1: np.ndarray, rho2: np.ndarray, 
                    tolerance: float = 1e-10) -> float:
    """
    便捷函数：计算两个密度矩阵的保真度（已弃用）
    
    推荐使用：
    - DensityMatrix(rho1, tolerance=tolerance).fidelity(DensityMatrix(rho2, tolerance=tolerance))
    
    对应MATLAB的fidelity.m函数
    """
    import warnings
    warnings.warn(
        "compute_fidelity is deprecated, use DensityMatrix(rho1).fidelity(DensityMatrix(rho2))",
        DeprecationWarning,
        stacklevel=2
    )
    dm1 = DensityMatrix(rho1, tolerance=tolerance)
    dm2 = DensityMatrix(rho2, tolerance=tolerance)
    return dm1.fidelity(dm2)
