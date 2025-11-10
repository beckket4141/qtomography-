# ProjectorSet 代码结构分析与系统集成

> **核心定位**：`ProjectorSet` 是量子层析重构系统的**测量基础设施提供者**，负责生成和管理不同测量设计的投影算符集合。

---

## 1. 代码架构设计

### 1.1 设计模式

```
┌─────────────────────────────────────┐
│      ProjectorSet (门面/适配器)      │
│  - 统一接口 (bases, projectors等)    │
│  - 类级缓存 (_CACHE)                 │
│  - 策略选择 (design="mub"/"sic")     │
└──────────────┬──────────────────────┘
               │ 委托给具体实现
               ├─────────────────┬─────────────────┐
               ▼                 ▼                 ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │  MUB     │      │   SIC    │      │  未来    │
        │ 设计     │      │  POVM    │      │  扩展    │
        └──────────┘      └──────────┘      └──────────┘
```

**使用的设计模式**：
1. **策略模式 (Strategy Pattern)**：通过 `design` 参数选择不同的测量设计（MUB/SIC）
2. **工厂模式 (Factory Pattern)**：`get()` 类方法提供便捷的创建接口
3. **单例缓存模式**：类级 `_CACHE` 确保相同维度/设计只计算一次
4. **适配器模式**：统一不同设计（MUB/SIC）的接口差异

### 1.2 核心数据结构

```python
class ProjectorSet:
    # 类级缓存：键=(dimension, design)，值=(bases, projectors, measurement_matrix, groups)
    _CACHE: ClassVar[dict[tuple[int, str], Tuple[...]]] = {}
    
    # 实例属性（都是副本，确保缓存安全）
    _bases: np.ndarray              # (d, d) - 为向后兼容保留
    _projectors: np.ndarray         # (m, d, d) - 投影算符矩阵
    _measurement_matrix: np.ndarray # (m, d*d) - 测量矩阵（线性方程系数）
    _groups: np.ndarray             # (m,) - 分组标识（用于归一化）
```

**数据维度说明**：
- `dimension = d`：希尔伯特空间维度
- `m`：投影算符总数
  - MUB: `m = (d+1) * d` （d+1 个基，每个基 d 个投影算符）
  - SIC: `m = d^2` （d=2 时为 4）
- `groups`：每个投影算符所属的测量基组（用于按组归一化）

---

## 2. 与其他模块的集成关系

### 2.1 依赖关系图

```
┌─────────────────────────────────────────────────────────┐
│                   使用 ProjectorSet 的模块                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐      ┌─────────────────┐           │
│  │ LinearRecon-    │      │ WLSRecon-       │           │
│  │ structor        │      │ structor        │           │
│  │                 │      │                 │           │
│  │ 用途：          │      │ 用途：          │           │
│  │ - 获取测量矩阵  │      │ - 获取投影算符  │           │
│  │ - 按组归一化    │      │ - 计算期望概率  │           │
│  └─────────────────┘      └─────────────────┘           │
│                                                          │
│  ┌─────────────────┐                                    │
│  │ Controller      │                                    │
│  │ (应用层)        │                                    │
│  │                 │                                    │
│  │ 用途：          │                                    │
│  │ - 管理重构器    │                                    │
│  │ - 传递配置      │                                    │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ 依赖
                        │
┌─────────────────────────────────────────────────────────┐
│              ProjectorSet 依赖的模块                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐      ┌─────────────────┐           │
│  │ mub.py          │      │ sic.py          │           │
│  │                 │      │                 │           │
│  │ build_mub_      │      │ build_sic_      │           │
│  │ projectors()    │      │ projectors()    │           │
│  │                 │      │                 │           │
│  │ 返回：          │      │ 返回：          │           │
│  │ MUBDesign       │      │ SICDesign       │           │
│  └─────────────────┘      └─────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

### 2.2 具体集成点分析

#### A. 线性重构器 (`linear.py`)

```python
# 使用场景
class LinearReconstructor:
    def __init__(self, dimension: int, ..., design: str = "mub"):
        self.projector_set = ProjectorSet.get(dimension, design=design)
    
    def reconstruct_with_details(self, probabilities):
        # 1. 获取测量矩阵用于线性方程求解
        measurement_matrix = self.projector_set.measurement_matrix  # (m, d*d)
        
        # 2. 使用 groups 进行按组归一化
        probs = self._normalize_probabilities_grouped(probabilities)
        # groups 用于确定哪些投影算符属于同一测量基
        
        # 3. 求解线性方程
        rho_vec = np.linalg.lstsq(measurement_matrix, probs, ...)
