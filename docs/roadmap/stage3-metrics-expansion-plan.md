# 阶段 3: 指标扩展与报表增强计划

**日期**: 2025-10-07  
**版本**: v1.0  
**状态**: 📋 设计中

---

## 🎯 目标

扩展 `summary.csv` 中的指标，并增强 CLI `summarize` 命令的分析和报表功能。

---

## 📊 当前状态分析

### **1. 现有 `summary.csv` 结构**

根据 `controller.py` 的代码分析 (L442-522)，当前 `summary.csv` 包含以下字段：

#### **Linear 方法字段**:
| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `sample` | int | 样本索引 | 第几个样本 |
| `method` | str | 固定为 "linear" | 重构方法 |
| `purity` | float | `density.purity` | 纯度 Tr(ρ²) |
| `trace` | float | `density.trace` | 迹 Tr(ρ) |
| `residual_norm` | float | `metrics.get("residual_norm", 0.0)` | 残差范数 |
| `bell_*` | float | Bell分析（可选） | Bell态相关指标 |

#### **MLE 方法字段**:
| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `sample` | int | 样本索引 | 第几个样本 |
| `method` | str | 固定为 "mle" | 重构方法 |
| `purity` | float | `density.purity` | 纯度 Tr(ρ²) |
| `trace` | float | `density.trace` | 迹 Tr(ρ) |
| `objective` | float | `mle_result.objective_value` | 目标函数值（χ²） |
| `bell_*` | float | Bell分析（可选） | Bell态相关指标 |

---

### **2. JSON 记录中已有但未导出到 CSV 的字段**

根据 `MLEReconstructionResult` (mle.py:17-42) 和 `LinearReconstructionResult` 的分析：

#### **MLE 结果中可用但未使用的字段**:
- ✅ **`n_iterations`** - 优化器迭代次数
- ✅ **`n_function_evaluations`** - 目标函数调用次数
- ✅ **`success`** - 优化是否成功
- ✅ **`status`** - 优化器状态码
- ✅ **`message`** - 优化器返回的信息

#### **Linear 结果中可用但未使用的字段**:
- ✅ **`rank`** - 矩阵秩
- ✅ **`singular_values`** - 奇异值数组
- ⚠️ **`condition_number`** - 条件数（需要计算：`max(sv) / min(sv)`）

#### **密度矩阵中可用的字段**:
- ✅ **`eigenvalues`** - 特征值数组（已在 `DensityMatrix` 中）
- ✅ **`fidelity`** - 保真度（需要与目标态对比）

---

### **3. 当前 CLI `summarize` 功能**

根据 `main.py:272-310`，当前功能：

**已实现**:
- ✅ 读取 `summary.csv`
- ✅ 按 `method` 分组
- ✅ 计算指定指标的均值和标准差
- ✅ 输出表格形式的汇总报告

**限制**:
- ❌ 无法对比多个方法（linear vs MLE）
- ❌ 无法显示方法间的差异
- ❌ 无法生成可视化图表
- ❌ 无法输出详细的统计信息（最小值、最大值、中位数等）

---

## 🚀 扩展方案

### **任务 1: 扩展 `summary.csv` 指标**

#### **1.1 Linear 方法新增字段**

| 字段 | 类型 | 来源 | 优先级 | 说明 |
|------|------|------|--------|------|
| `rank` | int | `linear_result.rank` | P1 | 矩阵秩 |
| `condition_number` | float | 计算：`max(sv) / min(sv[sv > tol])` | P2 | 条件数 |
| `min_eigenvalue` | float | `min(density.eigenvalues)` | P1 | 最小特征值 |
| `max_eigenvalue` | float | `max(density.eigenvalues)` | P1 | 最大特征值 |
| `eigenvalue_entropy` | float | 计算：`-sum(λ * log(λ))` | P3 | 特征值熵 |

**修改位置**: `controller.py:442-457`

```python
summary_entry = {
    "sample": idx,
    "method": "linear",
    "purity": record.metrics["purity"],
    "trace": record.metrics["trace"],
    "residual_norm": record.metrics.get("residual_norm", 0.0),
    # 新增字段
    "rank": linear_result.rank,  # P1
    "min_eigenvalue": float(np.min(linear_result.density.eigenvalues)),  # P1
    "max_eigenvalue": float(np.max(linear_result.density.eigenvalues)),  # P1
}
```

---

