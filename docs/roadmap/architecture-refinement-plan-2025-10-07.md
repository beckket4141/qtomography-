# 架构分层调整与后续计划

> 基于近期对目录结构与职责划分的讨论，沉淀出的整体观察与行动建议。

## 现状辨析

- **接口层**：`qtomography/cli` 已稳定；GUI 尚未落地但定位在接口层没有争议。
- **应用层**：`ReconstructionController` 负责流程编排、配置聚合，角色清晰。
- **分析工具**：`qtomography/analysis`（Bell 分析等）目前与 `domain` 并列，但本质是“面向用例的后处理”，依赖领域对象却不属于核心模型。
- **领域层**：`qtomography/domain` 同时承载核心模型（`DensityMatrix`、`ProjectorSet`）与算法（Linear/MLE）。同时夹带了 `persistence` 子包，带来职责模糊。
- **基础设施能力**：结果持久化（`qtomography/infrastructure/persistence`）和可视化（`qtomography/infrastructure/visualization`）已迁入统一的 `infrastructure` 层，`qtomography/domain/persistence` 与 `qtomography/visualization` 仅保留兼容入口。

## 总体原则

1. **分层清晰**：接口 → 应用 → 分析 → 领域 → 基础设施，依赖关系只向下。
2. **领域最小化**：`domain` 保留“纯模型 + 算法”，避免混入持久化、可视化等配套设施。
3. **基础设施集中**：将共用的 IO、可视化、配置等能力统一纳入 `qtomography.infrastructure` 以便维护。
4. **文档同步**：教学/架构说明应反映最新的目录与职责，防止贡献者困惑。

## 调整建议

| 方向 | 内容 | 行动 |
|------|------|------|
| 分析层定位 | 明确 `qtomography.analysis` 属于分析层，依赖领域但不纳入 `domain` | - 在文档中补充该定位<br>- 考虑在分析包内继续分模块（如 bell、metrics 等） |
| 持久化迁移 | `qtomography/infrastructure/persistence` 已作为统一实现层，`qtomography/domain/persistence` 仅保留兼容入口 | - 已完成迁移；继续巡检引用和文档同步 |
| 可视化迁移 | `qtomography/infrastructure/visualization` 已承载全部实现，原有 `qtomography/visualization` 保留兼容导出 | - 同步清理示例与文档的导入路径 |
| 统一文档 | 教程/说明仍沿用旧结构描述 | - 更新 `docs/teach/controller详解.md`、`cli详解.md` 等文档<br>- 在 README 与路线图中同步新的分层示意 |
| 示例/配置 | 新增的配置功能需要示例支撑 | - 提供示例配置文件或段落说明（已部分完成）<br>- 在 CLI 教程中加入 `--config` / `--save-config` 说明 |

## 建议执行顺序

1. **文档对齐**：先调整教学/设计文档的层级描述，明确分析层、基础设施层职责，为后续代码迁移建立共识。
2. **引入基础设施骨架**：在 `qtomography/infrastructure` 建立目录结构与 `__init__` 导出，迁移 `persistence`、`visualization` 实现。
3. **更新调用方与测试**：逐步修正引用路径，并确保现有测试覆盖迁移后的模块。
4. **扩展分析层**：在 Bell 分析基础上整理未来指标/报表计划，保持分析模块对领域模型的只读依赖。

## 风险与兼容

- **引用路径变更**：迁移模块后需同步更新 `__all__`、CLI、脚本及测试 import，必要时提供过渡别名。
- **文档滞后**：若代码调整领先文档，易造成误解；建议每次结构变动都同步更新 `docs/teach/*` 与 README。
- **未来 GUI/配置**：随着基础设施集中，GUI 引入时可直接复用新位置的持久化/可视化服务，降低重复实现风险。

---

**最后更新**：2025-10-07  
**维护人**：Adapted by Codex (auto-generated summary)
**后续执行**：详见 docs/roadmap/stage4-architecture-consolidation-plan.md
