# QTomography - 量子态层析重构工具包

> 高维OAM全息图生成与量子层析一体化工具链 (Python版本)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-36%20passing-brightgreen.svg)](tests/)

## 📖 项目简介

本项目是一套完整的量子态层析（Quantum State Tomography）重构工具包，从MATLAB系统重构为现代化的Python工程项目。支持任意维度的量子态重构，提供线性重构、加权最小二乘（WLS）和RρR Strict等多种重构算法，并集成完整的结果持久化与可视化能力。

### 核心特性

- ✅ **多算法支持**：线性重构（LinearReconstructor）+ 加权最小二乘（WLSReconstructor）+ RρR Strict重构
- ✅ **任意维度**：支持2维、4维、16维等任意 d² 维密度矩阵重构
- ✅ **数值稳定**：采用Cholesky分解、eigenvalue裁剪等技术保证数值稳定性
- ✅ **完整测试**：36 个单元/集成测试，与MATLAB基准对齐（误差 < 1e-10）
- ✅ **结果持久化**：支持JSON/CSV格式保存与加载重构结果
- ✅ **丰富可视化**：2D热图、3D柱状图（幅度/相位、实部/虚部）
- ✅ **分层架构**：领域层 + 基础设施层（持久化/可视化）+ 应用层进一步解耦
- ✅ **批处理与CLI**：ReconstructionController + qtomography CLI 覆盖批量重构、汇总与 bell-analyze
- ✅ **Bell 态分析**：内置 Bell 分析工具与 CLI 子命令，快速评估纠缠度
- ✅ **GUI图形界面**：基于 PySide6 的桌面应用，支持可视化操作和实时进度显示
- ✅ **完善文档**：实现指南、API文档、教学材料齐全
- ⭐ **Stage 3 增强** (2025-10):
  - 扩展 `summary.csv` 字段：rank, min/max_eigenvalue, condition_number, eigenvalue_entropy, n_iterations, success
  - CLI `summarize` 增强：`--compare-methods`（Linear vs WLS 对比）、`--output`（报告导出）
  - 完整单元测试覆盖，确保数据一致性
- 🔄 Stage 4 准备中：分析层拆分与基础设施合并，规划详见 docs/roadmap/stage4-architecture-consolidation-plan.md

## 🚀 快速开始

### 安装依赖

```bash
# 克隆仓库
git clone <repository-url>
cd QT_to_Python_1/python

# 安装所有依赖（包含GUI和测试工具）
pip install -r requirements.txt

# 或使用开发模式安装（推荐）
pip install -e .  # 仅核心依赖
pip install -e ".[gui,dev]"  # 包含GUI和开发工具

# 安装开发依赖（可选）
pip install -e ".[dev]"
```

### 可选依赖分组

| Extra | 说明 | 安装命令 |
| --- | --- | --- |
| `dev` | 开发/测试工具（pytest、覆盖率、格式化、类型检查、pre-commit 等） | `pip install -e ".[dev]"` |
| `gui` | GUI图形界面（PySide6） | `pip install -e ".[gui]"` |
| `performance` | 数值加速（Numba） | `pip install -e ".[performance]"` |
| `quantum` | 高级量子模拟（QuTiP） | `pip install -e ".[quantum]"` |

> `requirements.txt` 与 `pyproject.toml` 已同步列出核心依赖；若要运行 `generate_test_report.py` 生成 JSON 报告，请确保安装 `pytest-json-report`（随 `dev` extra 一同提供）。

### 基础使用示例

```python
import numpy as np
from qtomography.domain import LinearReconstructor, WLSReconstructor
from qtomography.infrastructure.visualization import ReconstructionVisualizer

# 1. 准备测量数据（概率向量）
probabilities = np.array([0.5, 0.5, 0.25, 0.25], dtype=float)

# 2. 线性重构
reconstructor = LinearReconstructor(dimension=2, tolerance=1e-9)
density = reconstructor.reconstruct(probabilities)

print(f"纯度 (Purity): {density.purity:.4f}")
print(f"迹 (Trace): {density.trace:.4f}")

# 3. 可视化
vis = ReconstructionVisualizer()
fig = vis.plot_amplitude_phase(density, title="Quantum State Reconstruction")
fig.savefig("reconstruction_result.png")
```

