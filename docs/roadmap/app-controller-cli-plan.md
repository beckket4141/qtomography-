# Application Controller & CLI Plan

_Last updated: 2025-10-07_
_Status: 📝 设计草案_

## 1. 背景与目标

- 项目目前通过脚本 (`examples/…`, `scripts/process_batch.py`) 触发重构流程，缺乏统一入口。
- P2-2 阶段目标是在保持脚本灵活性的同时，提供**标准化 CLI** 与**轻量控制器**，便于批处理自动化、CI 集成与后续 GUI 封装。
- 目标输出：
  1. `qtomography.app.controller` 模块，封装重构工作流（输入解析 → 重构器选择 → 持久化 → 汇总）。
  2. `qtomography.cli` 命令行入口，提供一致的参数界面（单次、批量、结果查询）。
  3. 必要的测试与文档，覆盖核心分支。

## 2. 设计原则

1. **模块化**：控制器只协调整体流程，重构逻辑继续复用 `LinearReconstructor` / `MLEReconstructor` / `ResultRepository`。
2. **无状态/幂等**：CLI 调用同一输入应生成同样输出，便于集成测试。
3. **可扩展**：新增重构器或指标时，无需修改 CLI 主体，只需注册新策略。
4. **易测性**：核心流程落地在可直接调用的 Python API，再由 CLI 包装，避免测试只能运行为系统命令。

## 3. 功能切分

### 3.1 控制器层 (`qtomography/app/controller.py`)

- `ReconstructionConfig` dataclass：描述输入文件、维度、方法、正则化、输出目录等。
- `ReconstructionController`：
  - `run_batch(config: ReconstructionConfig) -> SummaryResult`
  - 内部流程：
    1. 解析/加载概率数据。
    2. 根据 `config.methods` 调用线性/MLE 重构器。
    3. 通过 `ResultRepository` 持久化记录。
    4. 汇总指标（纯度/迹/目标函数等）。
- `SummaryResult`：封装输出路径、计数、指标统计，便于 CLI 或其它层消费。
- 附属工具：输入校验、维度推断、日志钩子。

### 3.2 CLI 层 (`qtomography/cli/__init__.py` or `qtomography/cli/main.py`)

- 使用 `argparse`（或 `typer` 如后续引入）实现：
  - `qtomography reconstruct`：单文件批处理；参数与 `ReconstructionConfig` 对齐。
  - `qtomography summarize`：读取已生成的 `summary.csv` 进行简单统计（均值、方差、过滤）。
  - `qtomography info`：输出当前依赖/版本/路径（辅助调试）。
- 安装入口：在 `pyproject.toml` 的 `[project.scripts]` 增加 `qtomography = "qtomography.cli:main"`。

### 3.3 配置与扩展

- 支持从 YAML/JSON 读取配置（可选）。
- 预留 `--config path/to/config.yml`，由控制器解析覆盖命令行参数。
- 未来 GUI 可以直接调用 `ReconstructionController`，避免重复实现。

## 4. 实施步骤

| 阶段 | 内容 | 说明 |
| --- | --- | --- |
| S1 | `qtomography/app/controller.py` 原型 | 提取 `process_batch` 的核心逻辑，设计 config/result dataclass，添加基础单元测试 |
| S2 | 新 CLI 入口 | `qtomography/cli/main.py`，实现 `reconstruct` 子命令和 `pyproject` 脚本入口 |
| S3 | 扩展功能 | `summarize` / `info` 子命令，配置文件、日志格式等（可选） |
| S4 | 文档与示例 | 更新 README、docs/roadmap 状态，提供示例命令，确保 `process_batch` 迁移到 CLI（保留脚本作为兼容层） |

## 5. 测试计划

1. **单元测试**：
   - `tests/unit/test_controller.py`：config 校验、维度推断、异常路径。
   - `tests/unit/test_cli.py`：使用 `CliRunner` (typer) 或 `pytest` 的 `capsys` 捕获输出。
2. **集成测试**：
   - 结合小型概率数据运行 CLI（线性/MLE），验证 JSON 记录与 summary 结果。
   - 与现有 MATLAB 对齐数据协同使用。
3. **回归保障**：更新 CI（未来任务）时引入 CLI 调用。

## 6. 风险与缓解

| 风险 | 影响 | 缓解策略 |
| --- | --- | --- |
| 参数组合复杂 | CLI 使用体验差 | 分阶段实现，先覆盖核心参数，其余默认 |
| 与现有脚本重复 | 维护成本上升 | 将 `process_batch.py` 重构为调用控制器的薄封装 |
| 测试耗时 | CI 时间增长 | 小规模示例输入，必要时使用标记 `slow` |

## 7. 里程碑建议

- **10 月第 1 周**：完成 S1（控制器原型）；保留原脚本作为兼容层。
- **10 月第 2 周**：CLI `reconstruct` 子命令上线，更新 README/项目状态。
- **10 月第 3 周**：引入配置文件解析、`summarize` 子命令；讨论与 P3 阶段 (Bell 态、GUI) 的衔接。

---

**责任人**：待指定（暂由当前维护者推进）  
**依赖**：完成度高的线性/MLE 模块、ResultRepository、批处理示例数据。