```

**关键集成点**：
- **测量矩阵**：用于线性方程 `M · ρ_vec = p_vec`
- **分组信息**：确保同一测量基的概率归一化到 1

#### B. 加权最小二乘重构器 (`wls.py`)

```python
# 使用场景
class WLSReconstructor:
    def __init__(self, dimension: int, ..., design: str = "mub"):
        self.projector_set = ProjectorSet.get(dimension, design=design)
    
    def reconstruct_with_details(self, probabilities):
        # 1. 获取投影算符用于计算期望概率
        projectors = self.projector_set.projectors  # (m, d, d)
        
        # 2. 在优化目标函数中使用
        expected = self._expected_probabilities(rho, projectors)
        # expected[i] = Tr(ρ · projectors[i])
```

**关键集成点**：
- **投影算符**：用于计算期望概率 `Tr(ρ · E_i)`
- **分组归一化**：与线性重构相同

#### C. 控制器 (`controller.py`)

```python
# 使用场景
class ReconstructionController:
    def __init__(self, config: ReconstructionConfig):
        # Controller 通过配置传递 design 参数
        # 由 LinearReconstructor/WLSReconstructor 内部创建 ProjectorSet
        pass
```

**关键集成点**：
- **配置传递**：从配置层到重构器再到 ProjectorSet
- **设计选择**：用户可以通过配置选择 MUB 或 SIC

---

## 3. 数据流分析

### 3.1 创建流程

```
用户调用
  │
  ├─> LinearReconstructor(dimension=4, design="mub")
  │         │
  │         └─> ProjectorSet.get(4, design="mub")
  │                    │
  │                    ├─> 检查缓存 _CACHE[(4, "mub")]
  │                    │
  │                    ├─> [缓存命中] 返回缓存数据
  │                    │
  │                    └─> [缓存未命中]
  │                            │
  │                            ├─> build_mub_projectors(4)
  │                            │        │
  │                            │        └─> 生成 MUBDesign:
  │                            │              - projectors: (20, 4, 4)
  │                            │              - groups: (20,)
  │                            │              - measurement_matrix: (20, 16)
  │                            │
  │                            └─> 存入缓存并返回副本
```

### 3.2 使用流程（线性重构示例）

```
测量概率 p = [p₁, p₂, ..., p₂₀]
  │
  ├─> LinearReconstructor.reconstruct_with_details(p)
  │         │
  │         ├─> _normalize_probabilities_grouped(p)
  │         │         │
  │         │         ├─> 使用 projector_set.groups
  │         │         │    groups = [0,0,0,0, 1,1,1,1, ..., 4,4,4,4]
  │         │         │
  │         │         └─> 按组归一化：
  │         │              group 0: p[0:4] / sum(p[0:4])
  │         │              group 1: p[4:8] / sum(p[4:8])
  │         │              ...
  │         │
  │         ├─> 获取测量矩阵
  │         │    M = projector_set.measurement_matrix  # (20, 16)
  │         │
  │         ├─> 求解线性方程
  │         │    M · ρ_vec = p_normalized
  │         │    → ρ_vec (16,)
  │         │
  │         └─> 重塑为密度矩阵
  │              ρ = reshape(ρ_vec) → (4, 4)
```

### 3.3 缓存机制

```python
# 第一次使用
ps1 = ProjectorSet.get(4, design="mub")  
# → 计算并缓存

# 第二次使用（同一维度+设计）
ps2 = ProjectorSet.get(4, design="mub")  
# → 直接从缓存读取

# 不同设计
ps3 = ProjectorSet.get(4, design="sic")  
# → 新计算（MUB 和 SIC 的缓存键不同）

# 缓存结构
_CACHE = {
    (4, "mub"): (bases, projectors, measurement_matrix, groups),
    (4, "sic"): (bases, projectors, measurement_matrix, groups),
    (16, "mub"): (bases, projectors, measurement_matrix, groups),
    ...
}
```

---

## 4. 接口设计分析

### 4.1 属性接口（只读，返回副本）

```python
@property
def bases(self) -> np.ndarray:
    """为向后兼容保留，当前返回零矩阵"""
    return self._bases.copy()  # 防御性副本

@property
def projectors(self) -> np.ndarray:
    """(m, d, d) 投影算符矩阵"""
    return self._projectors.copy()

@property
def measurement_matrix(self) -> np.ndarray:
    """(m, d*d) 测量矩阵，用于线性方程"""
    return self._measurement_matrix.copy()

@property
def groups(self) -> np.ndarray:
    """(m,) 分组标识，用于按组归一化"""
    return self._groups.copy()
```

**设计原则**：
- **不可变性**：所有属性返回副本，防止外部修改污染缓存
- **维度一致性**：确保 `measurement_matrix[i] = projectors[i].flatten()`

### 4.2 类方法接口

```python
@classmethod
def get(cls, dimension: int, *, design: str = "mub") -> "ProjectorSet":
    """工厂方法：从缓存获取或创建新的 ProjectorSet"""
    return cls(dimension, design=design, cache=True)

@classmethod
def clear_cache(cls) -> None:
    """测试工具：清空缓存"""
    cls._CACHE.clear()
