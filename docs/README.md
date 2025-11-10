# Documentation Index

> 文档按主题分成 implemented/、roadmap/、teach/、meta/、archive/ 等子目录，便于快速定位当前实现、路线规划、教学材料与历史资料。

**最后更新**: 2025年11月

---

## 📚 目录结构

```
docs/
├── README.md                    # 本文档（文档索引）
├── implemented/                 # 已实现功能文档 (15份) - 当前有效的实现文档
├── roadmap/                     # 路线规划文档 (20+份) - 未来计划和设计提案
├── teach/                       # 教学文档 (49+份) - 学习、理解、教学材料
├── meta/                        # 元文档（文档管理）(9份) - 文档管理相关
├── archive/                     # 历史归档 (5份) - 已过时的历史文档
├── guides/                      # 使用指南 (4份) - 用户和开发者指南
├── gui/                         # GUI实现原理和细节 (2份) - 仅保留实现原理和细节
├── visualization/               # 可视化实现原理和细节 (5份) - 仅保留实现原理和细节
├── implemented/
│   ├── gui/                     # GUI已实现功能文档
│   └── visualization/           # 可视化已实现功能文档
└── roadmap/
    └── gui/                     # GUI未来计划文档
└── 论文/                        # 论文资料 (1份) - 相关论文资料
```

> **目录结构评估**: 详见 [DOCS_DIRECTORY_STRUCTURE_EVALUATION.md](meta/DOCS_DIRECTORY_STRUCTURE_EVALUATION.md)

---

## 已实现 / Implemented

> **说明**: 本目录包含**当前有效的实现文档**，描述已实现功能的现状和使用方法。如果文档完全过时，会移至 `archive/` 目录。详见 [ARCHIVE_VS_IMPLEMENTED_ANALYSIS.md](meta/ARCHIVE_VS_IMPLEMENTED_ANALYSIS.md)

| 文档 | 内容摘要 | 状态 |
| --- | --- | --- |
| [system-completeness-analysis-2025-10-07](implemented/system-completeness-analysis-2025-10-07.md) | 系统完成度与合理性分析 ⭐ **最新主文档** | ✅ 最新 |
| [repository-comprehensive-analysis-2025-10-07](implemented/repository-comprehensive-analysis-2025-10-07.md) | 仓库全面分析（架构、科学性、测试） | ✅ 有效 |
| [project-status-2025-10-07](implemented/project-status-2025-10-07.md) | 项目现状评估报告 ⚠️ **部分过时** | ⚠️ 已标注 |
| [ARCHITECTURE_REFINEMENT_ANALYSIS](implemented/ARCHITECTURE_REFINEMENT_ANALYSIS.md) | 架构调整计划深度分析 | ✅ 有效 |
| [ADD_MLE_RECONSTRUCTION_GUIDE](implemented/ADD_MLE_RECONSTRUCTION_GUIDE.md) | MLE重构算法集成指南 | ✅ 有效 |
| [density-module-overview](implemented/density-module-overview.md) | DensityMatrix 模块的现状、数值策略与维护建议 | ✅ 有效 |
| [linear-reconstruction-guide](implemented/linear-reconstruction-guide.md) | LinearReconstructor 线性重构器实现指南 | ✅ 有效 |
| [mle-reconstruction-guide](implemented/mle-reconstruction-guide.md) | MLEReconstructor MLE重构器实现总结 | ✅ 有效 |
| [cli-usage-guide](implemented/cli-usage-guide.md) | CLI命令行工具使用指南 | ✅ 有效 |
| [visualization-3d-enhancement](implemented/visualization-3d-enhancement.md) | 3D可视化功能增强（实部虚部3D图） | ✅ 有效 |
| [matlab-gui-feature-comparison-v2](implemented/matlab-gui-feature-comparison-v2.md) | MATLAB与Python功能对比（v2.0） | ✅ 有效 |

---

## 路线规划 / Roadmap