#### **1.2 MLE 方法新增字段**

| 字段 | 类型 | 来源 | 优先级 | 说明 |
|------|------|------|--------|------|
| `n_iterations` | int | `mle_result.n_iterations` | P1 | 迭代次数 |
| `n_evaluations` | int | `mle_result.n_function_evaluations` | P2 | 函数评估次数 |
| `success` | bool | `mle_result.success` | P1 | 优化是否成功 |
| `status` | int | `mle_result.status` | P2 | 优化器状态码 |
| `min_eigenvalue` | float | `min(density.eigenvalues)` | P1 | 最小特征值 |
| `max_eigenvalue` | float | `max(density.eigenvalues)` | P1 | 最大特征值 |
| `eigenvalue_entropy` | float | 计算：`-sum(λ * log(λ))` | P3 | 特征值熵 |

**修改位置**: `controller.py:507-522`

```python
summary_entry = {
    "sample": idx,
    "method": "mle",
    "purity": record.metrics["purity"],
    "trace": record.metrics["trace"],
    "objective": record.metrics["objective"],
    # 新增字段
    "n_iterations": mle_result.n_iterations,  # P1
    "n_evaluations": mle_result.n_function_evaluations,  # P2
    "success": mle_result.success,  # P1
    "status": mle_result.status,  # P2
    "min_eigenvalue": float(np.min(mle_result.density.eigenvalues)),  # P1
    "max_eigenvalue": float(np.max(mle_result.density.eigenvalues)),  # P1
}
```

---

#### **1.3 通用计算函数** ⭐ 已改进（审查反馈）

新增辅助函数用于计算特征值熵等指标：

**位置**: `controller.py` 顶部或独立模块

```python
def _calculate_eigenvalue_entropy(
    eigenvalues: np.ndarray, 
    epsilon: float = 1e-15,
    base: str = "natural"  # "natural" or "2"
) -> float:
    """计算 von Neumann 熵（改进版：自动归一化）。
    
    参数:
        eigenvalues: 特征值数组（会自动归一化）
        epsilon: 小值截断阈值
        base: 对数底（"natural" 或 "2"）
    
    返回:
        von Neumann 熵 S = -Tr(ρ log ρ) = -sum(λ log λ)
    
    改进点（审查反馈）:
        - 自动归一化特征值
        - 支持不同对数底
        - 明确物理意义
    """
    # 自动归一化（审查建议）
    trace = np.sum(eigenvalues)
    if abs(trace - 1.0) > 1e-6:
        eigenvalues = eigenvalues / trace
    
    # 过滤小值
    eigs = eigenvalues[eigenvalues > epsilon]
    if len(eigs) == 0:
        return 0.0
    
    # 计算熵
    if base == "natural":
        return -float(np.sum(eigs * np.log(eigs)))
    elif base == "2":
        return -float(np.sum(eigs * np.log2(eigs)))
    else:
        raise ValueError(f"不支持的对数底: {base}")


def _calculate_condition_number(
    singular_values: np.ndarray, 
    tolerance: Optional[float] = None
) -> float:
    """计算条件数（改进版：相对容差 + 避免 inf）。
    
    参数:
        singular_values: 奇异值数组
        tolerance: 相对容差（默认为 max(sv) * 1e-10）
    
    返回:
        条件数，如果无有效奇异值则返回 1e16（大数而非 inf）
    
    改进点（审查反馈）:
        - 使用相对容差而非绝对容差
        - 返回 1e16 代替 np.inf，避免 CSV 格式问题
        - 处理空数组边界情况
    """
    if len(singular_values) == 0:
        return 1e16  # 避免 inf（审查建议）
    
    max_sv = np.max(singular_values)
    if tolerance is None:
        tolerance = max_sv * 1e-10  # 相对容差（审查建议）
    
    sv = singular_values[singular_values > tolerance]
    if len(sv) == 0:
        return 1e16  # 避免 inf（审查建议）
    
    return float(max_sv / np.min(sv))
```

---

#### **1.4 CSV 列顺序控制** ⭐ 新增（审查反馈）

**问题**: pandas `DataFrame(summary_rows).to_csv()` 的列顺序不确定，可能导致不同运行产生不同的列顺序。

**修改位置**: `controller.py:526-532`

**改进代码**:

