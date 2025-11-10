# CLI 命令行使用指南

> **快速参考**：qtomography 命令行工具的完整使用说明

---

## 📦 安装与环境配置

### 1. 安装依赖

```bash
cd QT_to_Python_1/python
pip install -r requirements.txt
```

### 2. 安装软件包（开发模式）

```bash
pip install -e .
```

安装后即可在任何目录使用 `qtomography` 命令。

---

## 🚀 快速开始

### 最简单的用法

```bash
# 对测量数据执行量子态重构（默认同时执行 Linear 和 MLE）
qtomography reconstruct data.csv
```

### 查看帮助

```bash
# 查看所有可用命令
qtomography --help

# 查看 reconstruct 命令的详细参数
qtomography reconstruct --help

# 查看 summarize 命令的详细参数
qtomography summarize --help
```

---

## 📋 命令详解

### 1️⃣ `reconstruct` - 量子态重构

**功能**：从测量概率数据重构量子态密度矩阵

#### 基本语法

```bash
qtomography reconstruct <输入文件> [选项]
```

#### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `input` | 输入文件路径（CSV 或 Excel） | `data.csv` 或 `data.xlsx` |

#### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--method` | 选择 | `both` | 重构方法：`linear`（线性）、`mle`（最大似然）、`both`（两者） |
| `--dimension` | 整数 | 自动推断 | 希尔伯特空间维度 $n$（数据应有 $n^2$ 行） |
| `--output-dir` | 路径 | `demo_output` | 结果输出目录 |
| `--sheet` | 字符串/整数 | 无 | Excel 工作表名称或索引（如 `Sheet1` 或 `0`） |
| `--linear-regularization` | 浮点数 | 无 | 线性重构的岭回归系数（推荐：`1e-6` ~ `1e-3`） |
| `--mle-regularization` | 浮点数 | 无 | MLE 的 L2 正则化系数（推荐：`1e-6` ~ `1e-4`） |
| `--mle-max-iterations` | 整数 | `2000` | MLE 优化器最大迭代次数 |

---

#### 使用示例

**示例 1：基本用法**（CSV 输入，默认两种方法）

```bash
qtomography reconstruct measurements.csv
```

**输出**：
```
✅ 汇总报告已保存至：demo_output/summary.csv
📁 详细记录目录：demo_output/records
🔬 执行的重构方法：linear, mle
```

---

**示例 2：仅执行线性重构**

```bash
qtomography reconstruct measurements.csv --method linear
```

---

**示例 3：指定维度和输出目录**

```bash
qtomography reconstruct data.csv --dimension 4 --output-dir results
```

**说明**：
- 强制设置维度为 4（数据应有 16 行）
- 结果保存到 `results/` 目录

---

**示例 4：Excel 输入，指定工作表**

```bash
# 使用工作表名称
qtomography reconstruct data.xlsx --sheet Sheet1

# 使用工作表索引（0 表示第一个）
qtomography reconstruct data.xlsx --sheet 0
```

---

**示例 5：启用正则化（噪声数据）**

```bash
qtomography reconstruct noisy_data.csv \
    --method both \
    --linear-regularization 1e-6 \
    --mle-regularization 1e-6
```

**说明**：
- 适合高噪声数据
- 正则化系数增强数值稳定性

---

**示例 6：MLE 增加迭代次数**

```bash
qtomography reconstruct data.csv \
    --method mle \
    --mle-max-iterations 5000
```

**说明**：
- 适合收敛困难的情况
- 迭代次数越多，耗时越长

---

#### 输入文件格式

**CSV 格式**（推荐）：

```csv
probability
0.8023
0.1977
0.5012
0.4988
```

**Excel 格式**：

| probability |
|-------------|
| 0.8023      |
| 0.1977      |
| 0.5012      |
| 0.4988      |

**要求**：
- 必须有名为 `probability` 的列
- 行数应为 $n^2$（$n$ 是维度）
- 例如：2维系统 → 4行，4维系统 → 16行

---

#### 输出文件结构

执行后会生成以下文件：

```
demo_output/
├── summary.csv          # 汇总报告（所有样本的指标）
└── records/             # 详细记录目录
    ├── record_1_<时间戳>.json  # 第1个样本的详细结果
    ├── record_2_<时间戳>.json  # 第2个样本的详细结果
    └── ...
```