| 文档 | 内容摘要 | 状态 |
| --- | --- | --- |
| [master-plan](roadmap/master-plan.md) | MATLAB → Python 全量迁移蓝图与阶段规划 | ✅ 有效 |
| [2025-09-24-roadmap-status](roadmap/2025-09-24-roadmap-status.md) | 路线图状态（截至2025-09-24） ⚠️ **历史快照** | ⚠️ 已标注 |
| [stage3-metrics-expansion-plan](roadmap/stage3-metrics-expansion-plan.md) | Stage 3 指标扩展计划 | ✅ 已完成 |
| [stage4-architecture-consolidation-plan](roadmap/stage4-architecture-consolidation-plan.md) | Stage 4 架构整合计划 | 🔄 规划中 |
| [NEXT_STEPS_RECOMMENDATIONS](roadmap/NEXT_STEPS_RECOMMENDATIONS.md) | 下一步行动建议 | ✅ 有效 |
| [PRIORITY_PLAN_ANALYSIS](roadmap/PRIORITY_PLAN_ANALYSIS.md) | 优先级规划深度分析 | ✅ 有效 |
| [base-reconstructor-proposal](roadmap/base-reconstructor-proposal.md) | BaseReconstructor 抽象基类设计建议 | ✅ 有效 |
| [linear-reconstructor-design](roadmap/linear-reconstructor-design.md) | LinearReconstructor 设计文档 | ✅ 有效 |
| [mle-reconstructor-design](roadmap/mle-reconstructor-design.md) | MLEReconstructor 设计文档 | ✅ 有效 |
| [projector-set-design](roadmap/projector-set-design.md) | ProjectorSet 设计文档 | ✅ 有效 |
| [bell-analysis-design](roadmap/bell-analysis-design.md) | Bell态分析设计文档 | ✅ 有效 |
| [result-visualization-design](roadmap/result-visualization-design.md) | 结果持久化与可视化设计 | ✅ 有效 |

### 子目录

