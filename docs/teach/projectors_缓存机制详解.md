# ProjectorSet 缓存机制详解

> **文档目的**：深入分析 `ProjectorSet` 类的缓存实现，包括缓存内容、策略、生命周期和性能影响。

---

## 1. 缓存数据结构

### 1.1 缓存定义

```python
# 类级缓存变量
_CACHE: ClassVar[dict[tuple[int, str], Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]] = {}
```

**结构说明**：
- **类型**：类级变量（`ClassVar`），所有 `ProjectorSet` 实例共享
- **键 (Key)**：`(dimension, design)` 元组
  - `dimension`: `int` - 希尔伯特空间维度（如 2, 3, 4, 16）
  - `design`: `str` - 测量设计名称（"mub", "sic", "nopovm"）
- **值 (Value)**：4 元组 `(bases, projectors, measurement_matrix, groups)`
  - `bases`: `np.ndarray` - 基向量 `(d, d)` - 当前为占位符（全零）
  - `projectors`: `np.ndarray` - 投影算符 `(m, d, d)`
  - `measurement_matrix`: `np.ndarray` - 测量矩阵 `(m, d*d)`
  - `groups`: `np.ndarray` - 分组标识 `(m,)`

### 1.2 缓存示例

```python
# 缓存可能包含的内容（示例）
_CACHE = {
    (2, "mub"): (
        bases=np.zeros((2, 2), dtype=complex),
        projectors=np.array([...]),      # (6, 2, 2) - MUB 有 6 个投影算符
        measurement_matrix=np.array([...]),  # (6, 4)
        groups=np.array([0,0,0,1,1,1])      # 2 个组
    ),
    (2, "sic"): (
        bases=np.zeros((2, 2), dtype=complex),
        projectors=np.array([...]),      # (4, 2, 2) - SIC 有 4 个投影算符
        measurement_matrix=np.array([...]),  # (4, 4)
        groups=np.array([0,0,0,0])        # 1 个组
    ),
    (2, "nopovm"): (
        bases=np.zeros((2, 2), dtype=complex),
        projectors=np.array([...]),      # (4, 2, 2) - nopovm 有 4 个投影算符
        measurement_matrix=np.array([...]),  # (4, 4)
        groups=np.array([0,0,0,0])        # 1 个组
    ),
    (4, "mub"): (
        bases=np.zeros((4, 4), dtype=complex),
        projectors=np.array([...]),      # (20, 4, 4) - MUB 有 20 个投影算符
        measurement_matrix=np.array([...]),  # (20, 16)
        groups=np.array([...])           # 5 个组
    ),
    # ... 更多维度/设计的组合
}
```

---

## 2. 缓存策略

### 2.1 缓存查找逻辑

```python
def __init__(self, dimension: int, *, design: str = "mub", cache: bool = True):
    # 1. 构建缓存键
    key = (dimension, design.lower())  # 注意：design 转换为小写
    
    # 2. 检查缓存
    if cache and key in self._CACHE:
        # ✅ 缓存命中：直接使用缓存数据
        bases, projectors, measurement, groups = self._CACHE[key]
    else:
        # ❌ 缓存未命中：计算新数据
        if design == "mub":
            mub = build_mub_projectors(dimension)
            # ... 构建数据
        # ... 其他设计
        
        # 3. 存入缓存（如果启用缓存）
        if cache:
            self._CACHE[key] = (bases, projectors, measurement, groups)
    
    # 4. 创建防御性副本（确保缓存安全）
    self._bases = bases.copy()
    self._projectors = projectors.copy()
    self._measurement_matrix = measurement.copy()
    self._groups = groups.copy()
```

### 2.2 缓存策略特点

| 特性 | 当前实现 | 说明 |
|------|---------|------|
| **缓存类型** | 类级缓存 | 所有实例共享同一个 `_CACHE` 字典 |
| **缓存键** | `(dimension, design)` | 基于维度+设计组合 |
| **缓存大小** | 无限制 | 会一直增长，直到程序结束或手动清空 |
| **缓存过期** | 无过期机制 | 数据永久有效 |
| **线程安全** | 未明确保护 | 在单线程环境中安全，多线程可能有问题 |
| **内存管理** | 手动管理 | 只能通过 `clear_cache()` 清空 |