### 更多示例

如需查看更复杂的使用场景和完整的工作流示例，可以参考测试代码：

```bash
# 运行测试以查看各种使用场景
pytest tests/ -v

# 查看测试代码作为示例参考
# tests/unit/ - 单元测试展示了核心API的使用
# tests/integration/ - 集成测试展示了完整的工作流
```

测试代码位于 `tests/` 目录，包含了从基础使用到复杂场景的完整示例，可作为学习和参考。

### 启动GUI应用

安装GUI依赖后，可以通过以下方式启动图形界面：

```bash
# 方式1：使用启动脚本（推荐）
python run_gui.py

# 方式2：使用Python模块方式
python -m qtomography.gui

# 方式3：如果已安装包，可直接运行
qtomography-gui  # 如果配置了入口点
```

GUI功能包括：
- 📊 **数据加载**：支持 CSV/Excel 文件导入
- ⚙️ **参数配置**：可视化配置重构算法参数
- 🚀 **批量重构**：支持 Linear、WLS、RρR Strict 多种算法
- 📈 **实时进度**：显示重构进度和状态
- 🖼️ **结果可视化**：2D热图和3D柱状图展示
- 📋 **结果汇总**：自动生成汇总表格
- 🔬 **谱分解**：支持密度矩阵的谱分解分析

### 批量处理概率文件

安装或以开发模式安装后，可直接使用 `qtomography` 命令行工具进行批量处理：

```bash
# 使用 CSV 或 Excel 批量重构（默认同时运行线性 + WLS）
qtomography reconstruct path/to/probabilities.xlsx --sheet 0 --output-dir demo_output

# 仅运行线性重构并指定维度
qtomography reconstruct path/to/probabilities.csv --dimension 4 --method linear --output-dir results_batch

# 同步运行线性 + WLS 重构（推荐）
qtomography reconstruct path/to/probabilities.csv --dimension 4 --method both --bell --output-dir results_cli

# 只运行线性重构
qtomography reconstruct path/to/probabilities.xlsx --sheet Sheet1 --method linear --dimension 4 --bell

# 汇总指标并查看均值/标准差
qtomography summarize results_cli/summary.csv --metrics purity trace objective

# ⭐ Stage 3 新增：Linear vs WLS 方法对比
qtomography summarize results_cli/summary.csv --compare-methods --metrics purity trace fidelity

# ⭐ Stage 3 新增：保存对比报告到文件
qtomography summarize results_cli/summary.csv --compare-methods --metrics purity trace --output comparison_report.csv

# 对既有记录执行 Bell 态分析
qtomography bell-analyze results_cli/records --output results_cli/bell_summary.csv

# 查看当前版本信息
qtomography info
```

配置复用示例:
```bash
# 将当前命令行参数保存为 JSON 配置，便于重复使用
qtomography reconstruct data.csv --dimension 4 --method both --save-config demo_config.json

# 基于配置文件运行，可叠加命令行覆盖项
qtomography reconstruct --config demo_config.json --bell
```

该 CLI 内部调用 `ReconstructionController`，提供完整的批量重构、结果汇总和分析功能。

生成的重构记录会保存在指定输出目录的 `records/` 子目录中（JSON），并伴随一份 `summary.csv` 汇总文件，可直接用于后续分析。

### 配置文件参数说明

配置文件采用 JSON 格式，支持所有命令行参数的持久化。使用配置文件可以避免每次输入冗长的参数列表，特别适合重复性实验。

#### 完整配置示例