- **mub/** - MUB（相互无偏基）相关文档
- **rrr算法/** - RρR算法相关文档
- **谱分解/** - 谱分解相关文档

---

## 教学文档 / Teaching

### 🏗️ 架构设计
| 文档 | 内容摘要 |
| --- | --- |
| [__init__文件详解](teach/__init__文件详解.md) | Python 包管理核心知识（包、模块、导入） ⭐ 基础必读 |
| [cli详解](teach/cli详解.md) | CLI 接口层设计、argparse 实战与分层架构 ⭐ 新增 |
| [controller详解](teach/controller详解.md) | 应用层编排、批处理流程与设计模式 ⭐ 新增 |
| [1.Python程序架构分析](teach/1.Python程序架构分析.md) | Python程序架构深度分析 |

### 📐 领域层模块
| 文档 | 内容摘要 |
| --- | --- |
| [density公式教学](teach/density公式教学.md) | 密度矩阵物理约束的数学推导与实现 |
| [density的结构概述](teach/density的结构概述.md) | DensityMatrix 类的架构与设计思路 |
| [projector公式教学](teach/projector公式教学.md) | 投影算符与测量基的数学原理 |
| [projector的结构概述](teach/projector的结构概述.md) | ProjectorSet 类的架构与缓存机制 |
| [linear公式教学](teach/linear公式教学.md) | 线性重构的数学推导与物理意义 |
| [linear的结构概述](teach/linear的结构概述.md) | LinearReconstructor 类的结构与求解策略 |
| [mle公式教学](teach/mle公式教学.md) | MLE 重构的数学推导与统计学基础 |
| [mle的结构概述](teach/mle的结构概述.md) | MLEReconstructor 类的架构与优化策略 |

### 📖 面试准备
| 文档 | 内容摘要 |
| --- | --- |
| [os_interview_answers_detailed.md](teach/os_interview_answers_detailed.md) | 操作系统面试详解（基于项目实战） |
| [os_interview_answers.md](teach/os_interview_answers.md) | 操作系统面试答案摘要 |
| [os_interview_checklist.md](teach/os_interview_checklist.md) | 操作系统面试检查清单 |
| [os_review_quick_sheet.md](teach/os_review_quick_sheet.md) | 操作系统快速复习表 |
| [面试准备.md](teach/面试准备.md) | 量子层析项目面试准备 |

---

## 历史归档 / Archive

> **说明**: 本目录包含**已过时的历史文档**，仅供回顾和背景了解。这些文档描述的问题已解决，或被新版本替代。当前有效的实现文档在 `implemented/` 目录。详见 [ARCHIVE_VS_IMPLEMENTED_ANALYSIS.md](meta/ARCHIVE_VS_IMPLEMENTED_ANALYSIS.md)

| 文档 | 内容摘要 |
| --- | --- |
| [density-temp-design-notes-2024](archive/density-temp-design-notes-2024.md) | 初期从 MATLAB 移植 density.py 的草稿和思路 |
| [density-initial-issues-analysis](archive/density-initial-issues-analysis.md) | 2025-09 首轮问题分析，现已被新版实现覆盖 |
| [density-step2-issues-and-fixes](archive/density-step2-issues-and-fixes.md) | 第二批问题清单与修复背景，供回顾使用 |
| [matlab-gui-feature-comparison-v1.0-deprecated](archive/matlab-gui-feature-comparison-v1.0-deprecated.md) | MATLAB功能对比v1.0（已过时，包含错误） |
| [project-status-corrections-2025-10-07](archive/project-status-corrections-2025-10-07.md) | 项目状态修正补丁（已整合到新文档） |

---

## 使用指南 / Guides

| 文档 | 内容摘要 |
| --- | --- |
| [README](guides/README.md) | 使用指南索引 |
| [gitignore-guide](guides/gitignore-guide.md) | .gitignore 规则及项目约定 |
| [installation-guide](guides/installation-guide.md) | 安装指南（系统要求、安装步骤、验证） |
| [development-guide](guides/development-guide.md) | 开发指南（环境设置、代码规范、测试） |

---

## GUI 相关文档

> **说明**: `gui/` 目录现在**只保留实现原理和细节**文档。已实现功能文档在 `implemented/gui/`，未来计划在 `roadmap/gui/`。

### 实现原理和细节（`gui/`）

| 文档 | 内容摘要 | 状态 |
| --- | --- | --- |
| [README](gui/README.md) | GUI文档索引 | ✅ |
| [GUI配置保存机制实现说明](gui/GUI配置保存机制实现说明.md) | 配置保存机制的详细实现说明 | ✅ 实现原理 |
| [配置机制解耦分析与改动指南](gui/配置机制解耦分析与改动指南.md) | 配置机制解耦分析和改动指南 | ✅ 实现细节 |

### 已实现功能（`implemented/gui/`）

| 文档 | 内容摘要 | 状态 |
| --- | --- | --- |
| [gui-mvp-implementation-status](implemented/gui/gui-mvp-implementation-status.md) | MVP实现状态 | ✅ 已实现 |

### 未来计划（`roadmap/gui/`）

| 文档 | 内容摘要 | 状态 |
| --- | --- | --- |
| [gui-design-v2-plan](roadmap/gui/gui-design-v2-plan.md) | GUI v2.0 完整设计方案 | 🔄 规划中 |
| [gui-new-plan-2025](roadmap/gui/gui-new-plan-2025.md) | 2025年新计划（Dock架构等） | 🔄 规划中 |

---

## 可视化相关文档

> **说明**: `visualization/` 目录现在**只保留实现原理和细节**文档。已实现功能文档在 `implemented/visualization/`。

### 实现原理和细节（`visualization/`）

| 文档 | 内容摘要 | 状态 |
| --- | --- | --- |
| [README](visualization/README.md) | 可视化文档索引 | ✅ |
| [密度矩阵可视化方法总结](visualization/密度矩阵可视化方法总结.md) | 所有可视化方法总结和使用指南 | ✅ 实现原理 |
| [图像预览交互功能实现详解](visualization/图像预览交互功能实现详解.md) | 图像预览交互功能实现细节 | ✅ 实现细节 |
| [图像预览显示技术分析](visualization/图像预览显示技术分析.md) | 图像预览显示技术分析 | ✅ 实现细节 |
| [MATLAB与Python_3D可视化对比分析](visualization/MATLAB与Python_3D可视化对比分析.md) | MATLAB与Python 3D可视化对比和改进建议 | 📊 分析文档 |
| [plot_density_matrix_python_分析](visualization/plot_density_matrix_python_分析.md) | 绘制方式分析和改进建议 | 📊 分析文档 |

### 已实现功能（`implemented/visualization/`）

| 文档 | 内容摘要 | 状态 |
| --- | --- | --- |
| [visualization-3d-enhancement](implemented/visualization-3d-enhancement.md) | 3D可视化功能增强 | ✅ 已实现 |

---

## 元文档 / Meta

| 文档 | 内容摘要 |
| --- | --- |
| [DOCUMENT_ORGANIZATION_SUMMARY.md](meta/DOCUMENT_ORGANIZATION_SUMMARY.md) | 文档整理总结（2025年11月） |
| [DOCUMENT_REORGANIZATION_2025_11.md](meta/DOCUMENT_REORGANIZATION_2025_11.md) | docs目录文档重组报告（2025年11月） |
| [DOCS_CLEANUP_2025_11.md](meta/DOCS_CLEANUP_2025_11.md) | docs目录整理报告（2025年11月） |
| [ARCHIVE_VS_IMPLEMENTED_ANALYSIS.md](meta/ARCHIVE_VS_IMPLEMENTED_ANALYSIS.md) | Archive vs Implemented 目录分析 ⭐ **新增** |
| [DOCS_DIRECTORY_STRUCTURE_EVALUATION.md](meta/DOCS_DIRECTORY_STRUCTURE_EVALUATION.md) | Docs 目录结构评估报告 ⭐ **新增** |
| [DOCS_RESTRUCTURE_PLAN.md](meta/DOCS_RESTRUCTURE_PLAN.md) | 文档结构重组计划 ⭐ **新增** |
| [DOCUMENT_CLEANUP_SUMMARY.md](meta/DOCUMENT_CLEANUP_SUMMARY.md) | 文档清理总结（2025年10月） |
| [DOCS_STRUCTURE_ANALYSIS.md](meta/DOCS_STRUCTURE_ANALYSIS.md) | 文档结构分析（2025年10月） |
| [DOCS_STRUCTURE_FINAL.md](meta/DOCS_STRUCTURE_FINAL.md) | 文档结构优化完成报告（2025年10月） |
| [PROJECT_STRUCTURE_CLEANUP.md](meta/PROJECT_STRUCTURE_CLEANUP.md) | 项目结构清理报告（2025年10月） |

---

## 快速导航

### 🚀 开始使用
- **新手入门**：先看 [master-plan](roadmap/master-plan.md) 了解整体架构
- **理解分层**：阅读 [cli详解](teach/cli详解.md) → [controller详解](teach/controller详解.md) 理解接口层和应用层
- **理解核心**：阅读 [density公式教学](teach/density公式教学.md) 理解物理约束
- **开始开发**：参考 [2025-09-24-roadmap-status](roadmap/2025-09-24-roadmap-status.md) 查看当前进度

### 📚 深入学习

#### 🏗️ 架构层面（推荐学习路径）
1. **Python 基础**: [__init__文件详解](teach/__init__文件详解.md) - 理解包管理
2. **接口层**: [cli详解](teach/cli详解.md) - 理解命令行接口设计
3. **应用层**: [controller详解](teach/controller详解.md) - 理解流程编排
4. **领域层**: 各模块的结构概述和公式教学

#### 📐 领域层模块
- **密度矩阵**: [density-module-overview](implemented/density-module-overview.md)
- **线性重构**: [linear-reconstruction-guide](implemented/linear-reconstruction-guide.md)
- **MLE重构**: [mle-reconstruction-guide](implemented/mle-reconstruction-guide.md)
- **可视化**: [visualization-3d-enhancement](implemented/visualization-3d-enhancement.md)

### 🔧 参与开发
- 查看规划：[roadmap/](roadmap/) 目录下的所有文档
- 设计提案：[base-reconstructor-proposal](roadmap/base-reconstructor-proposal.md)
- 代码规范：[gitignore-guide](guides/gitignore-guide.md)

---

> **最后更新**: 2025年11月  
> **文档整理**: 参见 [meta/DOCUMENT_REORGANIZATION_2025_11.md](meta/DOCUMENT_REORGANIZATION_2025_11.md)