### 2.3 缓存控制参数

```python
# 1. 启用缓存（默认）
ps1 = ProjectorSet(dimension=4, design="mub", cache=True)
# 或使用便捷方法
ps2 = ProjectorSet.get(dimension=4, design="mub")  # cache=True 是默认值

# 2. 禁用缓存（每次重新计算）
ps3 = ProjectorSet(dimension=4, design="mub", cache=False)

# 3. 手动清空缓存
ProjectorSet.clear_cache()
```

---

## 3. 缓存生命周期

### 3.1 缓存创建时机

```python
# 场景 1：首次使用某个 (dimension, design) 组合
ps1 = ProjectorSet.get(4, design="mub")
# → 计算并缓存 (4, "mub")

# 场景 2：使用相同组合（缓存命中）
ps2 = ProjectorSet.get(4, design="mub")
# → 直接从缓存读取，不重新计算

# 场景 3：不同维度
ps3 = ProjectorSet.get(2, design="mub")
# → 计算并缓存 (2, "mub")，不影响 (4, "mub") 的缓存

# 场景 4：不同设计
ps4 = ProjectorSet.get(4, design="sic")
# → 计算并缓存 (4, "sic")，不影响 (4, "mub") 的缓存
```

### 3.2 缓存销毁时机

```python
# 方式 1：手动清空（推荐用于测试）
ProjectorSet.clear_cache()

# 方式 2：程序结束
# Python 解释器退出时，所有类级变量自动销毁

# 方式 3：模块重新加载
# importlib.reload() 会重新初始化类级变量（开发/测试场景）
```

---

## 4. 缓存安全性机制

### 4.1 防御性副本策略

**问题**：如果直接返回缓存中的数组，外部修改会污染缓存。

**解决方案**：两层防御性副本

```python
# 第一层：实例存储副本
self._bases = bases.copy()              # 从缓存拷贝
self._projectors = projectors.copy()
self._measurement_matrix = measurement.copy()
self._groups = groups.copy()

# 第二层：属性返回副本
@property
def projectors(self) -> np.ndarray:
    return self._projectors.copy()  # 再次拷贝
```

**效果**：
```
缓存数据 → [第一层副本] → 实例属性 → [第二层副本] → 用户使用
         (不受外部修改影响)        (可以自由修改)
```

### 4.2 内存影响

假设维度为 `d`，不同类型的数据大小：

| 数据类型 | 形状 | 内存大小（复数，16 字节/元素） |
|---------|------|------------------------------|
| `bases` | `(d, d)` | `16 * d²` 字节 |
| `projectors` (MUB) | `((d+1)*d, d, d)` | `16 * (d+1) * d³` 字节 |
| `measurement_matrix` (MUB) | `((d+1)*d, d²)` | `16 * (d+1) * d³` 字节 |
| `groups` (MUB) | `((d+1)*d,)` | `8 * (d+1) * d` 字节 |

**示例**（维度 4，MUB）：
- `bases`: 16 × 16 = 256 字节
- `projectors`: 16 × 20 × 16 = 5,120 字节
- `measurement_matrix`: 16 × 20 × 16 = 5,120 字节
- `groups`: 8 × 20 = 160 字节
- **总计约 10.5 KB**（单次缓存）

**内存增长**：
- 如果使用多个维度（2, 3, 4, 8, 16）和多个设计（mub, sic, nopovm）
- 缓存可能占用几百 KB 到几 MB（通常可接受）

---

## 5. 性能分析

### 5.1 缓存命中率

```python
# 典型使用场景
for dim in [2, 3, 4, 8, 16]:
    for design in ["mub", "sic", "nopovm"]:
        ps = ProjectorSet.get(dim, design=design)
        # 第一次：缓存未命中，需要计算（慢）
        # 后续：缓存命中，直接读取（快）

# 在重构循环中
for i in range(1000):
    reconstructor = LinearReconstructor(dimension=4, design="mub")
    # 每次都使用相同的 (4, "mub")
    # → 缓存命中率：100%（除了第一次）
```

### 5.2 性能对比

