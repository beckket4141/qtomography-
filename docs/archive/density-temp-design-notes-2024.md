# 密度矩阵临时设计草稿（归档）

> **状态**：已归档，仅保留历史背景。当前实现详见 docs/implemented/density-module-overview.md。

我来详细分析MATLAB中的密度矩阵相关代码，然后设计并实现Python版本的`density.py`。


[4 tools called]

现在让我查看一些测试数据来了解密度矩阵的格式：


[2 tools called]

让我检查正确的路径：


[2 tools called]

我发现teste文件夹不在当前目录下。让我基于MATLAB代码分析来设计`density.py`。

## 详细设计计划

基于MATLAB代码分析，我需要实现一个`DensityMatrix`类，它应该包含以下核心功能：

### 1. 核心属性
- 存储复数密度矩阵数据
- 维度信息
- 数值精度控制

### 2. 核心方法
- `ensure_physical()` - 对应MATLAB的`makephysical.m`
- `purity()` - 计算纯度
- `trace()` - 计算迹
- `eigenvalues()` - 获取特征值
- `is_hermitian()` - 检查Hermitian性
- `is_positive_semidefinite()` - 检查正半定性

### 3. 静态方法
- `from_array()` - 从数组创建密度矩阵
- `from_linear_reconstruction()` - 从线性重构结果创建

现在让我实现这个类：


[3 tools called]

现在让我检查代码是否有语法错误：


[1 tool called]

## 详细设计说明

我已经完成了`density.py`的实现，下面详细解释我的设计思路和与MATLAB代码的对应关系：

### 1. 核心设计理念

**面向对象设计**：将密度矩阵封装为一个类，提供丰富的属性和方法，比MATLAB的过程式编程更加模块化和可复用。

### 2. 与MATLAB代码的对应关系

| MATLAB函数 | Python方法 | 功能说明 |
|------------|------------|----------|
| `makephysical.m` | `ensure_physical()` | 确保密度矩阵满足物理条件 |
| `fidelity.m` | `fidelity()` | 计算两个密度矩阵的保真度 |
| `matrix_square_root.m` | `matrix_square_root()` | 计算矩阵平方根 |
| 密度矩阵基本操作 | 各种属性方法 | 纯度、迹、特征值等 |

### 3. 核心功能实现

#### 3.1 物理约束处理 (`ensure_physical()`)
```python
# 对应MATLAB的makephysical.m
def ensure_physical(self) -> np.ndarray:
    # 1. 特征值分解
    eigenvals, eigenvecs = eig(self._matrix)
    
    # 2. 将负特征值设为0
    eigenvals = np.where(eigenvals < 0, 0, eigenvals)
    
    # 3. 重新归一化
    eigenvals = eigenvals / np.sum(eigenvals)
    
    # 4. 重构并确保Hermitian性
    # 完全对应MATLAB的复杂操作
```

#### 3.2 保真度计算 (`fidelity()`)
```python
# 对应MATLAB的fidelity.m
def fidelity(self, other: 'DensityMatrix') -> float:
    # F(ρ₁, ρ₂) = [Tr(√(√ρ₁ ρ₂ √ρ₁))]²
    sqrt_rho1 = self.matrix_square_root()
    intermediate = sqrt_rho1 @ other.matrix @ sqrt_rho1
    sqrt_intermediate = self.matrix_square_root(intermediate)
    return np.real(np.trace(sqrt_intermediate)) ** 2
```

#### 3.3 矩阵平方根 (`matrix_square_root()`)
```python
# 对应MATLAB的matrix_square_root.m
def matrix_square_root(self, matrix: Optional[np.ndarray] = None) -> np.ndarray:
    eigenvals, eigenvecs = eig(matrix)
    sqrt_eigenvals = np.sqrt(eigenvals)
    return eigenvecs @ np.diag(sqrt_eigenvals) @ np.linalg.inv(eigenvecs)
```

### 4. 增强功能

#### 4.1 丰富的属性
- `purity`: 纯度计算
- `trace`: 迹计算
- `eigenvalues`: 特征值获取
- `dimension`: 维度信息

#### 4.2 物理条件验证
- `is_hermitian()`: Hermitian性检查
- `is_positive_semidefinite()`: 正半定性检查
- `is_normalized()`: 归一化检查
- `is_physical()`: 综合物理条件检查

#### 4.3 便捷的工厂方法
- `from_linear_reconstruction()`: 从线性重构结果创建
- `maximally_mixed()`: 创建最大混合态
- `pure_state()`: 从纯态向量创建

### 5. 数值稳定性改进

1. **容差控制**：使用`tolerance`参数控制数值比较精度
2. **异常处理**：添加输入验证和错误处理
3. **数值稳定性**：在`ensure_physical()`中添加数值稳定性项
4. **精度控制**：保真度计算精确到8位小数

### 6. 使用示例

```python
# 创建密度矩阵
rho = DensityMatrix.from_array(some_matrix)

# 检查物理性
if not rho.is_physical():
    print("密度矩阵不满足物理条件")

# 计算保真度
fidelity = rho1.fidelity(rho2)

# 获取属性
print(f"纯度: {rho.purity}")
print(f"迹: {rho.trace}")
print(f"特征值: {rho.eigenvalues}")
```

这个实现完全对应了MATLAB的核心功能，同时提供了更丰富的接口和更好的错误处理。接下来我们可以为这个类编写单元测试来验证其正确性。