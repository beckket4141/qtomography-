# QTomography GUI – MVP 实现状态

> **版本**: 0.2 → **已实现**  
> **撰写日期**: 2025-10-17  
> **最后更新**: 2025年11月  
> **状态**: ✅ **MVP 已完成并投入使用**  
> **目标读者**: GUI 工程师、应用层开发者、产品负责人  
> **背景**: 基于 `qtomography.app.controller` 等现有后端能力构建桌面客户端，作为后续完整 GUI（design_v2）的第一阶段。

---

## 📋 实现状态总结

### ✅ 已实现功能

根据当前代码库（`qtomography/gui/`），以下功能已实现：

1. **数据加载** ✅
   - 通过 `QFileDialog` 选择 `.csv` / `.xlsx` 文件
   - 文件信息显示（`DataPanel`）
   - 数据预览功能

2. **参数配置** ✅
   - 映射 `ReconstructionConfig` 字段（`ConfigPanel`）
   - 方法选择（Linear/MLE 复选框）
   - 维度设置（自动推断/手动）
   - 正则化参数
   - Bell 分析开关
   - 配置保存/加载机制（`GUIConfigUseCase`）

3. **执行控制** ✅
   - 运行/取消按钮（`ExecutePanel`）
   - `ControllerRunner` 后台执行
   - 任务状态管理

4. **进度监控** ✅
   - 进度条和状态显示（`ProgressPanel`）
   - 日志输出
   - 任务完成/失败提示

5. **结果展示** ✅
   - Summary 表格视图（`SummaryPanel`）
   - 图像显示（`FigurePanel`）
   - 支持热力图和3D柱状图切换
   - 结果目录打开功能

6. **谱分解功能** ✅
   - 谱分解面板（`SpectralDecompositionPanel`）
   - 后台执行（`SpectralRunner`）
   - 结果展示和导出

7. **配置持久化** ✅
   - GUI配置保存/加载（`GUIConfigRepository`）
   - 窗口状态保存
   - 默认配置管理

### 📍 实际实现位置

| 功能模块 | 实现位置 | 状态 |
|---------|---------|------|
| 主窗口 | `qtomography/gui/main_window.py` | ✅ |
| 数据面板 | `qtomography/gui/panels/data_panel.py` | ✅ |
| 配置面板 | `qtomography/gui/panels/config_panel.py` | ✅ |
| 执行面板 | `qtomography/gui/panels/execute_panel.py` | ✅ |
| 进度面板 | `qtomography/gui/panels/progress_panel.py` | ✅ |
| Summary面板 | `qtomography/gui/panels/summary_panel.py` | ✅ |
| 图像面板 | `qtomography/gui/panels/figure_panel.py` | ✅ |
| 谱分解面板 | `qtomography/gui/panels/spectral_panel.py` | ✅ |
| 图像查看器 | `qtomography/gui/widgets/image_viewer.py` | ✅ |
| 控制器运行器 | `qtomography/gui/services/controller_runner.py` | ✅ |
| 谱分解运行器 | `qtomography/gui/services/spectral_runner.py` | ✅ |
| 配置用例 | `qtomography/gui/application/use_cases/gui_config_use_case.py` | ✅ |
| 配置仓储 | `qtomography/gui/infrastructure/repositories/gui_config_repository.py` | ✅ |

### 🔄 与原计划的差异

1. **图像显示增强**：实际实现了热力图和3D柱状图两种模式，支持切换
2. **谱分解集成**：MVP阶段已包含谱分解功能，超出原计划范围
3. **配置持久化**：实现了完整的配置保存/加载机制，包括窗口状态
4. **图像查看器**：实现了独立的 `ImageViewer` 组件，支持缩放、拖拽、全屏

### 📝 使用说明

启动GUI：
```bash
python -m qtomography.gui
# 或
python run_gui.py
```

详细使用说明请参考：
- [GUI配置保存机制实现说明](../../gui/GUI配置保存机制实现说明.md)
- [配置机制解耦分析与改动指南](../../gui/配置机制解耦分析与改动指南.md)

---

## 原始设计文档（保留作为参考）

---

## 1. 项目定位与目标

