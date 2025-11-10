# MUB使用指南

## 快速开始

### 基本使用

```python
from qtomography.domain.measurement.mub import build_mub_projectors

# 创建维度为5的MUB投影算符
design = build_mub_projectors(dimension=5)

# 访问投影算符、分组和测量矩阵
projectors = design.projectors  # shape: (d(d+1), d, d)
groups = design.groups          # shape: (d(d+1),)
measurement_matrix = design.measurement_matrix  # shape: (d(d+1), d*d)
```

### 与ProjectorSet集成

```python
from qtomography.domain.projectors import ProjectorSet

# 使用MUB设计
ps = ProjectorSet(dimension=5, design="mub")

# 访问投影算符
projectors = ps.projectors
groups = ps.groups
```

## 支持的维度

### 理论支持范围

MUB仅支持**素数幂维度**：d = p^k（p是素数，k ≥ 1）

- ✅ 支持：2, 3, 4(2²), 5, 7, 8(2³), 9(3²), 11, 13, 16(2⁴), 25(5²), 27(3³)...
- ❌ 不支持：6, 10, 12, 14, 15, 18...（非素数幂）

### 实际支持情况

#### 情况1：安装了galois库（推荐）

**完全支持所有素数幂维度**：
- 所有素数：2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31...
- 2的幂次：4, 8, 16, 32, 64...
- 3的幂次：9, 27, 81...
- 5的幂次：25, 125...
- 其他素数幂：49(7²), 121(11²)...

**安装galois库**：
```bash
pip install galois
```

#### 情况2：未安装galois库

**有限支持**（仅 `_MinimalGFBackend`）：
- ✅ 所有素数维度：2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31...
- ✅ d=4 (2²)
- ✅ d=9 (3²)
- ✅ d=16 (2⁴)
- ❌ 不支持：d=8, 25, 27, 32等其他素数幂

## 构造方法

### method='wh'（默认，推荐）

**Weyl-Heisenberg/Pauli构造**：
- **奇数特征 (p>2)**：使用有限域二次相位公式
- **特征2 (p=2)**：使用Stabilizer/Pauli构造

**支持范围**：
- 安装galois库：所有素数幂维度
- 未安装galois库：所有素数，d=4, d=9, d=16

```python
# 使用Weyl-Heisenberg构造
design = build_mub_projectors(dimension=9, method='wh')
```

### method='ff'

**有限域二次相位公式**：
- 仅支持**奇数特征 (p>2)**
- 不支持特征2 (p=2)

**支持范围**：
- 安装galois库：所有奇数特征的素数幂维度
- 未安装galois库：所有奇素数，d=9

```python
# 使用有限域公式（仅奇数特征）
design = build_mub_projectors(dimension=9, method='ff')
```

## variant参数

### variant='compact'（默认）

返回 **d² 个投影算符**（选择d组线性无关的基）

```python
design = build_mub_projectors(dimension=5, variant='compact')
print(len(design.projectors))  # 输出: 25
```

**用途**：最小信息完备集，适合线性重构

### variant='full'

返回 **d(d+1) 个投影算符**（全部d+1组基）

```python
design = build_mub_projectors(dimension=5, variant='full')
print(len(design.projectors))  # 输出: 30
```

**用途**：完整MUB集合，适合需要所有基的场景

## 错误处理

### 非素数幂维度

```python
try:
    design = build_mub_projectors(dimension=6)  # 6不是素数幂
except ValueError as e:
    print(e)  # "dimension 6 is not a prime power"
```

### 未安装galois库时的限制

```python
try:
    design = build_mub_projectors(dimension=25)  # 需要galois库
except NotImplementedError as e:
    print(e)  # "GF(p^k) not implemented for given (p,k) in fallback backend"
    # 建议：pip install galois
```

### method='ff'用于特征2

```python
try:
    design = build_mub_projectors(dimension=4, method='ff')
except ValueError as e:
    print(e)  # "method='ff' is invalid for characteristic 2; use method='wh'"
```

## 完整示例

### 示例1：基本使用

```python
from qtomography.domain.measurement.mub import build_mub_projectors
import numpy as np

# 创建MUB
design = build_mub_projectors(dimension=5, method='wh', variant='full')

# 检查结构
print(f"维度: {design.dimension}")
print(f"投影算符数量: {len(design.projectors)}")
print(f"基组数量: {len(np.unique(design.groups))}")  # 应该是 d+1 = 6

# 验证MUB性质（可选）
# 检查组内正交性和组间无偏性...
```

### 示例2：与重构器集成

```python
from qtomography.domain.projectors import ProjectorSet
from qtomography.domain.reconstruction.linear import LinearReconstructor

# 创建投影算符集合
ps = ProjectorSet(dimension=5, design="mub")

# 创建线性重构器
reconstructor = LinearReconstructor(dimension=5, design="mub")

# 使用测量概率重构密度矩阵
probabilities = np.random.rand(len(ps.projectors))
probabilities = probabilities / np.sum(probabilities) * len(ps.groups)
rho = reconstructor.reconstruct(probabilities)
```

### 示例3：不同variant的对比

```python
# compact模式：d²个投影
compact = build_mub_projectors(5, variant='compact')
print(f"Compact: {len(compact.projectors)} 个投影")  # 25

# full模式：d(d+1)个投影
full = build_mub_projectors(5, variant='full')
print(f"Full: {len(full.projectors)} 个投影")  # 30
```

## 性能考虑

1. **安装galois库**：强烈推荐，支持所有维度且性能更好
2. **variant选择**：
   - `compact`：更少的投影算符，适合快速重构
   - `full`：完整的MUB集合，适合需要所有基的场景
3. **缓存**：`ProjectorSet` 默认启用缓存，重复使用相同维度时自动复用

## 常见问题

### Q: 为什么d=6不支持？
A: MUB理论仅保证在素数幂维度上存在完整的d+1组MUB。对于非素数幂维度（如d=6），完整MUB集合的存在性仍是开放问题。

### Q: 如何支持更多维度？
A: 安装galois库：`pip install galois`。安装后支持所有素数幂维度。

### Q: method='wh'和method='ff'有什么区别？
A: 
- `wh`：Weyl-Heisenberg构造，支持所有素数幂（包括p=2）
- `ff`：有限域公式，仅支持奇数特征（p>2）

### Q: variant='compact'和'full'如何选择？
A:
- `compact`：最小信息完备集（d²个投影），适合线性重构
- `full`：完整MUB集合（d(d+1)个投影），适合需要所有基的场景

## 相关文档

- 理论背景：`python/docs/相互无偏基矢构造.markdown`
- 实现分析：`python/docs/roadmap/mub/MUB_IMPLEMENTATION_ANALYSIS.md`
- 维度支持：`python/docs/roadmap/mub/MUB支持的维度分析.md`
- 参考文献：`python/docs/roadmap/mub/参考文献.md`

