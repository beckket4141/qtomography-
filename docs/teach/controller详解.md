# Controller 详解 - 应用层编排的艺术

> 深入理解 `qtomography/app/controller.py`：批处理流程编排、设计模式与最佳实践

---

## 📋 目录

1. [模块概览](#模块概览)
2. [核心类和数据结构](#核心类和数据结构)
3. [设计模式深度解析](#设计模式深度解析)
4. [批处理流程详解](#批处理流程详解)
5. [关键Python知识点](#关键python知识点)
6. [使用场景与最佳实践](#使用场景与最佳实践)

---

## 模块概览

### 🎯 Controller 的职责

`controller.py` 是**应用层（Application Layer）的核心**，负责：

```
┌─────────────────────────────────────────────────┐
│           ReconstructionController               │
│                                                   │
│  职责：                                          │
│  1. 接收配置（ReconstructionConfig）            │
│  2. 加载数据（CSV/Excel）                        │
│  3. 编排算法（Linear、MLE）                      │
│  4. 持久化结果（JSON、CSV）                      │
│  5. 生成报告（SummaryResult）                    │
└─────────────────────────────────────────────────┘
         ↓ 依赖                    ↓ 依赖
┌──────────────────┐      ┌──────────────────┐
│ LinearReconstructor│      │ MLEReconstructor │
│  (领域层)         │      │  (领域层)        │
└──────────────────┘      └──────────────────┘
```

### 📦 分层架构（含 Bell 分析）

| 层级 | 组件 | 职责 |
|-----|------|-----|
| **接口层** | CLI、GUI | 用户交互 |
| **应用层** | **Controller** | 流程编排、配置管理、可选分析编排 |
| **领域层 - 重构** | LinearReconstructor、MLEReconstructor | 量子态重构算法 |
| **领域层 - 核心** | DensityMatrix、ProjectorSet | 密度矩阵和投影算子 |
| **领域层 - 分析** | **BellAnalysis** | 量子态特性分析（Bell 态保真度） |
| **基础设施层** | Repository、Visualizer | 持久化和可视化 |

**说明**：Bell 分析是领域层的可选分析功能，由应用层（Controller）根据配置决定是否调用

---

## 核心类和数据结构

### 1. `ReconstructionConfig` - 配置类

#### 💡 知识点：`dataclass` 的高级用法

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)  # frozen=True → 不可变配置
class ReconstructionConfig:
    input_path: Path
    output_dir: Path
    methods: Sequence[str] = ("linear", "mle")
    dimension: Optional[int] = None
    sheet: Optional[Union[str, int]] = None
    linear_regularization: Optional[float] = None
    mle_regularization: Optional[float] = None
    mle_max_iterations: int = 2000
    tolerance: float = 1e-9
    cache_projectors: bool = True
    analyze_bell: bool = False  # ← Bell 态分析开关
    # ... 更多参数
```

**analyze_bell 参数说明**：
- **类型**：`bool`
- **默认值**：`False`（不执行）
- **作用**：在每次重构后自动执行 Bell 态保真度分析
- **适用场景**：纠缠态量子系统的重构验证（如 2-qubit Bell 态、GHZ 态）
- **输出指标**：
  - `bell_max_fidelity`: 与最相似 Bell 态的保真度
  - `bell_avg_fidelity`: 与所有 Bell 态的平均保真度
  - `bell_dominant_index`: 主导的 Bell 态索引（识别具体是哪个 Bell 态）
  - `bell_dimension`: 系统总维度
  - `bell_local_dimension`: 局域维度（如 2-qubit 系统中每个 qubit 的维度）
- **注意**：要求系统维度是完全平方数（如 4, 9, 16），否则自动跳过分析
```

**关键特性**：

| 特性 | 说明 | 好处 |
|-----|------|-----|
| `frozen=True` | 实例不可修改 | 防止配置被意外修改，线程安全 |
| `dataclass` | 自动生成 `__init__`、`__repr__` | 减少样板代码 |
| 类型标注 | `input_path: Path` | 提高代码可读性，支持静态检查 |

#### 🔧 `__post_init__` 的妙用

```python
def __post_init__(self) -> None:
    # frozen=True 禁止 self.attribute = value
    # 必须使用 object.__setattr__
    object.__setattr__(self, "input_path", Path(self.input_path))
    
    # 验证逻辑
    if self.dimension is not None and self.dimension < 2:
        raise ValueError("dimension must be >= 2 if provided")
```

**为什么用 `object.__setattr__`？**

```python
# ❌ 这样会报错（frozen=True）
self.input_path = Path(self.input_path)  
# FrozenInstanceError: cannot assign to field 'input_path'

# ✅ 正确做法（绕过 frozen 限制）
object.__setattr__(self, "input_path", Path(self.input_path))
```

---

### 2. `SummaryResult` - 结果类

```python
@dataclass  # 注意：没有 frozen=True（可变）
class SummaryResult:
    summary_path: Path
    records_dir: Path
    num_samples: int
    methods: Tuple[str, ...]
    rows: List[dict]
    
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)
```

**为什么不是 `frozen`？**

- 配置类（Config）→ `frozen=True`（不应被修改）
- 结果类（Result）→ 可变（可能需要后处理）

---

### 3. `ReconstructionController` - 核心控制器

```python
class ReconstructionController:
    def run_batch(self, config: ReconstructionConfig) -> SummaryResult:
        # [1] 准备阶段
        # [2] 初始化阶段
        # [3] 批处理阶段
        # [4] 汇总阶段
        pass
```

---

## 设计模式深度解析

### 🎭 设计模式 1: 门面模式（Facade Pattern）

**问题**：领域层的接口复杂，用户需要了解太多细节

```python
# ❌ 没有 Controller 时：用户需要手动编排
from qtomography.domain.reconstruction.linear import LinearReconstructor
from qtomography.domain.reconstruction.mle import MLEReconstructor
from qtomography.infrastructure.persistence import ResultRepository

# 用户需要知道：
# 1. 如何创建 Reconstructor
# 2. 如何加载数据
# 3. 如何保存结果
# 4. 如何生成报告
linear = LinearReconstructor(dimension=4, ...)
data = pd.read_csv("data.csv").to_numpy()
for idx in range(data.shape[1]):
    result = linear.reconstruct(data[:, idx])
    # ... 手动保存 ...
```

**解决方案**：Controller 提供简化的接口

```python
# ✅ 有 Controller 时：一行代码完成
from qtomography.app.controller import ReconstructionConfig, run_batch

config = ReconstructionConfig(
    input_path="data.csv",
    output_dir="output/",
    methods=["linear", "mle"],
)
result = run_batch(config)  # 完成！
```

---

### 🎨 设计模式 2: 策略模式（Strategy Pattern）

**核心思想**：算法可以动态选择和切换

```python
# 策略接口（鸭子类型，无需显式定义）
# 任何有 reconstruct_with_details() 的对象都是"重构器"

# 策略 1：线性重构
linear: Optional[LinearReconstructor] = None
if "linear" in config.methods:
    linear = LinearReconstructor(...)

# 策略 2：MLE 重构
mle: Optional[MLEReconstructor] = None
if "mle" in config.methods:
    mle = MLEReconstructor(...)

# 动态调用策略
if linear is not None:
    result = linear.reconstruct_with_details(probs)
if mle is not None:
    result = mle.reconstruct_with_details(probs)
```

**扩展性**：新增算法无需修改 Controller

```python
# 未来添加 HMLE 只需：
if "hmle" in config.methods:
    hmle = HMLEReconstructor(...)
    result = hmle.reconstruct_with_details(probs)
```

---

### 📐 设计模式 3: 模板方法模式（Template Method）

**核心思想**：定义算法骨架，细节可变

```python
def run_batch(self, config):
    # ========== 模板骨架 ==========
    # [1] 准备阶段（固定）
    self._prepare_config(config)
    data = _load_probabilities(...)
    
    # [2] 初始化阶段（可变：根据 config.methods）
    linear = self._create_linear(...) if "linear" in config.methods else None
    mle = self._create_mle(...) if "mle" in config.methods else None
    
    # [3] 批处理阶段（固定）
    for sample in data:
        if linear: process_with_linear(sample)
        if mle: process_with_mle(sample)
    
    # [4] 汇总阶段（固定）
    return self._create_summary(...)
```

---

## 批处理流程详解

### 🔄 完整流程图

```
┌─────────────────────────────────────────────────┐
│  [1] 准备阶段                                    │
│  - _prepare_config(): 创建输出目录              │
│  - _load_probabilities(): 加载 CSV/Excel        │
│  - _infer_dimension(): 推断系统维度             │
└─────────────────────┬───────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  [2] 初始化阶段                                  │
│  - 创建 ResultRepository（持久化仓库）          │
│  - 实例化 LinearReconstructor（如果启用）       │
│  - 实例化 MLEReconstructor（如果启用）          │
└─────────────────────┬───────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  [3] 批处理阶段（循环处理每个样本）             │
│  ┌─────────────────────────────────────────┐   │
│  │  对每个样本：                            │   │
│  │  1. 提取概率向量 probs                   │   │
│  │  2. 执行线性重构（如果启用）             │   │
│  │     - 调用 linear.reconstruct_with_details() │
│  │     - 执行 Bell 分析（如果 analyze_bell） ← 新增
│  │     - 保存结果为 JSON                    │   │
│  │     - 添加指标到 summary_rows            │   │
│  │  3. 执行 MLE 重构（如果启用）            │   │
│  │     - 使用线性结果作为初始值（智能初始化）│  │
│  │     - 调用 mle.reconstruct_with_details()│   │
│  │     - 执行 Bell 分析（如果 analyze_bell） ← 新增
│  │     - 保存结果为 JSON                    │   │
│  │     - 添加指标到 summary_rows            │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  [4] 汇总阶段                                    │
│  - 将 summary_rows 写入 summary.csv             │
│  - 返回 SummaryResult 对象                      │
└─────────────────────────────────────────────────┘
```

---

### 💡 关键设计亮点

#### 亮点 1: 智能初始化

```python
# MLE 使用线性结果作为初始点（提高收敛速度）
if mle is not None:
    initial_density = (
        linear_result.density.matrix  # 如果有线性结果
        if linear_result is not None 
        else None  # 否则用单位矩阵
    )
    mle_result = mle.reconstruct_with_details(
        probs,
        initial_density=initial_density,
    )
```

**好处**：

- 线性结果通常已经接近真实解
- MLE 从更好的初始点开始，收敛更快
- 如果只运行 MLE，自动使用默认初始化

---

#### 亮点 2: 投影算子缓存

```python
linear = LinearReconstructor(
    dimension,
    cache_projectors=True,  # 批处理推荐 True
)

# 效果：
# - 首次调用：计算并缓存投影算子矩阵（耗时）
# - 后续调用：直接使用缓存（快速）
# - 批处理 100 个样本：只计算一次投影算子
```

**性能对比**：

| 场景 | 缓存关闭 | 缓存开启 | 加速比 |
|-----|---------|---------|--------|
| 单个样本 | 1.0s | 1.0s | 1x |
| 100 个样本 | 100s | 10s | 10x |

---

#### 亮点 3: 元数据追溯

```python
metadata = {
    "source_file": config.input_path.name,  # 例："experiment_1.csv"
    "sample_index": idx,                     # 例：0, 1, 2, ...
}

record = _create_record(
    method="mle",
    dimension=4,
    probabilities=probs,
    density_matrix=rho,
    metrics={"purity": 0.99},
    metadata=metadata,  # 保存来源信息
)
```

**好处**：

- 每个结果都能追溯到源文件和样本索引
- 便于后续分析和调试
- 符合科学研究的可重现性要求

---

#### 亮点 4: 可选的 Bell 态分析

```python
# 启用 Bell 态分析
config = ReconstructionConfig(
    input_path="entangled_data.csv",
    output_dir="results/",
    methods=["mle"],
    dimension=4,  # 2-qubit 系统
    analyze_bell=True,  # ← 开启 Bell 态分析
)

result = run_batch(config)

# 效果：
# - 每个重构态自动与标准 Bell 基比较
# - 计算与各 Bell 态的保真度
# - 识别主导的 Bell 态分量
# - 指标自动写入 JSON 和 CSV
```

**实现机制**：

```python
# 在 Controller 内部（伪代码）
if config.analyze_bell:
    try:
        bell_result = analyze_density_matrix(
            reconstructed_density,
            dimension=dimension
        )
        bell_metrics = bell_result.to_dict()
        # 将 Bell 指标添加到 record.metrics
        record.metrics.update({
            f"bell_{key}": value
            for key, value in bell_metrics.items()
        })
    except ValueError:
        # 维度不匹配（非完全平方数），跳过分析
        pass
```

**好处**：

- ✅ **自动化分析**：无需手动调用 Bell 分析函数
- ✅ **纠缠态验证**：快速评估重构态的纠缠特性
- ✅ **主导态识别**：自动找出最相似的 Bell 态
- ✅ **统一存储**：Bell 指标与重构指标一起保存
- ✅ **批量处理**：对所有样本统一分析
- ✅ **容错设计**：维度不匹配时自动跳过，不影响重构流程

**适用场景**：

| 场景 | 说明 | 示例系统 |
|-----|------|----------|
| 纠缠态重构 | 验证 Bell 态、GHZ 态等纠缠态的重构质量 | 2-qubit: dim=4 |
| 量子通信实验 | 评估纠缠光子对的保真度 | 光子纠缠源 |
| 量子计算验证 | 检查量子门操作后的态是否接近目标 Bell 态 | CNOT 门输出 |
| 噪声分析 | 研究噪声对纠缠态的影响 | 去相干实验 |

**输出指标示例**：

```json
{
  "method": "mle",
  "purity": 0.987,
  "trace": 1.000,
  "bell_dimension": 4,
  "bell_local_dimension": 2,
  "bell_max_fidelity": 0.965,
  "bell_min_fidelity": 0.012,
  "bell_avg_fidelity": 0.256,
  "bell_dominant_index": 0
}
```

**Bell 态索引对照**（2-qubit 系统）：

| 索引 | Bell 态 | 标准表示 |
|-----|---------|----------|
| 0 | \|Φ⁺⟩ | (&#124;00⟩ + &#124;11⟩) / √2 |
| 1 | \|Φ⁻⟩ | (&#124;00⟩ - &#124;11⟩) / √2 |
| 2 | \|Ψ⁺⟩ | (&#124;01⟩ + &#124;10⟩) / √2 |
| 3 | \|Ψ⁻⟩ | (&#124;01⟩ - &#124;10⟩) / √2 |

---

## 关键Python知识点

### 知识点 1: `Optional[Type]` 的使用

```python
from typing import Optional

linear: Optional[LinearReconstructor] = None
# 等价于：linear: Union[LinearReconstructor, None] = None

if "linear" in config.methods:
    linear = LinearReconstructor(...)

# 使用时需要检查
if linear is not None:
    result = linear.reconstruct_with_details(probs)
```

**类型检查器（mypy）会确保你检查了 None**：

```python
# ❌ 错误：可能是 None
result = linear.reconstruct_with_details(probs)  # mypy 报错

# ✅ 正确：先检查
if linear is not None:
    result = linear.reconstruct_with_details(probs)
```

---

### 知识点 2: `Path` vs `str`

```python
from pathlib import Path

# ❌ 旧方式（字符串）
import os
path = "output/records/result.json"
os.makedirs(os.path.dirname(path), exist_ok=True)
full_path = os.path.join(path, "file.txt")

# ✅ 新方式（Path）
path = Path("output/records/result.json")
path.parent.mkdir(parents=True, exist_ok=True)  # 创建父目录
full_path = path / "file.txt"  # 使用 / 拼接路径
```

**Path 的优势**：

| 特性 | 字符串 | Path |
|-----|--------|------|
| 跨平台 | ❌（需手动处理 `/` vs `\`） | ✅ 自动处理 |
| 可读性 | ❌ `os.path.join(a, b, c)` | ✅ `a / b / c` |
| 类型安全 | ❌ 容易拼错 | ✅ IDE 自动补全 |
| 操作便捷 | ❌ 需要 `os` 模块 | ✅ 内置方法 |

---

### 知识点 3: 列表推导式 vs 字典推导式

```python
# 列表推导式（生成列表）
summary_rows = [
    {"sample": idx, "method": "linear", "purity": purity}
    for idx, purity in enumerate(purities)
]

# 字典推导式（类型转换）
metrics = {
    str(k): float(v) if isinstance(v, (int, float)) else v
    for k, v in metrics.items()
}

# 集合推导式（去重）
tokens = {m for m in methods}
```

---

### 知识点 4: `@staticmethod` 的使用场景

```python
class ReconstructionController:
    @staticmethod
    def _prepare_config(config):
        # 不需要访问 self
        output_dir = config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        return config
```

**何时使用 `@staticmethod`？**

| 情况 | 使用 | 说明 |
|-----|------|-----|
| 需要访问 `self` | 普通方法 | 访问实例属性/方法 |
| 不需要 `self`，但逻辑相关 | `@staticmethod` | 工具方法，放在类内组织 |
| 不需要 `self`，逻辑独立 | 模块级函数 | 例：`_load_probabilities()` |

---

### 知识点 5: 类型转换的防御式编程

```python
def _create_record(metrics: dict, metadata: Optional[dict]) -> ReconstructionRecord:
    return ReconstructionRecord(
        # 确保 metrics 中的数值都是 Python float
        # （避免 numpy.float64 导致 JSON 序列化失败）
        metrics={
            str(k): float(v) if isinstance(v, (int, float)) else v
            for k, v in metrics.items()
        },
        # 确保 metadata 中的值都是字符串
        metadata={
            str(k): str(v)
            for k, v in (metadata or {}).items()
        },
    )
```

**为什么需要？**

```python
import numpy as np
import json

value = np.float64(0.99)
json.dumps({"purity": value})  # ❌ TypeError: Object of type float64 is not JSON serializable

value = float(np.float64(0.99))
json.dumps({"purity": value})  # ✅ '{"purity": 0.99}'
```

---

## 使用场景与最佳实践

### 场景 1: 单次重构任务

```python
from qtomography.app.controller import ReconstructionConfig, run_batch

config = ReconstructionConfig(
    input_path="data.csv",
    output_dir="results/",
    methods=["mle"],
    dimension=4,
)

result = run_batch(config)
print(f"完成 {result.num_samples} 个样本")
```

---

### 场景 2: 对比多种算法

```python
config = ReconstructionConfig(
    input_path="data.csv",
    output_dir="results/",
    methods=["linear", "mle"],  # 同时运行两种算法
)

result = run_batch(config)
df = result.to_dataframe()

# 分析对比
print(df.groupby('method')['purity'].describe())
```

---

### 场景 3: 批量处理多个文件

```python
from pathlib import Path

input_dir = Path("experiments/")
for csv_file in input_dir.glob("*.csv"):
    config = ReconstructionConfig(
        input_path=csv_file,
        output_dir=f"results/{csv_file.stem}/",
        methods=["mle"],
    )
    result = run_batch(config)
    print(f"✅ {csv_file.name}: {result.num_samples} 个样本完成")
```

---

### 场景 4: 自定义正则化参数

```python
config = ReconstructionConfig(
    input_path="noisy_data.csv",
    output_dir="results/",
    methods=["linear", "mle"],
    linear_regularization=1e-6,  # Tikhonov 正则化
    mle_regularization=1e-5,     # 纯度惩罚
)

result = run_batch(config)
```

---

### 场景 5: Bell 态分析（纠缠态验证）

```python
# 场景：验证纠缠光子对的重构质量
config = ReconstructionConfig(
    input_path="bell_pair_measurements.csv",
    output_dir="bell_results/",
    methods=["linear", "mle"],
    dimension=4,  # 2-qubit 系统
    analyze_bell=True,  # ← 启用 Bell 态分析
)

result = run_batch(config)

# 查看 Bell 态保真度
df = result.to_dataframe()

print("=" * 50)
print("Linear 重构的 Bell 态分析：")
linear_df = df[df['method'] == 'linear']
print(f"  平均最大保真度: {linear_df['bell_max_fidelity'].mean():.3f}")
print(f"  主导 Bell 态: {linear_df['bell_dominant_index'].mode()[0]}")

print("\nMLE 重构的 Bell 态分析：")
mle_df = df[df['method'] == 'mle']
print(f"  平均最大保真度: {mle_df['bell_max_fidelity'].mean():.3f}")
print(f"  主导 Bell 态: {mle_df['bell_dominant_index'].mode()[0]}")

# 输出示例：
# ==================================================
# Linear 重构的 Bell 态分析：
#   平均最大保真度: 0.945
#   主导 Bell 态: 0
#
# MLE 重构的 Bell 态分析：
#   平均最大保真度: 0.987
#   主导 Bell 态: 0

# 结论：
# 1. MLE 重构的 Bell 态保真度更高（接近理论值）
# 2. 主导的 Bell 态索引为 0，对应 |Φ⁺⟩ = (|00⟩ + |11⟩)/√2
# 3. 说明实验制备的是 |Φ⁺⟩ 纠缠态
# 4. MLE 对纠缠态的重构效果优于线性方法
```

---

## Bell 分析如何协同

- 当 `ReconstructionConfig.analyze_bell=True` 时，控制器会在保存 JSON 记录前调用 `qtomography.analysis.bell.analyze_density_matrix`，并将 \`bell_max_fidelity\`、\`bell_avg_fidelity\` 等指标写入 `record.metrics` 与 `summary.csv`。
- 该分析层只依赖领域层产出的 `DensityMatrix`，不会改变线性/MLE 的收敛结果，是可选的附属功能。
- 如果维度不是完全平方数（如 6、8），分析会自动跳过并记录日志，重构流程照常完成。
- CLI (`--bell`) 和脚本（`--bell` 参数）都通过此机制触发分析；批处理历史数据则可以使用 `qtomography bell-analyze` 读取 JSON 目录后追补指标。

## DDD 分层复盘

| 层级 | 组件/模块 | 说明 |
| --- | --- | --- |
| **领域层** | `DensityMatrix`、`Linear/MLEReconstructor`、`analysis.bell` | 核心算法与指标计算能力（包含内置保真度运算）。 |
| **应用层** | `ReconstructionController`、CLI | 编排重构流程，并按需触发分析层。 |
| **基础设施层** | `ResultRepository`、可视化模块 | 持久化、可视化、外部适配器。 |

加入分析层后，整体仍遵循 DDD 架构：领域层提供基础能力，分析层作为可选服务，应用层负责组合调用，持久化/可视化继续作为支撑组件。

---

## 🎯 总结

### 核心设计原则

| 原则 | 应用 |
|-----|------|
| **单一职责** | Controller 只负责编排，不实现算法 |
| **开闭原则** | 新增算法无需修改 Controller |
| **依赖倒置** | 依赖抽象接口（鸭子类型），不依赖具体实现 |
| **里氏替换** | 任何重构器都可以互换（只要实现相同接口） |

---

### 关键技术点

```
1. dataclass          → 简化配置类定义
2. frozen=True        → 不可变配置，线程安全
3. Optional[Type]     → 明确可选依赖
4. Path               → 跨平台路径操作
5. 策略模式           → 动态选择算法
6. 模板方法模式       → 统一批处理流程
7. 智能初始化         → MLE 使用线性结果加速
8. 投影算子缓存       → 10x 性能提升
9. 元数据追溯         → 科学可重现性
10. 类型转换防御      → JSON 序列化安全
11. 可选分析编排      → Bell 态分析的条件调用
12. 容错设计          → 分析失败不影响重构流程
```

---

**文档版本**: v1.1 (新增 Bell 态分析章节)  
**最后更新**: 2025年10月7日  
**作者**: AI Assistant  
**难度等级**: 中级到高级

---

## 📝 更新日志

### v1.1 (2025-10-07)
- ✅ 更新分层架构，细化领域层（重构、核心、分析子层）
- ✅ 新增 `analyze_bell` 参数的详细说明
- ✅ 更新批处理流程图（包含 Bell 分析步骤）
- ✅ 新增亮点 4：可选的 Bell 态分析
- ✅ 新增场景 5：Bell 态分析的实际应用示例
- ✅ 新增 Bell 分析协同机制说明
- ✅ 新增 DDD 分层复盘章节

### v1.0 (2025-10-07)
- 初始版本：Controller 基础架构和核心功能

