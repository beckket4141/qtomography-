# Roadmap Status · 截至 2025-09-24

---

⚠️ **文档状态**: **历史快照**（截至2025-09-24，当前为2025年11月）

> **注意**: 本文档为历史快照，记录了2025年9月24日的项目状态。当前项目已完成Stage 3，正在规划Stage 4。

**当前最新状态** (2025年11月):
- ✅ P2-2 应用层 CLI/控制器 → **已完成**
- ✅ P3-1 Bell 态分析 → **已完成**
- ✅ P3-2 工程化基础设施 → **已完成**
- ✅ Stage 3 指标扩展与报告增强 → **已完成** (2025-10-07)
- 🔄 Stage 4 架构整合 → **规划中**

**最新完成度评估**: 参见 `docs/implemented/system-completeness-analysis-2025-10-07.md`  
**Stage 3 完成报告**: 参见 `STAGE3_COMPLETION_REPORT.md`  
**项目最终状态**: 参见 `FINAL_STATUS_REPORT.md`

---

> 参照 `docs/roadmap/master-plan.md` 评估阶段性目标，状态分为 **已完成 / 进行中 / 规划中**。

## 汇总表
| ID  | 阶段目标                     | 当前状态 | 最新进展概述 |
| --- | ---------------------------- | -------- | ------------ |
| P0-1 | 基础算法与测量算符稳态      | ✅ 已完成 | `ProjectorSet`、`LinearReconstructor` 经单元/集成测试验证，数值稳定性问题关闭 |
| P0-2 | 小维度 MATLAB 对齐          | ✅ 已完成 | 4×4、16×16 Excel/Matlab 数据通过 `tests/integration/test_linear_reconstruction_excel.py` 覆盖 |
| P0-3 | DensityMatrix 修复          | ✅ 已完成 | 物理化流程、特征值裁剪与错误处理全部合并，覆盖率>90% |
| P1-1 | 数据持久化与可视化工具      | ✅ 已完成 | `ResultRepository`、`ReconstructionVisualizer` 上线，新增 3D 实/虚柱状图 |
| P1-2 | 指标比较与报告               | 🔄 进行中 | 批处理 summary.csv 已产出基础指标，正推进自动化指标对比 |
| P2-1 | MLE 重构模块                 | ✅ 已完成 | `MLEReconstructor` 与线性重构共存，支持正则/初值；集成测试通过 |
| P2-2 | 应用层 CLI / 控制器          | ✅ 已完成 | `ReconstructionController` + `qtomography` CLI（含 `--bell` / `bell-analyze`）投产，批处理脚本改为薄封装 |
| P3-1 | Bell 态 / 高级重构迁移       | ✅ 已完成 | `qtomography.analysis.bell` 模块与 CLI `bell-analyze` 子命令正式可用 |
| P3-2 | 工程化基础设施               | 🔄 进行中 | `pyproject.toml` / `requirements.txt` 已补齐依赖，将补充 `qtomography.infrastructure` / `qtomography.utils` 骨架并规划 CI |
| P4   | 产品化增强                   | ⏳ 规划中 | 等待上一层级的 CLI、GUI、Bell 态完成后推进 |

## 关键进展
- **批处理工作流**：`ReconstructionController` 搭配 `scripts/process_batch.py` 打通多算法批处理，自动落地 JSON 记录与 `summary.csv`。
- **CLI 与 Bell 分析**：`qtomography` CLI 支持 `reconstruct`/`summarize`/`bell-analyze`，内置 Bell 指标统计与导出。
- **依赖与文档**：`requirements.txt`、`pyproject.toml`、`docs/implemented/*` 已同步更新，帮助快速搭建开发环境。

## 阶段详述
### P0 系列 · 基础稳定
- Linear/MLE 重构及 ProjectorSet 保持绿灯，数值与测试覆盖稳定。
- 小维度验证脚本与集成测试持续可用，作为回归基线。

### P1 系列 · 结果与展示
- ResultRepository 与可视化模块投入使用；新增 3D 实/虚柱状图及批处理汇总。
- 指标对比（P1-2）计划结合批处理输出扩展纯度/chi²/Fidelity 等统计。

### P2 系列 · 算法/流程扩展
- MLE 模块验收完成。
- 应用层控制器与 CLI 已落地，后续聚焦指标自动化与模块协同。

### P3 / P4 · 中长期任务
- Bell 态分析已上线；GUI 与工程化设施转入排期，重点准备 CI、配置以及通用工具。

## 下一步行动
**短期（本周）**
1. 扩展 `summary.csv` 与 Bell 统计选项，补发自动指标示例及测试用例。
2. 在 `qtomography.infrastructure` / `qtomography.utils` 中补充 README 与骨架注释，明确计划职责。

**中期（本月）**
1. 搭建 CI 流程（lint + pytest + 覆盖率），集成 pre-commit。
2. 完成指标比较/报告自动化（P1-2），输出初版统计报表。
3. 启动 GUI 原型设计，梵理应用层与可视化的交互需求。

## 最近更新记录
- **2025-10-07**：ReconstructionController、CLI 与 Bell 分析功能合并完成，并同步更新 README / Roadmap。
- **2025-10-06**：MLE 模块合并，3D 可视化增强。