```

---

## 5. 扩展性设计

### 5.1 添加新的测量设计

```python
# 1. 在对应的 measurement/ 目录下实现构建函数
def build_xxx_projectors(dimension: int) -> XXXDesign:
    # 返回包含 projectors, groups, measurement_matrix 的数据类
    pass

# 2. 在 ProjectorSet.__init__ 中添加分支
elif self.design == "xxx":
    xxx = build_xxx_projectors(dimension)
    bases = np.zeros((dimension, dimension), dtype=complex)
    projectors = xxx.projectors
    groups = xxx.groups
    measurement = xxx.measurement_matrix
```

### 5.2 当前支持的测量设计

| 设计 | 维度要求 | 投影算符数 | 分组数 | 状态 |
|------|---------|-----------|--------|------|
| **MUB** | 素数幂 (2, 3, 4, 5, 7, 8, 9, ...) | (d+1)·d | d+1 | ✅ 完全实现 |
| **SIC** | 当前仅 d=2 | d² (d=2 时为 4) | 1 | ⚠️ 部分实现 |

---

## 6. 关键设计决策

### 6.1 为什么使用类级缓存？

**优点**：
- 相同维度/设计多次使用时避免重复计算（计算成本高）
- 内存共享，减少内存占用

**注意事项**：
- 返回副本确保缓存安全
- 测试时需要 `clear_cache()` 避免状态污染

### 6.2 为什么分离 `bases` 和 `projectors`？

- **历史兼容性**：早期代码可能使用 `bases`
- **设计清晰性**：`projectors` 是实际使用的数据
- **当前实现**：`bases` 返回零矩阵（占位符）

### 6.3 为什么需要 `groups`？

**用途**：
1. **按组归一化**：MUB 中同一基的投影算符概率和应为 1
2. **物理意义**：确保测量概率满足物理约束

**示例**（d=4 MUB）：
```
groups = [0,0,0,0, 1,1,1,1, 2,2,2,2, 3,3,3,3, 4,4,4,4]
         └─基0─┘  └─基1─┘  └─基2─┘  └─基3─┘  └─基4─┘

归一化规则：
  sum(p[0:4]) = 1   # 基 0
  sum(p[4:8]) = 1   # 基 1
  ...
```

---

## 7. 使用示例

### 7.1 基本使用

```python
from qtomography.domain.projectors import ProjectorSet

# 创建投影算符集合
ps = ProjectorSet.get(dimension=4, design="mub")

# 获取测量矩阵（用于线性重构）
M = ps.measurement_matrix  # (20, 16)

# 获取投影算符（用于 WLS 重构）
E = ps.projectors  # (20, 4, 4)

# 获取分组信息（用于归一化）
groups = ps.groups  # (20,)
```

### 7.2 在重构器中使用

```python
from qtomography.domain.reconstruction.linear import LinearReconstructor

# 创建重构器（内部自动创建 ProjectorSet）
reconstructor = LinearReconstructor(
    dimension=4,
    design="mub",
    cache_projectors=True  # 使用缓存
)

# 执行重构
probabilities = np.array([...])  # (20,)
density_matrix = reconstructor.reconstruct(probabilities)
```

---

## 8. 总结

### 8.1 核心职责
1. **统一接口**：为不同测量设计提供一致的访问接口
2. **性能优化**：类级缓存避免重复计算
3. **数据管理**：提供测量矩阵、投影算符、分组信息

### 8.2 在系统中的位置
```
┌─────────────────┐
│   用户/配置层    │
└────────┬────────┘
         │ 配置 dimension, design
         ▼
┌─────────────────┐
│  Controller     │ 应用层
└────────┬────────┘
         │ 创建重构器
         ▼
┌─────────────────┐
│  Linear/WLS     │ 领域层 - 重构算法
│  Reconstructor  │
└────────┬────────┘
         │ 使用 ProjectorSet
         ▼
┌─────────────────┐
│  ProjectorSet   │ 领域层 - 测量基础设施
└────────┬────────┘
         │ 委托构建
         ▼
┌─────────────────┐
│  MUB/SIC        │ 领域层 - 具体实现
│  Builders       │
└─────────────────┘
```

### 8.3 设计优势
- ✅ **可扩展性**：易于添加新的测量设计
- ✅ **性能优化**：缓存机制避免重复计算
- ✅ **接口统一**：不同设计使用相同的访问方式
- ✅ **向后兼容**：保留 `bases` 属性
- ✅ **线程安全考虑**：副本机制避免并发问题

---

## 9. 潜在改进方向

1. **缓存策略**：当前无大小限制，大维度可能占用大量内存
2. **异步构建**：对于大维度，可以考虑异步构建
3. **序列化**：支持将缓存持久化到磁盘
4. **验证机制**：添加投影算符的完备性验证（∑E_i = I？）

---

**文档版本**: 1.0  
**最后更新**: 2025-01-XX  
**作者**: Auto Analysis