**summary.csv 内容示例** (⭐ Stage 3 扩展后)：

| method | sample | purity | trace | rank | min_eigenvalue | max_eigenvalue | condition_number | eigenvalue_entropy | n_iterations | success | timestamp |
|--------|--------|--------|-------|------|----------------|----------------|------------------|-------------------|--------------|---------|-----------|
| linear | 1 | 0.68 | 1.0 | 2 | 0.32 | 0.68 | 2.125 | 0.664 | - | - | 2025-10-07T10:30:00 |
| mle    | 1 | 0.67 | 1.0 | 2 | 0.33 | 0.67 | - | 0.652 | 45 | True | 2025-10-07T10:30:05 |

**新增字段说明**：
- `rank`: 密度矩阵秩（独立特征值数量）
- `min_eigenvalue` / `max_eigenvalue`: 特征值范围
- `condition_number`: 条件数（仅 Linear，衡量数值稳定性）
- `eigenvalue_entropy`: 特征值熵（混合度量）
- `n_iterations`: 迭代次数（仅 MLE）
- `success`: 优化是否收敛（仅 MLE）

**JSON 记录示例**：

```json
{
  "method": "mle",
  "dimension": 2,
  "purity": 0.67,
  "trace": 1.0,
  "eigenvalues": [0.8, 0.2],
  "density_matrix": [[0.8, 0.0], [0.0, 0.2]],
  "timestamp": "2025-10-07T10:30:05.123456"
}
```

---

### 2️⃣ `summarize` - 结果汇总

**功能**：对 `reconstruct` 生成的 summary.csv 进行统计分析

#### 基本语法

```bash
qtomography summarize <汇总文件> [选项]
```

#### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `summary` | summary.csv 文件路径 | `demo_output/summary.csv` |

#### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--metrics` | 列表 | `purity trace` | 要统计的指标列表 |
| `--compare-methods` | 标志 | 关闭 | 生成 Linear vs MLE 对比报表，包括差异分析和 MLE 优化统计 |
| `--detailed` | 标志 | 关闭 | 显示详细统计信息（最小值、最大值、中位数、25/75分位数） |
| `--output` | 路径 | 无 | 保存汇总报告到文件（支持 `.csv` 或 `.json` 格式） |

#### 可用指标列表

| 指标名称 | 说明 | Linear | MLE |
|---------|------|:------:|:---:|
| `purity` | 纯度（物理特性） | ✅ | ✅ |
| `trace` | 迹（归一化检验） | ✅ | ✅ |
| `fidelity` | 保真度（与输入的接近程度） | ✅ | ✅ |
| `rank` | 矩阵秩（独立性） | ✅ | ✅ |
| `min_eigenvalue` | 最小特征值（正定性检验） | ✅ | ✅ |
| `max_eigenvalue` | 最大特征值（最大占据态） | ✅ | ✅ |
| `eigenvalue_entropy` | 特征值熵（混合度量） | ✅ | ✅ |
| `condition_number` | 条件数（数值稳定性） | ✅ | ❌ |
| `n_iterations` | 迭代次数 | ❌ | ✅ |
| `n_evaluations` | 目标函数评估次数 | ❌ | ✅ |
| `success` | 优化是否收敛 | ❌ | ✅ |
| `bell_max_fidelity` | Bell 态最大保真度（纠缠态分析） | ✅ | ✅ |
| `bell_best_state` | Bell 态最佳匹配态 | ✅ | ✅ |

---

#### 使用示例

**示例 1：默认汇总（purity 和 trace）**

```bash
qtomography summarize demo_output/summary.csv
```

**输出**：
```
📊 重构结果统计汇总：
         mean_purity  std_purity  mean_trace  std_trace
method                                                  
linear        0.6800      0.0150      1.0000     0.0000
mle           0.6750      0.0120      1.0000     0.0000
```

---

**示例 2：自定义指标**

```bash
qtomography summarize demo_output/summary.csv --metrics purity fidelity
```