| 操作 | 无缓存 | 有缓存（首次） | 有缓存（命中） |
|------|--------|---------------|---------------|
| 计算投影算符（d=4, MUB） | ~50ms | ~50ms | **< 1ms** ⚡ |
| 内存访问 | 一次 | 一次计算 + 一次存储 | 仅一次读取 |
| 内存使用 | 每次释放 | 累积增长 | 无额外开销 |

### 5.3 性能优化建议

1. **预加载常用维度**
   ```python
   # 在程序启动时预加载
   for dim in [2, 4, 8]:
       ProjectorSet.get(dim, design="mub")
       ProjectorSet.get(dim, design="nopovm")
   ```

2. **避免频繁清空缓存**
   ```python
   # ❌ 不好：每次测试都清空
   ProjectorSet.clear_cache()
   ps = ProjectorSet.get(4)
   
   # ✅ 好：只在必要时清空
   if need_fresh_data:
       ProjectorSet.clear_cache()
   ```

---

## 6. 缓存使用示例

### 6.1 基本使用

```python
from qtomography.domain.projectors import ProjectorSet

# 使用缓存（推荐）
ps1 = ProjectorSet.get(dimension=4, design="mub")
ps2 = ProjectorSet.get(dimension=4, design="mub")  # 从缓存读取

# 验证缓存生效
print(ps1 is ps2)  # False（不同实例）
print(np.array_equal(ps1.measurement_matrix, ps2.measurement_matrix))  # True
```

### 6.2 禁用缓存

```python
# 测试场景：需要独立的数据
ps_no_cache = ProjectorSet(dimension=4, design="mub", cache=False)
# 不会使用缓存，也不会存入缓存
```

### 6.3 清空缓存

```python
# 测试前清空
ProjectorSet.clear_cache()

# 运行测试
ps1 = ProjectorSet.get(4)
ps2 = ProjectorSet.get(4)

# 验证缓存
assert len(ProjectorSet._CACHE) == 1  # 只有一个条目
```

---

## 7. 潜在问题和改进方向

### 7.1 当前限制

1. **无大小限制**：缓存可能无限增长（虽然通常不是问题）
2. **无过期机制**：数据永不过期（可能需要内存优化）
3. **无线程保护**：多线程环境可能不安全
4. **无 LRU 机制**：无法自动淘汰不常用的缓存

### 7.2 可能的改进

参考 `projectors_optimized.py`（如果存在）：

```python
# 改进方向 1：LRU 缓存
class ProjectorSet:
    _CACHE = ProjectorLRUCache(max_bytes=1024*1024*1024)  # 1GB 限制

# 改进方向 2：线程安全
import threading
_CACHE_LOCK = threading.RLock()
with _CACHE_LOCK:
    # 缓存操作

# 改进方向 3：缓存统计
@classmethod
def get_cache_stats(cls):
    return {
        "size": len(cls._CACHE),
        "keys": list(cls._CACHE.keys()),
        "memory_bytes": sum(...)  # 计算内存占用
    }
```

---

## 8. 总结

### 8.1 缓存机制特点

- ✅ **类级共享**：所有实例共享，避免重复计算
- ✅ **简单高效**：字典查找 O(1)，性能优秀
- ✅ **安全性好**：防御性副本防止污染
- ⚠️ **无大小限制**：长期运行可能占用内存
- ⚠️ **无过期机制**：数据永久有效

### 8.2 适用场景

| 场景 | 是否使用缓存 | 原因 |
|------|------------|------|
| 生产环境 | ✅ 是 | 避免重复计算，提升性能 |
| 单元测试 | ⚠️ 视情况 | 测试隔离可能需要清空缓存 |
| 性能测试 | ✅ 是 | 测试真实性能表现 |
| 调试模式 | ⚠️ 视情况 | 可能需要禁用缓存以获取新数据 |

### 8.3 最佳实践

1. **默认启用缓存**（`cache=True`）
2. **使用 `get()` 方法**便捷访问
3. **测试前清空缓存**确保隔离
4. **避免频繁 `clear_cache()`**
5. **长期运行监控内存**（如果使用大量维度）

---

**文档版本**: 1.0  
**最后更新**: 2025-01-XX  
**相关文件**: `qtomography/domain/projectors.py`

