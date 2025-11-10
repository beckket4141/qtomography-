# CLI 详解 - 命令行接口的艺术

> 深入理解 `qtomography/cli/main.py`：接口层设计、argparse 实战与分层架构

---

## 📋 目录

1. [CLI 在分层架构中的位置](#cli在分层架构中的位置)
2. [核心概念：argparse 深度解析](#核心概念argparse深度解析)
3. [四大子命令详解](#四大子命令详解)
4. [设计模式与最佳实践](#设计模式与最佳实践)
5. [关键 Python 知识点](#关键python知识点)
6. [使用场景与示例](#使用场景与示例)
   - 场景 1: 快速重构单个文件
   - 场景 2: 纠缠态重构与 Bell 态分析
   - 场景 3: 批量处理多个文件
   - 场景 4: 历史数据追加 Bell 态分析
   - 场景 5: 在 Python 脚本中调用 CLI
   - **场景 6: 配置文件复用** ⭐ 新增

---

## CLI在分层架构中的位置

### 🏗️ 完整的四层架构（含 Bell 分析）

```
┌─────────────────────────────────────────────────────────┐
│  【接口层 - Interface Layer】                            │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │  CLI (命令行)     │    │  GUI (图形界面)   │          │
│  │  main.py ← 当前  │    │  (计划中)         │          │
│  └────────┬─────────┘    └──────────────────┘          │
└───────────┼─────────────────────────────────────────────┘
            ↓ 调用
┌─────────────────────────────────────────────────────────┐
│  【应用层 - Application Layer】                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  ReconstructionController (controller.py)        │  │
│  │  - 流程编排  - 配置管理  - 批处理逻辑            │  │
│  └────────┬───────────────────────────────────────────┘  │
└───────────┼─────────────────────────────────────────────┘
            ↓ 调用
┌─────────────────────────────────────────────────────────┐
│  【领域层 - Domain Layer】                               │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │ LinearReconstructor│    │ MLEReconstructor │          │
│  └──────────────────┘    └──────────────────┘          │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │  DensityMatrix    │    │  ProjectorSet    │          │
│  └──────────────────┘    └──────────────────┘          │
│  ┌──────────────────────────────────────────┐          │
│  │  BellAnalysis ← 量子态特性分析           │          │
│  └──────────────────────────────────────────┘          │
└───────────┬─────────────────────────────────────────────┘
            ↓ 依赖
┌─────────────────────────────────────────────────────────┐
│  【基础设施层 - Infrastructure Layer】                   │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │ ResultRepository │    │ Visualizer       │          │
│  │  (持久化)        │    │  (可视化)        │          │
│  └──────────────────┘    └──────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

---

### 🎯 CLI 的核心职责

| 职责 | 说明 | 示例 |
|-----|------|-----|
| **参数解析** | 解析命令行参数 | `--method mle` → `"mle"` |
| **输入验证** | 检查文件是否存在 | 验证 `data.csv` 存在 |
| **类型转换** | 转换为应用层格式 | `"both"` → `("linear", "mle")` |
| **调用应用层** | 调用 Controller | `run_batch(config)` |
| **结果展示** | 友好的输出格式 | `✅ 完成：results/summary.csv` |

**CLI 不负责**：
- ❌ 实现重构算法（领域层的事）
- ❌ 编排批处理流程（应用层的事）
- ❌ 持久化结果（基础设施层的事）

---

### 🔗 完整调用链路

```python
# [1] 用户在终端输入
$ qtomography reconstruct data.csv --method mle --dimension 4 --bell

# [2] Python 入口点（安装时由 setup.py 配置）
if __name__ == "__main__":
    raise SystemExit(main())

# [3] CLI 接口层 (main.py)
def main(argv=None):
    parser = build_parser()          # 创建参数解析器
    args = parser.parse_args(argv)   # 解析参数
    return args.func(args)           # 执行对应的子命令函数

# [4] reconstruct 子命令处理函数
def _cmd_reconstruct(args):
    # 验证输入
    if not args.input.exists():
        raise SystemExit("错误：文件不存在")
    
    # 构建配置对象（应用层的数据格式）
    config = ReconstructionConfig(
        input_path=args.input,
        methods=_resolve_methods(args.method),  # "both" → ("linear", "mle")
        dimension=args.dimension,
        analyze_bell=args.bell,  # ← Bell 态分析开关
        ...
    )
    
    # 调用应用层
    result = run_batch(config)  # ← 跨层调用
    
    # 展示结果
    print(f"✅ 完成：{result.summary_path}")
    if args.bell:
        print("🔔 已完成 Bell 态保真度分析")

# [5] 应用层 (controller.py)
def run_batch(config):
    controller = ReconstructionController()
    return controller.run_batch(config)  # ← 调用领域层

# [6] 领域层 (mle.py / linear.py / bell.py)
class MLEReconstructor:
    def reconstruct_with_details(self, probs):
        # 执行量子态重构算法
        ...
        
# Bell 分析（如果启用）
if config.analyze_bell:
    bell_result = analyze_density_matrix(density)
```

---

## 核心概念：argparse深度解析

### 📚 argparse 基础架构

```python
import argparse

# ========== 第 1 步：创建主解析器 ==========
parser = argparse.ArgumentParser(
    prog="qtomography",                    # 程序名（显示在帮助信息中）
    description="量子态重构工具集",        # 程序描述
)

# ========== 第 2 步：创建子命令解析器 ==========
subparsers = parser.add_subparsers(
    dest="command"  # 将选择的子命令存储到 args.command
)

# ========== 第 3 步：添加子命令 ==========
reconstruct = subparsers.add_parser(
    "reconstruct",                         # 子命令名称
    help="执行量子态重构",                # 子命令帮助信息
)

# ========== 第 4 步：为子命令添加参数 ==========
reconstruct.add_argument(
    "input",                               # 位置参数（必需）
    type=Path,                             # 类型转换
    help="输入数据文件路径"                # 参数帮助信息
)

reconstruct.add_argument(
    "--method",                            # 可选参数（以 -- 开头）
    choices=["linear", "mle", "both"],    # 限制可选值
    default="both",                        # 默认值
    help="重构方法"
)

reconstruct.add_argument(
    "--bell",                              # Bell 态分析开关
    action="store_true",                   # 布尔标志（不需要值）
    help="执行 Bell 态保真度分析"
)

# ========== 第 5 步：设置处理函数 ==========
reconstruct.set_defaults(func=_cmd_reconstruct)  # 将函数绑定到子命令

# ========== 第 6 步：解析并执行 ==========
args = parser.parse_args()                # 解析命令行参数
return args.func(args)                    # 调用绑定的函数
```

---

### 🎨 子命令架构模式

```python
def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。
    
    架构：
        qtomography
        ├── reconstruct    (重构量子态)
        │   ├── input (必需位置参数)
        │   ├── --method
        │   ├── --dimension
        │   ├── --bell  ← 新增
        │   └── --output-dir
        ├── summarize      (汇总结果)
        │   ├── summary (必需位置参数)
        │   └── --metrics
        ├── bell-analyze   (Bell态分析) ← 新增
        │   ├── records_dir (必需位置参数)
        │   └── --output
        └── info           (版本信息)
    """
    parser = argparse.ArgumentParser(prog="qtomography", ...)
    subparsers = parser.add_subparsers(dest="command")
    
    # ========== 子命令 1: reconstruct ==========
    reconstruct = subparsers.add_parser("reconstruct", ...)
    reconstruct.add_argument("input", ...)
    reconstruct.add_argument("--method", ...)
    reconstruct.add_argument("--bell", action="store_true", ...)
    reconstruct.set_defaults(func=_cmd_reconstruct)
    
    # ========== 子命令 2: summarize ==========
    summarize = subparsers.add_parser("summarize", ...)
    summarize.add_argument("summary", ...)
    summarize.add_argument("--metrics", ...)
    summarize.add_argument("--compare-methods", ...)  # ⭐ Stage 3 新增
    summarize.add_argument("--detailed", ...)         # ⭐ Stage 3 新增
    summarize.add_argument("--output", ...)           # ⭐ Stage 3 新增
    summarize.set_defaults(func=_cmd_summarize)
    
    # ========== 子命令 3: bell-analyze ==========
    bell_analyze = subparsers.add_parser("bell-analyze", ...)
    bell_analyze.add_argument("records_dir", ...)
    bell_analyze.set_defaults(func=_cmd_bell_analyze)
    
    # ========== 子命令 4: info ==========
    info = subparsers.add_parser("info", ...)
    info.set_defaults(func=_cmd_info)
    
    return parser
```

**命令示例**：

```bash
# 子命令 1
qtomography reconstruct data.csv --method mle --bell

# 子命令 2：基础汇总
qtomography summarize results/summary.csv --metrics purity bell_max_fidelity

# 子命令 2：方法对比 ⭐ Stage 3 新增
qtomography summarize results/summary.csv --compare-methods --metrics purity trace

# 子命令 3
qtomography bell-analyze results/records/ --output bell_summary.csv

# 子命令 4
qtomography info
```

---

## 四大子命令详解

### 1️⃣ reconstruct - 量子态重构

#### 命令格式

```bash
qtomography reconstruct <输入文件> [选项]
```

#### 参数详解

| 参数 | 类型 | 必需 | 说明 | 示例 |
|-----|------|-----|------|-----|
| `input` | Path | ✅ | 输入数据文件（CSV/Excel） | `data.csv` |
| `--sheet` | str/int | ❌ | Excel 工作表名称或索引 | `Sheet1` 或 `0` |
| `--dimension` | int | ❌ | 希尔伯特空间维度（可自动推断） | `4` |
| `--method` | str | ❌ | 重构方法（默认：both） | `linear`, `wls`, `rhor`, `both` |
| `--output-dir` | Path | ❌ | 输出目录（默认：demo_output） | `results/` |
| `--linear-regularization` | float | ❌ | 线性重构正则化参数 | `1e-6` |
| `--mle-regularization` | float | ❌ | WLS（原 MLE）正则化参数 | `1e-5` |
| `--mle-max-iterations` | int | ❌ | WLS 最大迭代次数（默认：2000） | `5000` |
| `--wls-min-expected-clip` | float | ❌ | 最小理论概率裁剪阈值（默认：1e-12） | `1e-10` |
| `--wls-ftol` | float | ❌ | WLS 优化器函数容差 ftol（默认：1e-9） | `5e-9` |
| `--bell` | flag | ❌ | 执行 Bell 态保真度分析 | 无值（开关参数） |

#### 实现代码

```python
def _cmd_reconstruct(args: argparse.Namespace) -> int:
    """执行 'reconstruct' 子命令。
    
    流程：
        [1] 验证输入文件是否存在
        [2] 构建 ReconstructionConfig 对象
        [3] 调用 run_batch() 执行批处理
        [4] 输出结果路径信息
    """
    input_path: Path = args.input
    
    # [1] 验证输入
    if not input_path.exists():
        raise SystemExit(f"错误：输入文件不存在：{input_path}")
    
    # [2] 构建配置对象（CLI → 应用层的数据转换）
    config = ReconstructionConfig(
        input_path=input_path,
        output_dir=args.output_dir,
        methods=_resolve_methods(args.method),  # "both" → ("linear", "wls")
        dimension=args.dimension,
        sheet=_coerce_sheet(args.sheet),        # "0" → 0 (整数)
        linear_regularization=args.linear_regularization,
        wls_regularization=args.mle_regularization,
        wls_max_iterations=args.mle_max_iterations,
        wls_min_expected_clip=args.wls_min_expected_clip,
        wls_optimizer_ftol=args.wls_ftol,
        analyze_bell=args.bell,  # ← Bell 态分析开关
    )
    
    # [3] 调用应用层
    result = run_batch(config)
    
    # [4] 展示结果（用户友好的输出）
    print(f"✅ 汇总报告已保存至：{result.summary_path}")
    print(f"📁 详细记录目录：{result.records_dir}")
    print(f"🔬 执行的重构方法：{', '.join(result.methods)}")
    
    # Bell 态分析提示
    if args.bell:
        print("🔔 已完成 Bell 态保真度分析，指标已写入 summary.csv / records JSON。")
    
    return 0  # 成功退出
```

#### 使用示例

```bash
# 示例 1: 最简单用法（使用默认值）
qtomography reconstruct data.csv

# 示例 2: 指定重构方法
qtomography reconstruct data.csv --method wls

# 示例 3: 启用 Bell 态分析
qtomography reconstruct data.csv --method both --bell

# 示例 4: 完整参数（纠缠态重构）
qtomography reconstruct entangled_pairs.csv \
    --dimension 4 \
    --method wls \
    --bell \
    --output-dir bell_results/ \
    --mle-regularization 1e-5 \
    --mle-max-iterations 5000

# 示例 5: Excel 文件（指定工作表）
qtomography reconstruct data.xlsx --sheet Sheet2 --bell
```

---

### 2️⃣ summarize - 结果汇总 ⭐ **Stage 3 增强版**

#### 命令格式

```bash
qtomography summarize <汇总文件> [--metrics METRICS...] [--compare-methods] [--detailed] [--output OUTPUT]
```

#### 参数详解

| 参数 | 类型 | 必需 | 说明 | 示例 |
|-----|------|-----|------|-----|
| `summary` | Path | ✅ | 汇总 CSV 文件路径 | `results/summary.csv` |
| `--metrics` | list[str] | ❌ | 要聚合的指标（默认：purity trace） | `purity bell_max_fidelity` |
| `--compare-methods` | bool | ❌ | 生成 Linear vs MLE 对比报表（默认：关闭） | `--compare-methods` |
| `--detailed` | bool | ❌ | 显示详细统计（最小值、最大值、中位数、分位数）（默认：关闭） | `--detailed` |
| `--output` | Path | ❌ | 保存报告到文件（支持 .csv 或 .json） | `comparison.csv` |

#### 实现代码 ⭐ **Stage 3 增强版**

```python
def _cmd_summarize(args: argparse.Namespace) -> int:
    """执行 'summarize' 子命令。
    
    功能：
        读取 summary.csv，按重构方法分组计算指标的均值和标准差
        Stage 3 新增：
        - Linear vs MLE 方法对比（--compare-methods）
        - 详细统计信息（--detailed）
        - 报告导出功能（--output）
    """
    summary_path: Path = args.summary
    
    # 验证文件存在
    if not summary_path.exists():
        raise SystemExit(f"错误：汇总文件不存在：{summary_path}")
    
    # 读取 CSV
    df = pd.read_csv(summary_path)
    if df.empty:
        print("⚠️ 汇总文件为空")
        return 0
    
    # 过滤出存在的指标列
    metrics = [m for m in args.metrics if m in df.columns]
    if not metrics:
        raise SystemExit(f"错误：未找到指定的指标列。可用列：{df.columns.tolist()}")
    
    # ========== Stage 3: 分支逻辑 ==========
    if args.compare_methods:
        # 对比模式：Linear vs MLE
        _print_method_comparison(df, metrics, detailed=args.detailed)
    else:
        # 基础模式：按方法分组统计
        grouped = df.groupby("method")[metrics]
        means = grouped.mean().rename(columns=lambda c: f"mean_{c}")
        stds = grouped.std(ddof=0).rename(columns=lambda c: f"std_{c}")
        report = pd.concat([means, stds], axis=1)
        
        print("\n📊 重构结果统计汇总：")
        print(report)
    
    # ========== Stage 3: 保存报告 ==========
    if args.output:
        _save_summary_report(df, args.output, metrics, args.compare_methods)
        print(f"\n✅ 汇总报告已保存至: {args.output}")
    
    return 0
```

#### 使用示例

```bash
# 示例 1: 默认指标（purity、trace）
qtomography summarize results/summary.csv

# 示例 2: 包含 Bell 态指标
qtomography summarize results/summary.csv --metrics purity trace bell_max_fidelity

# 示例 3: 只分析 Bell 态保真度
qtomography summarize results/summary.csv --metrics bell_max_fidelity bell_avg_fidelity

# 输出示例：
# 📊 重构结果统计汇总：
#          mean_purity  std_purity  mean_bell_max_fidelity  std_bell_max_fidelity
# method
# linear      0.982145    0.015234                 0.945321               0.023456
# mle         0.995678    0.008123                 0.987654               0.012345
```

---

#### ⭐ Stage 3 新增功能示例

**示例 4：Linear vs MLE 方法对比**

```bash
qtomography summarize results/summary.csv \
    --compare-methods \
    --metrics purity trace fidelity eigenvalue_entropy

# 输出：
# ===== Linear vs MLE 对比报告 (配对样本: 10/10) =====
#
# 指标: purity
# ┌──────────┬────────────┬────────────┬────────────┐
# │ Method   │ Mean       │ Std        │ Median     │
# ├──────────┼────────────┼────────────┼────────────┤
# │ linear   │     0.9821 │     0.0152 │     0.9800 │
# │ mle      │     0.9957 │     0.0081 │     0.9950 │
# │ Δ (diff) │ +   0.0136 │ -   0.0071 │ +   0.0150 │
# └──────────┴────────────┴────────────┴────────────┘
#
# MLE 优化统计:
#   - 成功率: 100.0% (10/10)
#   - 平均迭代次数: 45.2 ± 12.3
#   - 平均评估次数: 156.8 ± 38.5
```

**功能特点**：
- 自动配对 Linear 和 MLE 样本（基于 `sample` 列）
- 显示每个指标的均值、标准差、中位数
- Δ 行显示 MLE 相对于 Linear 的差异
- 包含 MLE 优化统计（成功率、迭代次数、评估次数）

---

**示例 5：保存对比报告（CSV 格式）**

```bash
qtomography summarize results/summary.csv \
    --compare-methods \
    --metrics purity trace fidelity \
    --output comparison_report.csv
```

**生成的 CSV 文件**：包含按方法分组的详细统计信息（count, mean, std, min, 25%, 50%, 75%, max）

---

**示例 6：保存对比报告（JSON 格式）**

```bash
qtomography summarize results/summary.csv \
    --compare-methods \
    --metrics purity trace \
    --output comparison_report.json
```

**生成的 JSON 文件**：
```json
{
  "linear": {
    "purity": {
      "count": 10.0,
      "mean": 0.9821,
      "std": 0.0152,
      "min": 0.9500,
      ...
    }
  },
  "mle": { ... }
}
```

---

### 3️⃣ bell-analyze - Bell 态分析

#### 命令格式

```bash
qtomography bell-analyze <records_dir> [--output OUTPUT]
```

#### 参数详解

| 参数 | 类型 | 必需 | 说明 | 示例 |
|-----|------|-----|------|-----|
| `records_dir` | Path | ✅ | 存储重构记录的目录 | `results/records/` |
| `--output` | Path | ❌ | Bell 分析结果保存路径 | `bell_summary.csv` |

#### 功能说明

这个子命令用于**对已有的重构记录追加 Bell 态分析**，适用于以下场景：
- 之前运行 `reconstruct` 时没有使用 `--bell`
- 需要重新分析历史数据
- 批量处理多个实验的 JSON 记录

#### 实现代码

```python
def _cmd_bell_analyze(args: argparse.Namespace) -> int:
    """执行 'bell-analyze' 子命令：分析已有记录的 Bell 态保真度。
    
    参数:
        args: 解析后的命令行参数对象
    
    返回:
        退出状态码（0 = 成功）
    
    流程:
        1. 读取 records_dir 中的所有 JSON 文件
        2. 对每个记录的密度矩阵执行 Bell 态分析
        3. 生成汇总 CSV 文件
    """
    records_dir: Path = args.records_dir
    
    # 验证目录存在
    if not records_dir.exists():
        raise SystemExit(f"错误：记录目录不存在：{records_dir}")
    
    # 加载所有重构记录
    repo = ResultRepository(records_dir, fmt="json")
    records = list(repo.load_all())
    
    if not records:
        print("⚠️ 未找到任何重构记录")
        return 0
    
    # 批量分析
    df = analyze_records(records)  # 来自 bell.py
    
    # 保存结果
    output_path = args.output or (records_dir / "bell_summary.csv")
    df.to_csv(output_path, index=False)
    
    print(f"🔔 Bell 态分析结果已保存至：{output_path}")
    print(f"📊 分析了 {len(records)} 个重构记录")
    return 0
```

#### 使用示例

```bash
# 示例 1: 分析已有记录（默认输出到 records/bell_summary.csv）
qtomography bell-analyze results/records/

# 示例 2: 指定输出文件
qtomography bell-analyze results/records/ --output my_bell_analysis.csv

# 示例 3: 批量分析多个实验
for exp in exp1 exp2 exp3; do
    qtomography bell-analyze "results/${exp}/records/" \
        --output "analysis/${exp}_bell.csv"
done

# 输出示例：
# 🔔 Bell 态分析结果已保存至：results/records/bell_summary.csv
# 📊 分析了 100 个重构记录
```

---

### 4️⃣ info - 版本信息

#### 命令格式

```bash
qtomography info
```

#### 实现代码

```python
def _cmd_info(_: argparse.Namespace) -> int:
    """执行 'info' 子命令。
    
    功能：
        显示软件包版本和安装信息
    """
    try:
        # 从已安装的包中获取版本号
        pkg_version = version("qtomography")
    except PackageNotFoundError:
        # 开发模式（未安装）
        pkg_version = "未知版本（开发模式）"
    
    print(f"📦 qtomography 版本：{pkg_version}")
    print(f"📂 核心模块：qtomography.app.controller, qtomography.cli.main")
    print(f"📚 文档目录：docs/")
    return 0
```

#### 使用示例

```bash
qtomography info

# 输出：
# 📦 qtomography 版本：1.0.0
# 📂 核心模块：qtomography.app.controller, qtomography.cli.main
# 📚 文档目录：docs/
```

---

## 设计模式与最佳实践

### 🎭 设计模式 1: 命令模式（Command Pattern）

**核心思想**：每个子命令是一个独立的命令对象

```python
# 每个子命令有自己的处理函数
reconstruct.set_defaults(func=_cmd_reconstruct)  # 命令 1
summarize.set_defaults(func=_cmd_summarize)      # 命令 2
bell_analyze.set_defaults(func=_cmd_bell_analyze)# 命令 3
info.set_defaults(func=_cmd_info)                # 命令 4

# 统一的执行接口
def main(argv):
    args = parser.parse_args(argv)
    return args.func(args)  # 多态调用
```

**好处**：
- ✅ 每个命令独立实现，易于维护
- ✅ 新增命令无需修改 `main()` 函数
- ✅ 支持命令的动态注册

---

### 🎨 设计模式 2: 适配器模式（Adapter Pattern）

**核心思想**：CLI 参数格式 → 应用层配置格式

```python
# CLI 格式（字符串、简单类型）
args.method = "both"              # 字符串
args.sheet = "0"                  # 字符串（可能是数字）
args.input = "data.csv"           # 字符串路径
args.bell = True                  # 布尔值

# ↓ 适配器函数 ↓

# 应用层格式（类型化、结构化）
config = ReconstructionConfig(
    methods=_resolve_methods("both"),     # → ("linear", "mle")
    sheet=_coerce_sheet("0"),              # → 0 (整数)
    input_path=Path("data.csv"),           # → Path 对象
    analyze_bell=True,                     # → bool
)
```

**适配器函数**：

```python
def _resolve_methods(flag: str) -> tuple[str, ...]:
    """适配器：CLI 字符串 → 应用层元组"""
    if flag == "both":
        return ("linear", "mle")
    return (flag,)

def _coerce_sheet(value: str | None) -> str | int | None:
    """适配器：字符串 → 整数或字符串"""
    if isinstance(value, str) and value.isdigit():
        return int(value)  # "0" → 0
    return value           # "Sheet1" → "Sheet1"
```

---

### 📐 设计模式 3: 门面模式（Facade Pattern）

**核心思想**：CLI 为复杂的应用层提供简单接口

```python
# ❌ 没有 CLI 时：用户需要手动编写 Python 脚本
from qtomography.app.controller import ReconstructionConfig, run_batch
config = ReconstructionConfig(
    input_path=Path("data.csv"),
    output_dir=Path("results/"),
    methods=("linear", "mle"),
    dimension=4,
    analyze_bell=True,
    ...
)
result = run_batch(config)

# ✅ 有 CLI 时：一行命令完成
qtomography reconstruct data.csv --dimension 4 --bell
```

---

### 🔧 最佳实践

#### 实践 1: 输入验证在 CLI 层

```python
def _cmd_reconstruct(args):
    # ✅ CLI 层验证（早失败，早反馈）
    if not args.input.exists():
        raise SystemExit(f"错误：文件不存在：{args.input}")
    
    # 而不是等到应用层才发现错误
    config = ReconstructionConfig(...)
    result = run_batch(config)  # 如果文件不存在，这里才报错（太晚了）
```

---

#### 实践 2: 用户友好的输出

```python
# ✅ 好的输出（清晰、友好）
print(f"✅ 汇总报告已保存至：{result.summary_path}")
print(f"📁 详细记录目录：{result.records_dir}")
print(f"🔬 执行的重构方法：{', '.join(result.methods)}")
if args.bell:
    print("🔔 已完成 Bell 态保真度分析")

# ❌ 不好的输出（不友好）
print(result)  # <SummaryResult object at 0x...>
print(result.summary_path)  # results/summary.csv（没有上下文）
```

---

#### 实践 3: 默认值的合理设置

```python
reconstruct.add_argument(
    "--method",
    choices=["linear", "mle", "both"],
    default="both",  # ✅ 默认运行两种算法（对比效果）
    help="重构方法（默认：both）"
)

reconstruct.add_argument(
    "--output-dir",
    type=Path,
    default=Path("demo_output"),  # ✅ 默认目录，避免污染当前目录
    help="输出目录（默认：./demo_output）"
)

reconstruct.add_argument(
    "--bell",
    action="store_true",  # ✅ 布尔标志，默认 False
    help="执行 Bell 态保真度分析"
)
```

---

## 关键Python知识点

### 知识点 1: `action="store_true"` 的使用

```python
# Bell 态分析是一个布尔标志
reconstruct.add_argument(
    "--bell",
    action="store_true",  # 存在即为 True，不存在为 False
    help="执行 Bell 态保真度分析"
)

# 用户使用
$ qtomography reconstruct data.csv --bell
# args.bell = True

$ qtomography reconstruct data.csv
# args.bell = False

# 不需要写成 --bell True（这样反而会报错）
```

**对比其他 action**：

| action 值 | 说明 | 示例 |
|-----------|------|------|
| `"store"` | 存储值（默认） | `--method mle` |
| `"store_true"` | 标志为 True | `--bell` |
| `"store_false"` | 标志为 False | `--no-cache` |
| `"append"` | 追加到列表 | `--exclude a --exclude b` |

---

### 知识点 2: `nargs` 参数（多值参数）

```python
summarize.add_argument(
    "--metrics",
    nargs="*",  # 接受 0 个或多个值
    default=["purity", "trace"],
    help="要聚合的指标"
)

# 使用示例
$ qtomography summarize summary.csv --metrics purity bell_max_fidelity trace
# args.metrics = ["purity", "bell_max_fidelity", "trace"]

$ qtomography summarize summary.csv
# args.metrics = ["purity", "trace"]  # 使用默认值
```

---

### 知识点 3: `set_defaults(func=...)` 的妙用

```python
# 为每个子命令绑定处理函数
reconstruct.set_defaults(func=_cmd_reconstruct)
summarize.set_defaults(func=_cmd_summarize)
bell_analyze.set_defaults(func=_cmd_bell_analyze)
info.set_defaults(func=_cmd_info)

# 解析后，args.func 就是对应的函数
args = parser.parse_args(['reconstruct', 'data.csv'])
print(args.func)  # <function _cmd_reconstruct at 0x...>

# 统一调用接口（多态）
return args.func(args)  # 调用 _cmd_reconstruct(args)
```

---

### 知识点 4: `choices` 参数验证

```python
reconstruct.add_argument(
    "--method",
    choices=["linear", "mle", "both"],  # 限制可选值
    default="both",
    help="重构方法"
)

# 用户输入无效值时自动报错
$ qtomography reconstruct data.csv --method invalid
# error: argument --method: invalid choice: 'invalid' 
# (choose from 'linear', 'mle', 'both')
```

---

## 使用场景与示例

### 场景 1: 快速重构单个文件

```bash
# 最简单的用法
qtomography reconstruct measurements.csv

# 等价的 Python 代码
from qtomography.cli.main import main
main(['reconstruct', 'measurements.csv'])
```

---

### 场景 2: 纠缠态重构与 Bell 态分析

```bash
# 2-qubit 纠缠态实验
qtomography reconstruct bell_pair_data.csv \
    --dimension 4 \
    --method mle \
    --bell \
    --output-dir bell_results/

# 输出：
# ✅ 汇总报告已保存至：bell_results/summary.csv
# 📁 详细记录目录：bell_results/records
# 🔬 执行的重构方法：mle
# 🔔 已完成 Bell 态保真度分析，指标已写入 summary.csv / records JSON。

# 查看 Bell 态保真度
qtomography summarize bell_results/summary.csv \
    --metrics purity bell_max_fidelity bell_dominant_index
```

---

### 场景 3: 批量处理多个文件（Shell 脚本）

```bash
#!/bin/bash
# process_all.sh

for file in data/*.csv; do
    echo "处理文件：$file"
    qtomography reconstruct "$file" \
        --method both \
        --bell \
        --output-dir "results/$(basename $file .csv)/"
done

echo "全部完成！"
```

---

### 场景 4: 历史数据追加 Bell 态分析

```bash
# 场景：之前运行重构时没有使用 --bell，现在需要补充分析

# 方法 1：对单个实验补充分析
qtomography bell-analyze results/experiment1/records/ \
    --output results/experiment1/bell_summary.csv

# 方法 2：批量处理多个实验
for exp in exp1 exp2 exp3 exp4 exp5; do
    qtomography bell-analyze "results/${exp}/records/" \
        --output "bell_analysis/${exp}_bell.csv"
done

# 方法 3：合并所有实验的 Bell 分析
python << 'EOF'
import pandas as pd
from pathlib import Path

dfs = []
for csv in Path("bell_analysis").glob("*_bell.csv"):
    df = pd.read_csv(csv)
    df['experiment'] = csv.stem.replace('_bell', '')
    dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)
combined.to_csv("bell_analysis/all_experiments.csv", index=False)
print(f"✅ 合并了 {len(dfs)} 个实验的 Bell 态分析")
EOF
```

---

### 场景 5: 在 Python 脚本中调用 CLI

```python
from qtomography.cli.main import main

# 场景 1：处理多个参数组合
methods = ["linear", "mle"]
dimensions = [2, 4, 8]

for method in methods:
    for dim in dimensions:
        result = main([
            'reconstruct',
            'data.csv',
            '--method', method,
            '--dimension', str(dim),
            '--bell',  # 启用 Bell 态分析
            '--output-dir', f'results/{method}_d{dim}/'
        ])
        print(f"完成：{method}, dimension={dim}")

# 场景 2：自动化实验流程
import subprocess

# 使用 subprocess 调用命令行
subprocess.run([
    'qtomography', 'reconstruct', 'experiment_1.csv',
    '--method', 'mle',
    '--bell',
    '--mle-regularization', '1e-5'
])
```

---

## 🎯 总结

### CLI 的本质

```
┌─────────────────────────────────────────┐
│  CLI 是什么？                            │
│                                          │
│  1. 用户界面（命令行形式）              │
│  2. 参数解析器（argparse）              │
│  3. 输入验证器（检查文件存在性）        │
│  4. 类型转换器（字符串 → Path/int/bool）│
│  5. 应用层的调用者（调用 Controller）   │
│  6. 结果展示器（友好的输出格式）        │
│                                          │
│  它 **不** 实现业务逻辑！               │
└─────────────────────────────────────────┘
```

---

### 核心设计原则

| 原则 | 应用 |
|-----|------|
| **关注点分离** | CLI 只管用户交互，不管业务逻辑 |
| **单一职责** | 每个子命令一个处理函数 |
| **适配器模式** | CLI 格式 → 应用层格式的转换 |
| **命令模式** | 每个子命令是独立的命令对象 |
| **早失败原则** | 输入验证在 CLI 层完成 |
| **用户友好** | 清晰的帮助信息和错误提示 |

---

### 四大子命令总结

| 子命令 | 功能 | 关键参数 | Bell 态相关 | Stage 3 增强 |
|--------|------|----------|------------|-------------|
| `reconstruct` | 量子态重构 | `--method`, `--dimension` | `--bell` 开关 | ✅ 扩展 summary.csv 字段 |
| `summarize` | 结果汇总 | `--metrics`, `--compare-methods` ⭐, `--output` ⭐ | 可分析 `bell_max_fidelity` | ✅ 方法对比、报告导出 |
| `bell-analyze` | Bell 态分析 | `--output` | ✅ 专用于 Bell 分析 | ❌ 无变更 |
| `info` | 版本信息 | 无 | ❌ 无关 | ❌ 无变更 |

---

### 场景 6: 配置文件复用（⭐ 推荐）

配置文件功能允许你将常用的命令行参数保存为 JSON 文件，避免每次输入冗长的参数列表。特别适合：
- 重复性实验（相同参数处理多个数据文件）
- 团队协作（共享标准配置）
- 参数记录（实验可重现性）

#### 6.1 基础用法

```bash
# 步骤 1: 第一次运行时保存配置
qtomography reconstruct data/exp001.csv \
    --dimension 4 \
    --method both \
    --mle-max-iterations 2000 \
    --tolerance 1e-9 \
    --bell \
    --output-dir results/exp001 \
    --save-config my_config.json

# 步骤 2: 之后复用配置
qtomography reconstruct data/exp002.csv --config my_config.json

# 步骤 3: 配置 + 命令行覆盖
qtomography reconstruct data/exp003.csv \
    --config my_config.json \
    --dimension 2  # 仅覆盖维度，其他参数保持不变
```

#### 6.2 配置文件结构

生成的 `my_config.json` 内容：

```json
{
  "version": "1.0",
  "input_path": "data/exp001.csv",
  "output_dir": "results/exp001",
  "methods": ["linear", "mle"],
  "dimension": 4,
  "sheet": null,
  "linear_regularization": null,
  "mle_regularization": 1e-06,
  "mle_max_iterations": 2000,
  "tolerance": 1e-09,
  "cache_projectors": true,
  "analyze_bell": true
}
```

#### 6.3 完整字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `version` | string | ✅ | - | 配置文件版本号（当前 "1.0"） |
| `input_path` | string | ✅ | - | 输入文件路径（CSV/Excel） |
| `output_dir` | string | ✅ | - | 结果输出目录 |
| `methods` | array | ❌ | `["linear", "mle"]` | 重构方法列表 |
| `dimension` | int | ❌ | `null` | 量子态维度（`null` 时自动推断） |
| `sheet` | string/int | ❌ | `null` | Excel 工作表名称或索引 |
| `linear_regularization` | float | ❌ | `null` | 线性重构 Tikhonov 正则化系数 |
| `mle_regularization` | float | ❌ | `1e-6` | MLE 正则化系数 |
| `mle_max_iterations` | int | ❌ | `2000` | MLE 最大迭代次数 |
| `tolerance` | float | ❌ | `1e-9` | 数值容差 |
| `cache_projectors` | bool | ❌ | `true` | 是否缓存投影算符（批处理加速） |
| `analyze_bell` | bool | ❌ | `false` | 是否执行 Bell 态分析 |

**字段值优先级**: 命令行参数 > 配置文件 > 默认值

#### 6.4 高级用法

**相对路径解析**

配置文件中的路径会相对于**配置文件所在目录**解析，便于项目迁移：

```json
{
  "input_path": "../data/measurements.csv",  // 相对于配置文件位置
  "output_dir": "./results"                  // 相对于配置文件位置
}
```

**示例目录结构**:
```
project/
├── configs/
│   └── standard.json       # input_path = "../data/..."
├── data/
│   └── measurements.csv
└── results/
```

**命令行覆盖机制**

```bash
# 配置文件: dimension=4, method=both, bell=false
qtomography reconstruct --config config.json \
    --dimension 2 \      # 覆盖维度
    --method linear \    # 覆盖方法
    --bell               # 覆盖 Bell 分析（开启）

# 最终生效: dimension=2, method=linear, bell=true
```

**批量处理不同文件**

```bash
#!/bin/bash
# 使用同一配置处理多个文件

BASE_CONFIG="configs/standard_4d_mle.json"

for file in data/exp_*.csv; do
    exp_name=$(basename "$file" .csv)
    qtomography reconstruct "$file" \
        --config "$BASE_CONFIG" \
        --output-dir "results/$exp_name"
done
```

#### 6.5 配置文件模板

**模板 1: 快速重构**（linear only）
```json
{
  "version": "1.0",
  "input_path": "data/input.csv",
  "output_dir": "results",
  "methods": ["linear"],
  "dimension": 2,
  "tolerance": 1e-9
}
```

**模板 2: 高精度重构**（MLE + Bell）
```json
{
  "version": "1.0",
  "input_path": "data/input.csv",
  "output_dir": "results",
  "methods": ["mle"],
  "dimension": 4,
  "mle_regularization": 1e-8,
  "mle_max_iterations": 5000,
  "tolerance": 1e-12,
  "analyze_bell": true
}
```

**模板 3: 完整对比**（Linear + MLE + Bell）
```json
{
  "version": "1.0",
  "input_path": "data/input.csv",
  "output_dir": "results",
  "methods": ["linear", "mle"],
  "dimension": 4,
  "linear_regularization": 0.01,
  "mle_regularization": 1e-6,
  "mle_max_iterations": 2000,
  "tolerance": 1e-9,
  "cache_projectors": true,
  "analyze_bell": true
}
```

#### 6.6 实战示例：实验参数管理

```bash
# 场景：3 个实验系列，每个系列有不同的优化参数

# 1. 创建系列 A 配置（低噪声环境）
cat > configs/series_a.json << 'EOF'
{
  "version": "1.0",
  "input_path": "placeholder.csv",
  "output_dir": "results",
  "methods": ["linear", "mle"],
  "dimension": 4,
  "mle_max_iterations": 1000,
  "tolerance": 1e-9,
  "analyze_bell": true
}
EOF

# 2. 创建系列 B 配置（高噪声环境，需要正则化）
cat > configs/series_b.json << 'EOF'
{
  "version": "1.0",
  "input_path": "placeholder.csv",
  "output_dir": "results",
  "methods": ["linear", "mle"],
  "dimension": 4,
  "linear_regularization": 0.05,
  "mle_regularization": 1e-5,
  "mle_max_iterations": 3000,
  "tolerance": 1e-8,
  "analyze_bell": true
}
EOF

# 3. 批量处理
for file in data/series_a_*.csv; do
    qtomography reconstruct "$file" --config configs/series_a.json
done

for file in data/series_b_*.csv; do
    qtomography reconstruct "$file" --config configs/series_b.json
done
```

#### 6.7 配置文件的优势总结

| 优势 | 说明 | 场景 |
|------|------|------|
| **减少输入** | 避免重复输入长参数列表 | 重复性实验 |
| **参数记录** | 配置文件即实验参数档案 | 论文可重现性 |
| **团队协作** | 共享标准配置文件 | 多人协作项目 |
| **版本控制** | 配置文件可纳入 Git | 参数演进追踪 |
| **批量处理** | 一个配置处理多个文件 | 大规模数据分析 |
| **易于调试** | 快速切换参数组合 | 参数优化实验 |

---

### 关键技术点

```
1. argparse              → 命令行参数解析
2. subparsers            → 子命令架构
3. set_defaults(func=..) → 命令绑定
4. action="store_true"   → 布尔标志参数
5. choices               → 参数验证
6. type=Path/int         → 自动类型转换
7. nargs="*"             → 多值参数
8. SystemExit            → 退出码管理
9. 适配器函数            → CLI → 应用层转换
10. 友好输出             → 用户体验
11. Bell 态集成          → --bell 参数和 bell-analyze 子命令
12. JSON 配置管理        → 配置文件加载与合并（场景 6）
```

---

### Bell 态分析的两种方式

| 方式 | 命令 | 适用场景 |
|-----|------|----------|
| **方式 1** | `reconstruct --bell` | 新实验，重构时直接分析 |
| **方式 2** | `bell-analyze` | 历史数据，后期追加分析 |

---

### 分层架构的好处

```
CLI (main.py)
    ↓ 只负责用户交互
Controller (controller.py)
    ↓ 只负责流程编排
Reconstructor (mle.py/linear.py)
    ↓ 只负责算法实现
BellAnalysis (bell.py)
    ↓ 只负责量子态分析

好处：
✅ 职责清晰
✅ 易于测试
✅ 易于扩展（添加 GUI 无需修改业务逻辑）
✅ 易于维护（修改 CLI 参数不影响算法）
```

---

**文档版本**: v1.2 (新增配置文件复用章节)  
**最后更新**: 2025年10月7日  
**作者**: AI Assistant  
**难度等级**: 初级到中级

---

## 📝 更新日志

### v1.2 (2025-10-07)
- ✅ 新增场景 6：配置文件复用（⭐ 重要）
- ✅ 配置文件完整字段说明表（12 个字段）
- ✅ 配置文件模板（快速重构/高精度重构/完整对比）
- ✅ 高级用法：相对路径、命令行覆盖、批量处理
- ✅ 实战示例：实验参数管理
- ✅ 新增知识点：JSON 配置管理

### v1.1 (2025-10-07)
- ✅ 新增 `bell-analyze` 子命令详解
- ✅ 新增 `--bell` 参数说明
- ✅ 更新分层架构图（包含 BellAnalysis）
- ✅ 新增场景 2：纠缠态重构与 Bell 态分析
- ✅ 新增场景 4：历史数据追加 Bell 态分析
- ✅ 新增知识点：`action="store_true"` 的使用
- ✅ 更新四大子命令总结表

### v1.0 (2025-10-07)
- 初始版本：CLI 基础架构和三大子命令

---

## ✅ 学习检查清单

学完本文档后，你应该能够：

- [ ] 理解 CLI 在四层架构中的位置
- [ ] 使用 argparse 创建命令行工具
- [ ] 实现子命令架构（subparsers）
- [ ] 编写参数验证和类型转换函数
- [ ] 理解命令模式和适配器模式在 CLI 中的应用
- [ ] 设计用户友好的命令行界面
- [ ] 在 Python 脚本中调用 CLI 函数
- [ ] 区分 CLI 层和应用层的职责
- [ ] 使用 `--bell` 参数进行 Bell 态分析
- [ ] 使用 `bell-analyze` 子命令追加分析历史数据
- [ ] 使用 `--config` 和 `--save-config` 管理配置文件 ⭐ 新增
- [ ] 理解配置文件的字段优先级和覆盖机制 ⭐ 新增
- [ ] 编写可复用的配置文件模板 ⭐ 新增

如果以上都能做到，恭喜你已经掌握了 CLI 设计的精髓！🎉
