# DensityMatrix 结构概述（2024年最新版）

下面是一份**清晰、简单、可一眼看懂**的整体结构大纲（按"模块→类→职责→关键方法→数据流"）：

## 1) 模块分层（1 文件内的逻辑分层）

* **A. 核心数据结构层** ：`class DensityMatrix`
* **B. 便捷函数层** ：`make_physical`、`compute_fidelity`
* **C. 依赖与类型** ：`numpy`, `scipy.linalg.eigh`, `typing.Optional`

## 2) `DensityMatrix` 类的职责与不变量

* **职责** ：承载与维护"物理密度矩阵"（Hermitian、PSD、`Tr=1`），并提供常用谱/度量运算。
* **不变量** ：实例创建完成后，`self._matrix` 满足物理性；若被外部改写，可用 `sanitize_within_tol()` 重新投影。

## 3) `DensityMatrix` 的接口结构（按功能分组）

### **A. 类定义和类属性**
```python
class DensityMatrix:
    k_factor: float = 50.0  # 自适应容差因子
```

### **B. 构造与初始化**
```python
def __init__(self, matrix, *, tolerance=1e-10, enforce='within_tol', strict=True, warn=True)
def _validate_input(self) -> None
```

### **C. 属性访问器（Properties）**
```python
@property
def matrix(self) -> np.ndarray
@property  
def dimension(self) -> int
@property
def trace(self) -> complex
@property
def purity(self) -> float
@property
def eigenvalues(self) -> np.ndarray
```

### **D. 物理性检查方法（外部接口）**
```python
def is_hermitian(self, tol=None, *, use_auto=True) -> bool
def is_positive_semidefinite(self, tol=None, *, use_auto=True) -> bool
def is_normalized(self, tol=None, *, use_auto=True) -> bool
def is_physical(self, tol=None, *, use_auto=True) -> bool
def physical_diagnostics(self, tol=None, *, use_auto=True) -> dict
```

### **E. 物理化处理方法**
```python
def sanitize_within_tol(self) -> np.ndarray
@classmethod
def project_to_physical(cls, matrix, *, tolerance=1e-10, enforce='within_tol', strict=True, warn=True) -> 'DensityMatrix'
```

### **F. 数值计算方法**
```python
def fidelity(self, other: 'DensityMatrix') -> float
def matrix_square_root(self, matrix: Optional[np.ndarray] = None) -> np.ndarray
```

### **G. 数据提取方法**
```python
def get_real_part(self) -> np.ndarray
def get_imag_part(self) -> np.ndarray
def get_amplitude(self) -> np.ndarray
def get_phase(self) -> np.ndarray
```

### **H. 特殊方法（Magic Methods）**
```python
def __str__(self) -> str
def __repr__(self) -> str
def __eq__(self, other) -> bool
```

### **I. 工厂方法（Class Methods）**
```python
@classmethod
def from_array(cls, array, *, tolerance=1e-10, enforce='within_tol', strict=True, warn=True) -> 'DensityMatrix'
@classmethod
def from_linear_reconstruction(cls, rho_vector, dimension, *, tolerance=1e-10, enforce='within_tol', strict=True, warn=True) -> 'DensityMatrix'
@classmethod
def maximally_mixed(cls, dimension, *, tolerance=1e-10) -> 'DensityMatrix'
@classmethod
def pure_state(cls, state_vector, *, tolerance=1e-10) -> 'DensityMatrix'
```

### **J. 内部工具方法（Private Methods）**
```python
@classmethod
def _auto_tol(cls, A, user_tol) -> float
def _auto_tol_inst(self, A) -> float
@classmethod
def _heig(cls, H) -> Tuple[np.ndarray, np.ndarray]
def _sanitize_within_tol(self, matrix, *, diagnostic=False) -> Union[np.ndarray, Tuple[np.ndarray, dict]]
```

## 4) 弃用函数（向后兼容）

```python
def make_physical(matrix, tolerance=1e-10) -> np.ndarray  # 弃用
def compute_fidelity(rho1, rho2, tolerance=1e-10) -> float  # 弃用
def ensure_physical(self) -> np.ndarray  # 弃用
def _make_physical_matrix(self, matrix, *, diagnostic=False) -> Union[np.ndarray, Tuple[np.ndarray, dict]]  # 弃用
```

## 5) 典型数据流（使用方式）

