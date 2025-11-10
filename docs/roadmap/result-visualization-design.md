# Result Repository & Visualization Plan

_Last updated: 2025-10-07_

## 1. 背景与目标
- 线性重构与 MLE 重构均已稳定，我们需要提供结果持久化与基础可视化能力，便于批量实验记录和快速诊断。
- 本阶段对应路线图中的 P1-1（结果持久化与可视化基线）和 P1-2（保真度数值稳健性提升）。

## 2. ResultRepository 设计
### 2.1 目标
- 提供统一的接口，将重构结果（密度矩阵、概率、指标）保存为 CSV / JSON / HDF5 等格式。
- 支持从文件中读取记录，便于分析和复现。

### 2.2 API 草案
```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ReconstructionRecord:
    method: str  # "linear" / "mle"
    dimension: int
    probabilities: list[float]
    density_matrix: list[list[complex]]  # 或 numpy 序列化
    metrics: dict[str, float]  # fidelity, purity, residuals 等
    metadata: dict[str, str] | None = None

class ResultRepository:
    def __init__(self, root: Path, *, fmt: str = "json"):
        ...

    def save(self, record: ReconstructionRecord) -> Path:
        ...

    def load_all(self) -> list[ReconstructionRecord]:
        ...

    def to_dataframe(self) -> pandas.DataFrame:
        ...
```
- 默认使用 JSON 或 CSV；对于大矩阵可选 HDF5。
- 提供扩展点：命名规则（时间戳/UID）、批量保存、清理等。

### 2.3 数据结构与兼容
- 与线性/MLE 重构输出的数据结构对齐（`DensityMatrix`、`LinearReconstructionResult`、`MLEReconstructionResult`）。
- 保存时需序列化 complex 数据，可使用 `numpy.ndarray.tolist()` 或自定义编码方案。
- 支持附加用户元信息（如实验批次、噪声模型、备注）。

## 3. 可视化基线
### 3.1 模块目标
- 提供简单的矩阵可视化（实部/虚部热力图、相位图）以及保真度/纯度曲线或柱状图。
- 输出图像（PNG/SVG）或直接显示（Jupyter/脚本）。

### 3.2 API 草案
```python
class ReconstructionVisualizer:
    def plot_density_heatmap(self, density: DensityMatrix, *, title: str = "") -> matplotlib.figure.Figure:
        ...  # 实部/虚部双面板

    def plot_amplitude_phase(self, density: DensityMatrix) -> matplotlib.figure.Figure:
        ...

    def plot_metrics(self, records: list[ReconstructionRecord], metric: str) -> matplotlib.figure.Figure:
        ...
```
- 使用 matplotlib / seaborn；根据记录列表绘制保真度、chi² 等轨迹。
- 与 ResultRepository 集成：可直接从 `records` 数据生成图。

### 3.3 示例脚本
- 在 `python/examples/` 增加示例：读取保存的记录 → 生成图像 → 保存到 `results/plots/`。
- Jupyter notebook 演示线性和 MLE 的可视化对比。

## 4. 保真度数值稳健性（P1-2）
- `DensityMatrix.fidelity` 当前已具备基本稳定性（eigh + 容差裁剪）。
- P1-2 的补充措施：
  * 在可视化模块中增加保真度/迹距离比较，便于监控数值波动。
  * 在 ResultRepository 中记录保真度计算时的容差、平方根方法等参数。
  * 提供工具函数：批量对比实验数据与理论态的保真度差异统计。

## 5. 测试计划
- **ResultRepository 单元测试** (`python/tests/unit/test_result_repository.py`)
  * 保存/读取单条记录（JSON/CSV/HDF5）
  * 批量读取、DataFrame 输出
  * 错误处理（路径不存在、格式不支持、complex 序列化等）

- **可视化单元测试** (`python/tests/unit/test_visualization.py`)
  * 使用固定密度矩阵生成热力图、相位图，检查 Figure 对象。
  * 在无显示环境下渲染（使用 Agg backend）。

- **集成测试** (`python/tests/integration/test_persistence_and_visualization.py`)
  * 对线性/MLE 重构结果保存 → 读取 → 生成图像（可只检查文件生成成功）。
  * 验证保真度统计函数在批量样本上的输出。

## 6. 文档与示例
- 新增 `docs/implemented/result-repository-guide.md`、`docs/implemented/visualization-guide.md`（或合并为单篇）。
- 更新 `README.md` 与路线图状态，标明 P1-1、P1-2 的完成情况。
- 提供示例脚本/Notebook（`examples/persistence_visualization_demo.py` 或 `.ipynb`）。

## 7. 实施步骤
1. 初始化 `ResultRepository` 类与 `ReconstructionRecord` 数据类。
2. 实现 JSON/CSV 保存与读取；后续可扩展 HDF5。
3. 编写 ResultRepository 单元测试。
4. 实现 `ReconstructionVisualizer`：热力图、幅度/相位、指标曲线。
5. 编写可视化相关测试，确保在批量/无屏幕环境下可运行。
6. 编写集成示例与脚本，演示从重构 → 保存 → 读取 → 可视化的流程。
7. 更新文档与路线图，并添加使用说明。

## 8. 后续扩展
- 支持更多输出格式（Parquet、Feather 等）。
- 与 CLI / Pipeline 对接，实现批量实验自动保存与可视化。
- 可视化模块加入交互式仪表板（Plotly、Panel 等）。
- 对保真度、纯度、迹距离等指标支持阈值报警或统计分析。
- 与 Bell 态分析、结果报告生成工具（如 `generate_test_report.py`）联动。