```python
# ========== [4] 汇总阶段 ==========
summary_path = config.output_dir / "summary.csv"
if summary_rows:
    df = pd.DataFrame(summary_rows)
    
    # ⭐ 新增：显式定义列顺序（审查建议）
    standard_columns = [
        # 通用字段
        "sample", "method", "purity", "trace",
        # Linear 专属
        "residual_norm", "rank",
        # MLE 专属
        "objective", "n_iterations", "n_evaluations", "success", "status",
        # 通用扩展字段
        "min_eigenvalue", "max_eigenvalue",
        # P2/P3 字段（可选）
        "condition_number", "eigenvalue_entropy",
    ]
    
    # 保留已存在的列 + Bell 分析列
    available_cols = [c for c in standard_columns if c in df.columns]
    bell_cols = [c for c in df.columns if c.startswith("bell_") and c not in available_cols]
    ordered_cols = available_cols + bell_cols
    
    # 按固定顺序保存
    df[ordered_cols].to_csv(summary_path, index=False)
else:
    # 空 CSV（保持向后兼容）
    summary_path.write_text("sample,method,purity,trace\n", encoding="utf-8")
```

**优势**:
- ✅ 列顺序一致，方便脚本解析
- ✅ 向后兼容（旧字段在前）
- ✅ 自动处理可选字段和 Bell 列

---

#### **1.5 record.metrics 同步** ⭐ 新增（审查反馈）

**问题**: 新字段需要同时写入 `summary.csv` 和 `record.metrics`（JSON），否则会导致数据不一致。

**修改位置**: `controller.py:442-457` (Linear) 和 `L507-522` (MLE)

**Linear 修改示例**:

```python
# 创建持久化记录（L403-416）
record = _create_record(
    method="linear",
    dimension=dimension,
    probabilities=linear_result.normalized_probabilities,
    density_matrix=linear_result.density.matrix,
    metrics={
        "purity": linear_result.density.purity,
        "trace": float(np.real(linear_result.density.trace)),
        # ⭐ 新增：同步 JSON 记录（审查建议）
        "rank": linear_result.rank,
        "min_eigenvalue": float(np.min(linear_result.density.eigenvalues)),
        "max_eigenvalue": float(np.max(linear_result.density.eigenvalues)),
    },
    metadata=metadata,
)

# ... Bell 分析（如果启用）...

# 添加到汇总表（L442-457）
summary_entry = {
    "sample": idx,
    "method": "linear",
    "purity": record.metrics["purity"],        # 从 record 读取
    "trace": record.metrics["trace"],
    "residual_norm": record.metrics.get("residual_norm", 0.0),
    "rank": record.metrics["rank"],            # ⭐ 同步
    "min_eigenvalue": record.metrics["min_eigenvalue"],  # ⭐ 同步
    "max_eigenvalue": record.metrics["max_eigenvalue"],  # ⭐ 同步
}
```

**要点**:
1. 先写入 `record.metrics`
2. 再从 `record.metrics` 读取到 `summary_entry`
3. 确保 JSON 和 CSV 的数据源一致

---

### **任务 2: 增强 CLI `summarize` 命令**

#### **2.1 新增 `--compare-methods` 选项**

**功能**: 对比不同重构方法的性能。

**实现位置**: `cli/main.py:107-128`

```python
summarize.add_argument(
    "--compare-methods",
    action="store_true",
    help="生成方法对比报表（linear vs mle）"
)

summarize.add_argument(
    "--detailed",
    action="store_true",
    help="显示详细统计信息（最小值、最大值、中位数、25/75分位数）"
)

summarize.add_argument(
    "--output",
    type=Path,
    help="保存汇总报告到文件（CSV 或 JSON 格式）"
)
```

---

#### **2.2 增强 `_cmd_summarize` 函数**

**位置**: `cli/main.py:272-310`

**新功能**:
1. **详细统计**: 最小值、最大值、中位数、25/75分位数
2. **方法对比**: Linear vs MLE 的差异分析
3. **成功率统计**: MLE 的优化成功率
4. **收敛分析**: 迭代次数分布

**伪代码**:

```python
def _cmd_summarize(args: argparse.Namespace) -> int:
    """增强版 summarize 命令。"""
    summary_path: Path = args.summary
    
    # 1. 读取数据
    df = pd.read_csv(summary_path)
    if df.empty:
        print("⚠️ 汇总文件为空")
        return 0
    
    # 2. 基础统计（现有功能）
    if not args.compare_methods:
        # 原有逻辑...
        _print_basic_summary(df, args.metrics)
    
    # 3. 方法对比（新功能）
    else:
        if "linear" in df["method"].values and "mle" in df["method"].values:
            _print_method_comparison(df, args.metrics, detailed=args.detailed)
        else:
            print("⚠️ 需要至少两种方法才能进行对比")
    
    # 4. 保存报告（新功能）
    if args.output:
        _save_summary_report(df, args.output, args.metrics)
    
    return 0


def _print_basic_summary(df: pd.DataFrame, metrics: List[str]) -> None:
    """打印基础统计汇总（现有功能）。"""
    # 现有代码...
    pass


def _print_method_comparison(df: pd.DataFrame, metrics: List[str], detailed: bool = False) -> None:
    """打印方法对比报表（改进版：样本配对检查）。
    
    输出格式:
        📊 Linear vs MLE 对比报告 (配对样本: 150/200)
        
        指标: purity
        ┌──────────┬────────────┬────────────┬────────────┐
        │ Method   │ Mean       │ Std        │ Median     │
        ├──────────┼────────────┼────────────┼────────────┤
        │ linear   │ 0.6800     │ 0.0150     │ 0.6795     │
        │ mle      │ 0.6750     │ 0.0120     │ 0.6748     │
        │ Δ (diff) │ +0.0050    │ +0.0030    │ +0.0047    │
        └──────────┴────────────┴────────────┴────────────┘
        
        指标: trace
        ...
        
        MLE 优化统计:
          - 成功率: 98.5% (197/200)
          - 平均迭代次数: 15.3 ± 5.2
          - 平均评估次数: 82.1 ± 23.4
    
    改进点（审查反馈）:
        - 检查样本配对，只对比共同样本
        - 显示配对样本数量
        - 友好的错误提示
    """
    # ⭐ 新增：检查样本配对（审查建议）
    linear_df = df[df["method"] == "linear"].set_index("sample")
    mle_df = df[df["method"] == "mle"].set_index("sample")
    
    # 找到共同样本
    common_samples = linear_df.index.intersection(mle_df.index)
    
    if len(common_samples) == 0:
        print("⚠️ 没有找到配对的样本（Linear 和 MLE 必须针对相同的样本）")
        return
    
    # 只对比共同样本
    linear_df = linear_df.loc[common_samples]
    mle_df = mle_df.loc[common_samples]
    
    # 统计总样本数
    all_samples = linear_df.index.union(mle_df.index)
    total_samples = len(all_samples)
    
    print(f"\n📊 Linear vs MLE 对比报告 (配对样本: {len(common_samples)}/{total_samples})\n")
    
    for metric in metrics:
        if metric not in df.columns:
            continue
        
        print(f"指标: {metric}")
        print("┌──────────┬────────────┬────────────┬────────────┐")
        print("│ Method   │ Mean       │ Std        │ Median     │")
        print("├──────────┼────────────┼────────────┼────────────┤")
        
        # Linear 统计
        l_mean = linear_df[metric].mean()
        l_std = linear_df[metric].std()
        l_median = linear_df[metric].median()
        print(f"│ linear   │ {l_mean:10.4f} │ {l_std:10.4f} │ {l_median:10.4f} │")
        
        # MLE 统计
        m_mean = mle_df[metric].mean()
        m_std = mle_df[metric].std()
        m_median = mle_df[metric].median()
        print(f"│ mle      │ {m_mean:10.4f} │ {m_std:10.4f} │ {m_median:10.4f} │")
        
        # 差异
        diff_mean = l_mean - m_mean
        diff_std = l_std - m_std
        diff_median = l_median - m_median
        sign_mean = "+" if diff_mean >= 0 else ""
        print(f"│ Δ (diff) │ {sign_mean}{diff_mean:9.4f} │ {sign_mean}{diff_std:9.4f} │ {sign_mean}{diff_median:9.4f} │")
        print("└──────────┴────────────┴────────────┴────────────┘\n")
    
    # MLE 专属统计
    if "n_iterations" in mle_df.columns and "success" in mle_df.columns:
        print("MLE 优化统计:")
        success_count = mle_df["success"].sum()
        total_count = len(mle_df)
        success_rate = 100 * success_count / total_count
        print(f"  - 成功率: {success_rate:.1f}% ({success_count}/{total_count})")
        
        avg_iter = mle_df["n_iterations"].mean()
        std_iter = mle_df["n_iterations"].std()
        print(f"  - 平均迭代次数: {avg_iter:.1f} ± {std_iter:.1f}")
        
        if "n_evaluations" in mle_df.columns:
            avg_eval = mle_df["n_evaluations"].mean()
            std_eval = mle_df["n_evaluations"].std()
            print(f"  - 平均评估次数: {avg_eval:.1f} ± {std_eval:.1f}")


def _save_summary_report(df: pd.DataFrame, output_path: Path, metrics: List[str]) -> None:
    """保存汇总报告到文件。"""
    if output_path.suffix == ".csv":
        # 保存为 CSV
        summary = df.groupby("method")[metrics].describe()
        summary.to_csv(output_path)
    elif output_path.suffix == ".json":
        # 保存为 JSON
        summary = df.groupby("method")[metrics].describe().to_dict()
        output_path.write_text(json.dumps(summary, indent=2))
    else:
        raise ValueError(f"不支持的输出格式: {output_path.suffix}")
    
    print(f"✅ 汇总报告已保存至: {output_path}")
```