| 项目属性 | 说明 |
| -------- | ---- |
| 核心目标 | 提供可被实验室用户直接使用的最小 GUI，覆盖"选择测量数据 → 设置参数 → 执行重构 → 查看/导出结果"的完整闭环 |
| 用户场景 | 单次批处理；实验人员手动触发任务，查看关键指标与图像，导出结果用于后续分析 |
| 范围限制 | 不实现多任务调度、项目/模板管理、统计回归、JSON/HDF5 自定义输入等 design_v2 中的高级功能 |
| 依赖基础 | PySide6、现有 `ReconstructionController`、`ResultRepository`、`ReconstructionVisualizer` 等模块 |

---

## 2. 功能范围 (MVP)

### 2.1 必须交付

1. **数据加载**
   - 通过 `QFileDialog` 选择 `.csv` / `.xlsx` 文件。
   - 展示文件路径、大小、最近修改时间。
   - 可选预览：读取前 10 行数据（使用 `pandas.read_csv`/`read_excel`）。

2. **参数配置**
   - 映射 `ReconstructionConfig` 字段：方法（Linear/MLE 复选框），维度（可选，自动推断开关），正则化（浮点输入），Bell 分析开关。
   - 合法性校验（维度 ≥ 2、正则化 ≥ 0、迭代次数 > 0）。
   - 支持"恢复默认"按钮。

3. **执行控制**
   - `运行`：禁用配置区域，触发 `run_batch_async`，创建输出目录。
   - `取消`：设置 `cancel_event`，终止正在运行的任务。
   - 阻止重复运行（Future 完成之前按钮置灰）。

4. **进度监控**
   - 进度条（0~100%）+ 文本状态（stage、样本索引）。
   - 滚动日志面板（`QPlainTextEdit` 只读）显示 `ProgressEvent` message / `logging` 输出。
   - 任务完成/失败/取消时弹出信息对话框。

5. **结果展示**
   - `summary.csv` 表格视图 (`QTableView` + 自定义 `QAbstractTableModel`)。
   - 基于 `ReconstructionVisualizer` 的热力图展示（线性 & MLE 切换；样本切换），使用 `qt_adapter.figure_to_pixmap`.
   - 结果目录路径显示，并提供"打开目录"按钮 (`QDesktopServices.openUrl`)。

6. **导出**
   - 复制 `summary.csv` 路径。
  - 允许用户点击按钮直接在文件浏览器中打开输出文件夹。

### 2.2 可选（优先级较低）

- 记住最近一次使用的输入目录/输出目录（写入 `QSettings`）。
- 在 Summary 表格中提供筛选/排序（`QSortFilterProxyModel`）。
- 简单的错误报告导出（复制日志文本）。

---

## 3. UI 整体布局

```
┌───────────────────────────────────────────────────────┐
│ 菜单栏： 文件 | 视图 | 帮助                             │
├───────────────────────────────────────────────────────┤
│ 工具栏： [打开数据] [运行] [取消] [打开输出目录]        │
├───────────────────────────────────────────────────────┤
│ QSplitter (水平)                                       │
│ ┌────────────────┬───────────────────────────────────┐ │
│ │ 左侧（控制面板）│ 右侧（结果与进度）                 │ │
│ │ QTabWidget     │ QTabWidget                        │ │
│ └────────────────┴───────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

### 3.1 左侧控制面板 (Tabs)

1. **数据**  
   - 文件路径输入框 + "浏览…" 按钮。  
   - 文件信息 (`QLabel` 列表)。  
   - 可选预览按钮：弹出对话框展示数据表。

2. **参数**  
   - 重构方法 (`QCheckBox`)：Linear / MLE。  
   - Bell 分析 (`QCheckBox`)。  
   - 维度：`QSpinBox` + "自动推断"复选框。  
   - 正则化：`QDoubleSpinBox`（Linear/MLE 各一个）。  
   - 迭代次数 `QSpinBox`（MLE）。  
   - 容差 `QDoubleSpinBox`。  
   - 保存当前配置到 JSON 的按钮（调用 `config_io.dump_config_file`）。

3. **执行**  
   - 输出目录 (`QLineEdit`) + 浏览按钮。  
   - "运行"、"取消"、"重置表单"按钮。  
   - 当前状态标签（Idle / Running / Cancelled / Completed）。

### 3.2 右侧输出面板 (Tabs)

1. **进度**  
   - 进度条 (`QProgressBar`)。  
   - 阶段信息 (`QLabel`)。  
   - 样本信息：当前样本、总样本数。  
   - 日志窗口 (`QPlainTextEdit`，带自动滚动)。

2. **Summary**  
   - 表格视图 + 工具栏：刷新、复制路径、导出为 Excel（可选）。  
   - 显示当前 `summary.csv` 全部列，支持列宽自动适配。

3. **可视化**  
   - 组合控件：  
     - 样本选择 (`QComboBox`)。  
     - 方法切换 (`QComboBox` 或 `QTabWidget`)。  
     - 图像显示 (`QLabel` + `QPixmap`)。  
   - 默认展示热力图；留出接口为 Stage 2 添加 3D 柱状图/趋势图。

---

## 4. 后端交互与线程模型

### 4.1 控制器 Runner

```
class ControllerRunner(QObject):
    started = Signal()
    progress = Signal(ProgressEvent)
    finished = Signal(SummaryResult)
    failed = Signal(str)
    cancelled = Signal(str)

    def start(self, config: ReconstructionConfig, output_dir: Path) -> None: ...
    def cancel(self) -> None: ...