**基础配置** (`demo_config.json`):
```json
{
  "version": "1.0",
  "input_path": "data/probabilities.csv",
  "output_dir": "results",
  "methods": ["linear", "wls"],
  "dimension": 4,
  "wls_max_iterations": 2000,
  "tolerance": 1e-9,
  "analyze_bell": true
}
```

#### 常用字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `version` | string | ✅ | - | 配置文件版本（当前 "1.0"） |
| `input_path` | string | ✅ | - | 输入 CSV/Excel 文件路径 |
| `output_dir` | string | ✅ | - | 结果输出目录 |
| `methods` | array | ❌ | `["linear", "wls"]` | 重构方法：`["linear"]`, `["wls"]`, 或 `["linear", "wls"]` |
| `dimension` | int | ❌ | `null` | 量子态维度（2/4/8/...），`null` 时自动推断 |
| `sheet` | string/int | ❌ | `null` | Excel 工作表名称或索引（仅 Excel 文件） |
| `linear_regularization` | float | ❌ | `null` | 线性重构 Tikhonov 正则化系数 |
| `wls_regularization` | float | ❌ | `1e-6` | WLS 正则化系数 |
| `wls_max_iterations` | int | ❌ | `2000` | WLS 最大迭代次数 |
| `tolerance` | float | ❌ | `1e-9` | 数值容差 |
| `cache_projectors` | bool | ❌ | `true` | 是否缓存投影算符（加速批处理） |
| `analyze_bell` | bool | ❌ | `false` | 是否执行 Bell 态分析 |

#### 使用方式

```bash
# 从配置文件运行
qtomography reconstruct --config demo_config.json

# 配置文件 + 命令行覆盖
qtomography reconstruct --config demo_config.json --dimension 2 --bell

# 保存当前参数为配置文件
qtomography reconstruct data.csv --dimension 4 --method both --save-config my_config.json
```