```
输入任意矩阵 A
 └─> DensityMatrix(A)                      # 构造即物理化
      ├─ 校验/只读：dm.is_physical(), dm.purity, dm.eigenvalues
      ├─ 度量：dm.fidelity(DensityMatrix(B))
      ├─ 光谱算子：dm.matrix_square_root()
      └─ 若外部改写 dm._matrix → dm.sanitize_within_tol() 再投影
```

## 6) 数值策略（统一风格）

* 所有谱运算前 **Hermitian 化** ；小负本征值按 **自适应容差**  **裁剪为 0** ；
* **两次归一化**确保 `Tr=1`；边界时回退到 `I/d`；与 MATLAB 心智对齐。
* **外部检查接口**：支持自定义容差，默认使用自适应容差

## 7) 一眼看懂的"盒图"

```
[ DensityMatrix ]
  |-- state: _matrix (complex NxN), tolerance, enforce, strict, warn
  |-- validate: _validate_input()
  |-- project:  _make_physical_matrix()  <-- 核心：Hermitian + eigh + clip + renorm
  |-- checks:   is_hermitian/is_psd/is_normalized/is_physical (外部接口)
  |-- props:    matrix/dimension/trace/purity/eigenvalues
  |-- ops:      matrix_square_root(), fidelity()
  |-- factory:  from_array(), from_linear_reconstruction(), pure_state(), maximally_mixed()
  |-- tools:    _auto_tol(), _heig(), _sanitize_within_tol()

[ Helpers ]
  |-- make_physical(matrix)      -> DensityMatrix(matrix).matrix (弃用)
  |-- compute_fidelity(rho1,rho2)-> DensityMatrix(rho1).fidelity(DensityMatrix(rho2)) (弃用)
```

## 8) 关键改进（2024年重构）

### **外部检查接口统一化**
- 所有 `is_*` 方法支持外部容差控制：`tol` 参数
- 新增 `use_auto` 参数：是否叠加自适应容差
- `is_hermitian` 使用相对残差，其他使用绝对容差

### **自适应容差系统**
- `_auto_tol()`: 基于矩阵维度和范数的自适应容差
- 默认策略：`tol_eff = max(user_tol, auto_tol)`

### **向后兼容性**
- 保持原有 API 不变
- 弃用函数标记但保留功能
- 新增参数都有合理默认值

> 这就是一个**"创建即物理、谱法为核、外部可控、函数式便捷入口"**的现代化结构。用时从便捷函数起步，深入时直接用类；需要精确控制时使用外部容差参数。

## 9) 方法统计汇总（有效方法）

| 功能分组 | 方法数量 | 主要功能 |
|----------|----------|----------|
| **构造与初始化** | 2 | 输入验证、初始化 |
| **属性访问器** | 5 | 数据访问 |
| **物理性检查** | 5 | 外部检查接口 |
| **物理化处理** | 2 | 确保物理性 |
| **数值计算** | 2 | 保真度、平方根 |
| **数据提取** | 4 | 实部、虚部、振幅、相位 |
| **特殊方法** | 3 | 字符串表示、相等性 |
| **工厂方法** | 4 | 特殊创建 |
| **内部工具** | 4 | 自适应容差、特征值分解 |

**有效方法总计：31个**，涵盖了密度矩阵的完整操作！

## 9.1) 弃用方法统计

| 弃用方法 | 数量 | 替代方案 |
|----------|------|----------|
| **模块函数** | 2 | `make_physical` → `DensityMatrix(matrix).matrix`<br>`compute_fidelity` → `DensityMatrix(rho1).fidelity(DensityMatrix(rho2))` |
| **实例方法** | 2 | `ensure_physical` → `sanitize_within_tol`<br>`_make_physical_matrix` → `_sanitize_within_tol` |

**弃用方法总计：4个**，保留用于向后兼容。

## 10) 访问级别统计（有效方法）

| 访问级别 | 数量 | 占比 | 说明 |
|----------|------|------|------|
| **公有方法** | 25个 | 81% | 用户接口 |
| **私有方法** | 6个 | 19% | 内部实现 |

## 10.1) 弃用方法访问级别

| 访问级别 | 数量 | 说明 |
|----------|------|------|
| **模块函数** | 2个 | 弃用便捷入口 |
| **实例方法** | 2个 | 弃用方法 |

## 11) 关键设计原则

1. **外部可控**：所有检查方法支持自定义容差
2. **自适应容差**：基于矩阵特性自动调整容差
3. **向后兼容**：保持原有 API 不变
4. **职责分离**：构造、检查、处理、计算各司其职
5. **数值稳定**：统一的 Hermitian 化和特征值处理策略