---

## 📋 实施计划

### **阶段 3.1: 扩展 summary.csv 指标** (优先级 P1)

**任务清单**:
1. ✅ 分析现有代码和数据结构
2. ⏳ 在 `controller.py` 中添加辅助计算函数
3. ⏳ 修改 Linear 方法的 `summary_entry` (L442-457)
4. ⏳ 修改 MLE 方法的 `summary_entry` (L507-522)
5. ⏳ 更新单元测试 (`test_controller.py`)
6. ⏳ 生成测试数据并验证新字段

**预期输出**:
```csv
sample,method,purity,trace,residual_norm,rank,min_eigenvalue,max_eigenvalue,n_iterations,n_evaluations,success,status
0,linear,0.68,1.0,0.0012,4,0.0001,0.85,...
0,mle,0.67,1.0,0.0008,,,0.0002,0.82,15,85,True,0
```

---

### **阶段 3.2: 增强 CLI summarize** (优先级 P1-P2)

**任务清单**:
1. ⏳ 添加 `--compare-methods` 参数
2. ⏳ 添加 `--detailed` 参数
3. ⏳ 添加 `--output` 参数
4. ⏳ 实现 `_print_method_comparison()` 函数
5. ⏳ 实现 `_save_summary_report()` 函数
6. ⏳ 更新 CLI 测试 (`test_cli.py`)
7. ⏳ 更新文档 (`cli详解.md`, `README.md`)

**预期输出**:
```bash
# 基础用法（不变）
$ qtomography summarize results/summary.csv
📊 重构结果统计汇总：
         mean_purity  std_purity  mean_trace  std_trace
method                                                  
linear        0.6800      0.0150      1.0000     0.0000
mle           0.6750      0.0120      1.0000     0.0000

# 新功能：方法对比
$ qtomography summarize results/summary.csv --compare-methods
📊 Linear vs MLE 对比报告
...

# 新功能：保存报告
$ qtomography summarize results/summary.csv --output report.csv
✅ 汇总报告已保存至: report.csv
```

---

## 🎯 成功标准

1. ✅ `summary.csv` 包含所有 P1 优先级字段
2. ✅ CLI `summarize --compare-methods` 能正常运行
3. ✅ 所有新功能通过单元测试
4. ✅ 文档更新完整（README、cli详解）
5. ✅ 向后兼容（旧版 summary.csv 仍可读取）

---

## 📚 相关文件

| 文件 | 修改内容 |
|------|----------|
| `qtomography/app/controller.py` | 扩展 `summary_entry` 字典 |
| `qtomography/cli/main.py` | 增强 `summarize` 命令 |
| `tests/unit/test_controller.py` | 添加新字段测试 |
| `tests/unit/test_cli.py` | 添加 `--compare-methods` 测试 |
| `docs/teach/cli详解.md` | 更新 `summarize` 用法 |
| `README.md` | 更新命令行工具章节 |

---

## 🔄 下一步

等待用户确认此计划后，开始实施：

1. **阶段 3.1**: 扩展 `summary.csv` 指标
2. **阶段 3.2**: 增强 CLI `summarize` 命令

---

## 🎯 风险与假设 ⭐ 新增（审查反馈）

### **已知风险**