**输出**：
```
📊 重构结果统计汇总：
         mean_purity  std_purity  mean_fidelity  std_fidelity
method                                                        
linear        0.6800      0.0150         0.9998        0.0002
mle           0.6750      0.0120         0.9999        0.0001
```

---

**示例 3：Linear vs MLE 方法对比** ⭐ **Stage 3 新增**

```bash
qtomography summarize demo_output/summary.csv --compare-methods --metrics purity trace fidelity
```

**输出**：
```
===== Linear vs MLE 对比报告 (配对样本: 10/10) =====

指标: purity
┌──────────┬────────────┬────────────┬────────────┐
│ Method   │ Mean       │ Std        │ Median     │
├──────────┼────────────┼────────────┼────────────┤
│ linear   │     0.6800 │     0.0150 │     0.6790 │
│ mle      │     0.6750 │     0.0120 │     0.6740 │
│ Δ (diff) │ -   0.0050 │     0.0030 │ -   0.0050 │
└──────────┴────────────┴────────────┴────────────┘

指标: trace
┌──────────┬────────────┬────────────┬────────────┐
│ Method   │ Mean       │ Std        │ Median     │
├──────────┼────────────┼────────────┼────────────┤
│ linear   │     1.0000 │     0.0000 │     1.0000 │
│ mle      │     1.0000 │     0.0000 │     1.0000 │
│ Δ (diff) │ +   0.0000 │     0.0000 │ +   0.0000 │
└──────────┴────────────┴────────────┴────────────┘

MLE 优化统计:
  - 成功率: 100.0% (10/10)
  - 平均迭代次数: 45.2 ± 12.3
  - 平均评估次数: 156.8 ± 38.5
```

**说明**：
- 自动配对 Linear 和 MLE 样本（基于 `sample` 列）
- 显示每个指标的均值、标准差、中位数
- Δ 行显示 MLE 相对于 Linear 的差异（Δ = MLE - Linear）
- 包含 MLE 优化统计信息（成功率、迭代次数、评估次数）

---

**示例 4：保存对比报告到 CSV** ⭐ **Stage 3 新增**

```bash
qtomography summarize demo_output/summary.csv \
    --compare-methods \
    --metrics purity trace fidelity \
    --output comparison_report.csv
```

**生成的 CSV 文件**：
```csv
,purity,trace,fidelity
,count,mean,std,min,25%,50%,75%,max,count,mean,std,...
linear,10.0,0.68,0.015,0.65,0.67,0.679,0.69,0.71,10.0,1.0,0.0,...
mle,10.0,0.675,0.012,0.66,0.668,0.674,0.682,0.69,10.0,1.0,0.0,...
```

---

**示例 5：保存对比报告到 JSON** ⭐ **Stage 3 新增**

```bash
qtomography summarize demo_output/summary.csv \
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
      "mean": 0.68,
      "std": 0.015,
      "min": 0.65,
      "25%": 0.67,
      "50%": 0.679,
      "75%": 0.69,
      "max": 0.71
    },
    "trace": {
      "count": 10.0,
      "mean": 1.0,
      "std": 0.0,
      ...
    }
  },
  "mle": {
    "purity": { ... },
    "trace": { ... }
  }
}
```

---

### 3️⃣ `info` - 版本信息

**功能**：显示软件包版本和模块信息

#### 基本语法

```bash
qtomography info
```

#### 输出示例

```
📦 qtomography 版本：0.6.0
📂 核心模块：qtomography.app.controller, qtomography.cli.main
📚 文档目录：docs/
```

---

## 🎯 典型使用场景

### 场景 1：快速验证单个样本

```bash
# 准备数据文件 test.csv
echo "probability" > test.csv
echo "0.8" >> test.csv
echo "0.2" >> test.csv
echo "0.5" >> test.csv
echo "0.5" >> test.csv

# 执行重构
qtomography reconstruct test.csv --dimension 2
```

---

### 场景 2：批量处理多个样本

假设 `batch_data.csv` 包含多行测量概率（每 4 行一个样本）：

```bash
qtomography reconstruct batch_data.csv --method both --output-dir batch_results
```

---

### 场景 3：高噪声数据处理