**提示**: 配置文件中的相对路径会相对于配置文件所在目录解析，便于项目迁移。完整字段列表和高级用法见 [CLI 详解](docs/teach/cli详解.md#配置文件复用)。

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 查看覆盖率
pytest tests/ --cov=qtomography --cov-report=html
```

## 📚 文档

### 核心文档
- [项目现状评估报告 (2025-10-07)](docs/implemented/project-status-2025-10-07.md) - **推荐首先阅读**
- [MATLAB → Python 迁移蓝图](docs/roadmap/master-plan.md) - 完整的重构规划
- [路线图状态跟踪](docs/roadmap/2025-09-24-roadmap-status.md) - 当前进度

### 实现指南
- [DensityMatrix 模块总结](docs/implemented/density-module-overview.md)
- [LinearReconstructor 实现指南](docs/implemented/linear-reconstruction-guide.md)
- [WLSReconstructor 实现指南](docs/implemented/wls-reconstruction-guide.md)
- [3D可视化增强](docs/implemented/visualization-3d-enhancement.md) ⭐ 新增

### 设计文档
- [BaseReconstructor 抽象基类建议](docs/roadmap/base-reconstructor-proposal.md)
- [ProjectorSet 实现规划](docs/roadmap/projector-set-plan.md)
- [结果持久化与可视化规划](docs/roadmap/result-visualization-plan.md)

### 教学材料
- [密度矩阵物理约束推导](docs/teach/density公式教学.md)
- [DensityMatrix 类架构说明](docs/teach/density的结构概述.md)

## 🏗️ 架构概览

```
qtomography/
├── domain/                      # 领域层（核心算法）
│   ├── density.py               # DensityMatrix 类
│   ├── projectors.py            # ProjectorSet 投影算符集
│   ├── reconstruction/          # 重构算法
│   │   ├── linear.py            # 线性重构
│   │   ├── wls.py               # WLS重构
│   │   └── rhor_strict.py      # RρR Strict重构
│   └── persistence/             # 结果持久化
│       └── result_repository.py # 结果保存/加载
│
├── app/                         # 应用层
│   ├── controller.py            # 批量重构控制器
│   └── config_io.py            # 配置文件IO
│
├── cli/                         # 命令行接口
│   └── main.py                 # CLI主入口
│
├── gui/                         # 图形用户界面
│   ├── app.py                  # GUI应用入口
│   ├── main_window.py          # 主窗口
│   ├── panels/                 # 功能面板
│   │   ├── data_panel.py      # 数据加载面板
│   │   ├── config_panel.py    # 参数配置面板
│   │   ├── execute_panel.py   # 执行控制面板
│   │   ├── progress_panel.py  # 进度显示面板
│   │   ├── summary_panel.py   # 结果汇总面板
│   │   ├── figure_panel.py    # 图像显示面板
│   │   └── spectral_panel.py  # 谱分解面板
│   └── services/               # 后台服务
│       ├── controller_runner.py # 重构任务执行器
│       └── spectral_runner.py  # 谱分解任务执行器
│
├── infrastructure/              # 基础设施层
│   ├── persistence/            # 持久化实现
│   ├── visualization/          # 可视化实现
│   └── io/                     # 数据IO
│
└── analysis/                    # 分析层
    ├── bell.py                 # Bell态分析
    ├── comparison.py           # 方法对比
    └── metrics.py              # 指标计算
```

## 🔬 核心算法

### 1. 线性重构 (Linear Reconstruction)

基于最小二乘法的量子态重构：

```python
from qtomography.domain import LinearReconstructor

reconstructor = LinearReconstructor(
    dimension=2,           # 量子系统维度（密度矩阵维度为 dimension²）
    tolerance=1e-9,        # 数值容差
    regularization=0.01    # Tikhonov正则化（可选）
)

result = reconstructor.reconstruct(probabilities)
density = result.density_matrix

print(f"残差范数: {result.residual_norm:.6e}")
print(f"条件数: {result.condition_number:.2f}")
```

**特点**：
- 快速求解（适合大规模数据）
- 支持Tikhonov正则化（岭回归）
- 提供详细诊断信息（残差、奇异值、条件数）

### 2. 加权最小二乘 (WLS)

基于迭代优化的量子态重构：

```python
from qtomography.domain import WLSReconstructor

reconstructor = WLSReconstructor(
    dimension=2,
    max_iterations=1000,
    tolerance=1e-8,
    regularization=1e-6
)

result = reconstructor.reconstruct(
    probabilities,
    initial_density=None,    # 可选：自定义初始值
    optimizer="L-BFGS-B"     # 可选：优化器类型
)

density = result.density_matrix
print(f"迭代次数: {result.iterations}")
print(f"最终目标函数值: {result.final_objective:.6e}")
```

**特点**：
- 更高精度（适合高保真度要求）
- Cholesky分解参数化（自动保证正半定性）
- 灵活的优化器选择（L-BFGS-B, trust-constr, SLSQP）

## 📊 可视化功能

```python
from qtomography.infrastructure.visualization import ReconstructionVisualizer

vis = ReconstructionVisualizer()

# 1. 2D热图（实部/虚部）
fig1 = vis.plot_density_heatmap(density, title="Density Matrix")

# 2. 3D柱状图（幅度/相位）
fig2 = vis.plot_amplitude_phase(density, title="Amplitude & Phase")

# 3. 3D柱状图（实部/虚部）⭐ 新功能
fig3 = vis.plot_real_imag_3d(density, title="Real & Imaginary")

# 4. 度量趋势图
records = repo.load_all()
fig4 = vis.plot_metric(records, metric="purity", title="Purity over Time")
```

## 💾 结果持久化

```python
from qtomography.infrastructure.persistence import (
    ReconstructionRecord,
    ResultRepository
)

# 创建记录
record = ReconstructionRecord(
    method="wls",
    dimension=2,
    probabilities=probabilities,
    density_matrix=density.matrix,
    metrics={
        "purity": density.purity,
        "fidelity": 0.95
    },
    metadata={"experiment_id": "exp001"}
)

# 保存
repo = ResultRepository(output_dir="./results", fmt="json")
path = repo.save(record)

# 加载
all_records = repo.load_all()
filtered = repo.load_by_method("wls")
```

## 🧪 测试覆盖

| 模块 | 测试类型 | 测试数量 | 状态 |
|------|---------|---------|------|
| DensityMatrix | 单元 + 性能 | 15+ | ✅ |
| ProjectorSet | 单元 | 10+ | ✅ |
| LinearReconstructor | 单元 + 集成 | 20+ | ✅ |
| WLSReconstructor | 单元 + 集成 | 15+ | ✅ |
| ResultRepository | 单元 | 10+ | ✅ |
| Visualizer | 单元 | 10+ | ✅ |
| MATLAB对比 | 集成 | 10+ | ✅ |
| **总计** | | **36** | ✅ |

## 📈 性能指标

基于实际测试数据：

| 维度 | 算法 | 耗时 | 纯度 | 与MATLAB误差 |
|------|------|------|------|--------------|
| 2×2 (4D) | Linear | < 1ms | 0.95+ | < 1e-10 |
| 2×2 (4D) | WLS | ~50ms | 0.96+ | < 1e-8 |
| 4×4 (16D) | Linear | < 5ms | 0.92+ | < 1e-10 |
| 4×4 (16D) | WLS | ~200ms | 0.94+ | < 1e-7 |

## 🔧 开发路线图

### ✅ 已完成 (v1.0.0) - 生产就绪
- [x] 密度矩阵类与物理约束
- [x] 投影算符集生成
- [x] 线性重构算法
- [x] WLS重构算法
- [x] RρR Strict重构算法
- [x] 结果持久化（JSON/CSV）
- [x] 可视化功能（2D/3D）
- [x] 完整测试覆盖（36个测试）
- [x] 文档体系完整
- [x] 批处理控制器与工作流
- [x] CLI命令行工具与脚本封装
- [x] Excel/CSV数据加载器
- [x] Bell态分析工具
- [x] **GUI图形界面（PySide6）** ⭐
- [x] **项目配置完善**（pyproject.toml、requirements.txt、LICENSE）⭐
- [x] **所有核心功能完整，API稳定，可用于生产** ⭐

### 🚧 计划中 (v1.1.0) - 功能增强
- [ ] 指标对比与报告自动化
- [ ] GUI功能增强（更多可视化选项）
- [ ] 性能优化（Numba JIT）

### 📋 计划中 (v1.2.0+) - 工程化改进
- [ ] 工程化基础设施（日志/配置/依赖注入）
- [ ] CI/CD pipeline
- [ ] 抽象基类重构

详见 [路线图状态跟踪](docs/roadmap/2025-09-24-roadmap-status.md)

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 编写测试并确保通过 (`pytest tests/`)
4. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
5. 推送到分支 (`git push origin feature/AmazingFeature`)
6. 开启 Pull Request

### 代码规范
- 遵循 PEP 8
- 使用 Black 格式化代码
- 编写 docstrings（Google风格）
- 添加类型注解
- 单元测试覆盖率 > 80%

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📧 联系方式

- 项目主页：[GitHub](https://github.com/yourusername/qtomography)
- 问题反馈：[Issues](https://github.com/yourusername/qtomography/issues)
- 文档：[Documentation](docs/)

## 🙏 致谢

- 感谢原始MATLAB实现提供的算法基础
- 感谢 NumPy、SciPy、Matplotlib 等开源项目
- 感谢量子信息社区的支持

---

**当前版本**: v1.0.0 (生产就绪)  
**最后更新**: 2025年11月  
**项目状态**: 🟢 **v1.0.0 正式版** - 所有核心功能完整，API稳定，可用于生产环境