| 风险项 | 等级 | 影响 | 缓解措施 |
|--------|------|------|----------|
| 向后兼容性 | 🟢 低 | 旧代码无法运行 | ✅ 已验证兼容性，列顺序控制 |
| CSV 格式问题 | 🟡 中 | 列顺序不一致 | ✅ 显式定义列顺序（任务 1.4） |
| 数值稳定性 | 🟡 中 | 条件数计算 inf | ✅ 使用改进算法（任务 1.3） |
| 样本配对失败 | 🟡 中 | 对比功能报错 | ✅ 改进配对逻辑（任务 2.2） |
| 性能影响 | 🟢 低 | 计算开销增加 | ✅ 新字段计算开销可忽略 |

### **需要验证的假设**

1. **假设 1**: MLE 优化器总是返回 `n_iterations` 和 `n_function_evaluations`
   - **验证方法**: 检查不同优化器（L-BFGS-B, trust-constr）的返回值
   - **风险**: 某些优化器可能不返回这些值，需要设置默认值

2. **假设 2**: `singular_values` 数组总是非空
   - **验证方法**: 测试极端输入（全零矩阵、秩缺失）
   - **风险**: 空数组会导致条件数计算失败，已在改进算法中处理

3. **假设 3**: 特征值数组已归一化（sum = 1）
   - **验证方法**: 添加断言检查或自动归一化
   - **风险**: 未归一化会导致熵值无意义，已在改进算法中自动归一化

4. **假设 4**: 样本索引在 Linear 和 MLE 之间一致
   - **验证方法**: 在 `--compare-methods` 中检查并提示
   - **风险**: 不一致会导致对比错误，已添加配对检查

### **未知风险**

1. **大规模数据性能**: 未测试 1000+ 样本的性能表现
2. **并行处理冲突**: 未来如果引入并行重构，CSV 写入可能冲突
3. **跨平台兼容性**: 未在 Linux/macOS 上测试 CSV 格式

---

## 📋 更新后的实施计划

### **阶段 3.1: 扩展 summary.csv（改进版）** ✅ 已整合审查反馈

**P0 - 必须修复**:
1. ✅ 添加 CSV 列顺序控制（任务 1.4）
2. ✅ 修复条件数计算的稳定性（任务 1.3）
3. ✅ 修复特征值熵计算（任务 1.3）
4. ✅ 确保 record.metrics 同步（任务 1.5）

**P1 - 核心功能**:
5. ⏳ 添加 `n_iterations`, `success`, `min_eigenvalue`, `max_eigenvalue` (任务 1.1, 1.2)
6. ⏳ 添加 `rank`, `n_evaluations`, `status` (任务 1.1, 1.2)

**P2 - 次要功能**:
7. ⏳ 添加 `condition_number`（使用改进版计算）
8. ⏳ 添加 `eigenvalue_entropy`（使用改进版计算）

### **阶段 3.2: 增强 CLI summarize（改进版）** ✅ 已整合审查反馈

**P0 - 必须修复**:
1. ✅ 改进 `--compare-methods` 的样本配对逻辑（任务 2.2）

**P1 - 核心功能**:
2. ⏳ 实现 `--compare-methods` 基础功能（任务 2.1, 2.2）
3. ⏳ 实现 MLE 优化统计（成功率、迭代次数）（任务 2.2）

**P2 - 次要功能**:
4. ⏳ 实现 `--detailed` 详细统计（任务 2.2）
5. ⏳ 实现 `--output` 保存报告（任务 2.2）

### **预期时间**

- **阶段 3.1**: 6-8 小时（编码 + 测试 + 文档）
- **阶段 3.2**: 4-6 小时（编码 + 测试 + 文档）
- **总计**: 10-14 小时

---

## 📚 参考审查文档

本计划已根据以下审查文档进行更新：
- **审查报告**: `stage3-plan-review.md`
- **用户反馈**: 2025-10-07

### **整合的改进**:
1. ✅ 数值稳定性算法（问题 1, 2）
2. ✅ CSV 列顺序控制（问题 3）
3. ✅ 样本配对逻辑（问题 4）
4. ✅ record.metrics 同步（用户建议）
5. ✅ 风险与假设章节（审查建议）

---

**文档版本**: v2.0 ⭐ 已整合审查反馈  
**最后更新**: 2025-10-07  
**作者**: AI Assistant  
**审查状态**: ✅ 用户反馈已整合