```bash
qtomography reconstruct noisy_measurements.csv \
    --method both \
    --linear-regularization 1e-5 \
    --mle-regularization 1e-5 \
    --mle-max-iterations 3000 \
    --output-dir noisy_results
```

---

### 场景 4：对比不同方法

```bash
# 1. 仅线性重构
qtomography reconstruct data.csv --method linear --output-dir linear_only

# 2. 仅 MLE 重构
qtomography reconstruct data.csv --method mle --output-dir mle_only

# 3. 两者对比
qtomography reconstruct data.csv --method both --output-dir comparison
```

---

### 场景 5：Excel 数据处理

```bash
# 读取 Excel 的第一个工作表
qtomography reconstruct experiment_data.xlsx --sheet 0

# 读取指定名称的工作表
qtomography reconstruct experiment_data.xlsx --sheet "Results_2024"
```

---

## 🐛 常见问题与解决

### Q1: 提示"输入文件不存在"

**问题**：
```bash
错误：输入文件不存在：data.csv
```

**解决**：
- 检查文件路径是否正确
- 使用绝对路径：`qtomography reconstruct /full/path/to/data.csv`
- 检查当前工作目录：`pwd` (Linux/Mac) 或 `cd` (Windows)

---

### Q2: 维度推断错误

**问题**：
```
ValueError: 概率向量长度应为 4, 实际为 5
```

**解决**：
- 检查数据行数是否为完全平方数（4, 9, 16, 25, ...）
- 手动指定维度：`--dimension 2`

---

### Q3: MLE 不收敛

**问题**：
```
⚠️ MLE 未收敛，迭代次数：2000
```

**解决**：
```bash
# 方法 1：增加迭代次数
qtomography reconstruct data.csv --mle-max-iterations 5000

# 方法 2：启用正则化
qtomography reconstruct data.csv --mle-regularization 1e-6
```

---

### Q4: Excel 工作表不存在

**问题**：
```
ValueError: Worksheet 'Sheet2' not found
```

**解决**：
- 检查工作表名称拼写
- 使用索引：`--sheet 0`（第一个工作表）
- 不指定 `--sheet` 时默认读取第一个工作表

---

## 🔧 高级用法

### 1. Python 脚本中调用

```python
from qtomography.cli.main import main

# 等价于命令行：qtomography reconstruct data.csv --method linear
exit_code = main(['reconstruct', 'data.csv', '--method', 'linear'])
print(f"执行状态码：{exit_code}")
```

---

### 2. 批处理脚本

**Linux/Mac (bash)**：
```bash
#!/bin/bash
for file in data/*.csv; do
    echo "处理文件：$file"
    qtomography reconstruct "$file" --output-dir "results/$(basename $file .csv)"
done
```

**Windows (PowerShell)**：
```powershell
Get-ChildItem -Path data\*.csv | ForEach-Object {
    Write-Host "处理文件：$($_.Name)"
    qtomography reconstruct $_.FullName --output-dir "results\$($_.BaseName)"
}
```

---

### 3. 结合其他工具

**生成数据 → 重构 → 可视化**：

```bash
# 1. 生成测试数据
python scripts/generate_test_data.py --output test_data.csv

# 2. 执行重构
qtomography reconstruct test_data.csv --method both

# 3. 可视化结果
python examples/demo_persistence_visualization.py demo_output/records/record_1_*.json
```

---

## 📚 相关文档

- [项目 README](../../README.md) - 项目概览
- [API 文档](../roadmap/app-controller-cli-plan.md) - 编程接口
- [教学文档](../teach/) - 算法原理
- [测试指南](../../tests/README.md) - 测试方法

---

## ✅ 快速检查清单

使用前检查：

- [ ] 已安装依赖：`pip install -r requirements.txt`
- [ ] 已安装软件包：`pip install -e .`
- [ ] 数据格式正确：有 `probability` 列，行数为 $n^2$
- [ ] 工作目录正确：`cd` 到项目根目录

使用后检查：

- [ ] 输出目录存在：`ls demo_output/`
- [ ] 汇总文件生成：`cat demo_output/summary.csv`
- [ ] JSON 记录存在：`ls demo_output/records/`

---

**文档版本**: v1.0  
**最后更新**: 2025年10月7日  
**作者**: AI Assistant