```

- 内部持有 `ReconstructionController`。
- `start()` 创建 `ThreadPoolExecutor`，调用 `run_batch_async`，保存 `Future`。
- 进度回调通过 `progress.emit` 转发给主线程。
- Future 完成后触发 `finished` / `failed` / `cancelled` 信号。
- `cancel()` 设置 `threading.Event`，并记录取消时间。

### 4.2 主窗口响应

1. 用户点击运行 → `ControllerRunner.start(...)`。  
2. `started` 信号：禁用配置面板，清空日志。  
3. `progress` 信号：更新进度条/日志。  
4. `finished` 信号：  
   - 重新启用配置面板。  
   - 加载 Summary 表格 (`pandas.read_csv`)。  
   - 触发图像面板刷新（线性/ MLE 各取第一条样本）。  
   - 弹出"完成"消息框。  
5. `failed` 或 `cancelled`：恢复界面、提示用户。

### 4.3 日志捕获

```python
class QtLogHandler(logging.Handler):
    message_emitted = Signal(str)

    def emit(self, record):
        self.message_emitted.emit(self.format(record))
```

- 主窗口注册 `QtLogHandler`，附加到 `controller` 的 logger。
- 日志面板监听 `message_emitted`，插入文本。

---

## 5. 模块划分与职责

| 包/模块 | 主要类/函数 | 职责 |
| ------- | ---------- | ---- |
| `qtomography.gui.__init__` | `main()` | GUI 入口，创建 `QApplication`，实例化主窗口 |
| `qtomography.gui.main_window` | `MainWindow` | 负责整体布局、菜单、信号连接 |
| `qtomography.gui.panels.data_panel` | `DataPanel` | 文件选择 & 预览 |
| `qtomography.gui.panels.config_panel` | `ConfigPanel` | 参数表单，出产 `ReconstructionConfig` |
| `qtomography.gui.panels.execute_panel` | `ExecutePanel` | 输出目录选择、运行/取消按钮 |
| `qtomography.gui.panels.progress_panel` | `ProgressPanel` | 进度条、状态、日志视图 |
| `qtomography.gui.panels.summary_panel` | `SummaryPanel` | `QTableView` + 模型 |
| `qtomography.gui.panels.figure_panel` | `FigurePanel` | 图像展示，调用 `qt_adapter` |
| `qtomography.gui.services.controller_runner` | `ControllerRunner` | 线程管理、进度信号 |
| `qtomography.gui.models.summary_model` | `SummaryTableModel` | 将 DataFrame 映射到 Qt Model |

> **说明**：初期可将所有 widget 放在单文件中，待 MVP 稳定后再按模块拆分。

---

## 6. 数据与状态流

```
用户操作 → 表单状态更新 → ConfigPanel 生成 config →
ExecutePanel 指定 output_dir →
ControllerRunner.start(config, output_dir) →
后台 run_batch_async → ProgressEvent → ProgressPanel →
任务完成 → Summary/Figure Panel 刷新 → 用户导出/新任务
```

- 表单状态存储在各 Panel 内部，通过信号方法 `build_config()` 统一生成 `ReconstructionConfig`。
- 主窗口负责协调：当任一表单字段变化时更新内部状态 `UiState`（可用 `dataclasses`）。
- `ControllerRunner` 结束后更新 `LastResult` 数据类，供 Summary/Figure 面板使用。

---

## 7. 错误处理与验证策略

| 情况 | 行为 |
| ---- | ---- |
| 文件不存在或格式错误 | 阻止运行，显示 `QMessageBox.critical` + 日志 |
| `ReconstructionConfig` 验证失败 | 参数面板显示红色边框，提示具体字段错误 |
| 重构过程中 `ReconstructionError` | 终止任务，日志显示异常堆栈，弹出错误对话框 |
| 用户取消 | 日志记录"用户取消"，状态栏提示，可立即重新运行 |
| GUI 崩溃保护 | 后台线程异常统一捕获，确保主线程不会退出 |

---

## 8. 开发里程碑

| 里程碑 | 内容 | 预估人日 |
| ------ | ---- | -------- |
| **M1** | 建立项目骨架：应用入口、主窗口、数据/参数/执行面板静态 UI | 2 |
| **M2** | 集成 `ControllerRunner`、进度事件、日志输出，完成运行/取消流程 | 3 |
| **M3** | 实现 Summary 表格、Figure 面板，完成结果展示与导出 | 2 |
| **M4** | 错误处理、表单校验、用户体验打磨（状态同步、按钮置灰） | 2 |
| **缓冲** | Bugfix、文档、手册与打包脚本 | 1 |

---

## 9. 依赖与运行要求

- Python ≥ 3.9  
- `pip install -e .[gui]`（当前 extra 只包含 PySide6，后续可扩展）  
- 运行方式：`python -m qtomography.gui`（待实现入口）  
- 推荐在虚拟环境中执行，保证与 CLI/测试环境分离。

---

## 10. 非 MVP 功能（Stage 2+ 展望）

1. **多数据源支持**：JSON/HDF5 导入、自定义矩阵编辑器。  
2. **批量任务管理**：任务队列、暂停/恢复、历史记录持久化。  
3. **高级分析**：Bell 分析可视化、统计检验、方法对比图表。  
4. **项目/模板管理**：保存/加载配置模板、工作区概念。  
5. **UI 优化**：主题切换、国际化、可拖拽布局。  
6. **自动化测试**：Qt Test + pytest-qt，覆盖关键交互。

---

## 11. 建议的开发流程

1. **搭建仓库结构**：`qtomography/gui` 包、入口脚本、基础 Panel 类。  
2. **实现 Runner 与信号机制**，验证与 `controller.run_batch_async` 协作。  
3. **完成各 Panel 的 UI 与数据绑定**，确保配置 → Controller 的数据流无误。  
4. **引入图像展示与表格展示**，确认 `qt_adapter` 正常工作。  
5. **进行集成测试与手动验收**，按照验收标准逐项验证。  
6. **撰写用户指南**（部署、数据要求、常见问题）。  
7. **评估 Stage 2 需求**，在此文档基础上扩展 design_v2 对应功能。

---

## 12. 验收标准

1. 成功加载 CSV/Excel，正确推断维度或使用手动维度。  
2. 执行过程中进度条、日志实时更新；取消操作即时生效。  
3. 重构完成后自动展开 Summary 表格与热力图，并可打开结果目录。  
4. 运行失败或参数错误时有清晰的用户提示，界面恢复可继续使用。  
5. 从命令行启动 GUI 无依赖缺失，使用说明齐备。

---

## 13. 后续工作追踪

> 建议在 Issue/Project Board 中创建以下任务：

1. `GUI-01`：创建 PySide6 骨架与入口。  
2. `GUI-02`：实现数据/参数/执行面板与配置构建。  
3. `GUI-03`：集成 ControllerRunner，支持运行与取消。  
4. `GUI-04`：进度面板与日志联动。  
5. `GUI-05`：Summary 表格 & 可视化展示。  
6. `GUI-06`：错误处理、测试与文档。

完成以上任务后，即可向 Stage 2 过渡，实现 design_v2 的高级模块与页面。

---

