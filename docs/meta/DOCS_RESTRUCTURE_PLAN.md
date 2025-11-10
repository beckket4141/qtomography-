# 文档结构重组计划

> **创建日期**: 2025年11月  
> **状态**: 📋 待执行

---

## 📋 重组目标

根据优化方案，重组 `gui/`、`visualization/` 和 `teach/` 目录结构：

1. **`gui/` 和 `visualization/`**: 只保留实现原理和细节
2. **已实现文档**: 移至 `implemented/` 子目录
3. **未来计划**: 移至 `roadmap/` 子目录
4. **`teach/`**: 建立子分类

---

## 🔄 文件移动清单

### GUI 目录

#### 移动到 `implemented/gui/`
- ✅ `gui/gui_mvp_plan.md` → `implemented/gui/gui-mvp-implementation-status.md`

#### 移动到 `roadmap/gui/`
- ✅ `gui/design_v2.md` → `roadmap/gui/gui-design-v2-plan.md`
- ✅ `gui/新计划.md` → `roadmap/gui/gui-new-plan-2025.md`

#### 移动到 `archive/`
- ✅ `gui/disign.md` → `archive/gui-disign-deprecated.md`

#### 保留在 `gui/`（实现原理和细节）
- ✅ `gui/GUI配置保存机制实现说明.md`
- ✅ `gui/配置机制解耦分析与改动指南.md`

---

### Visualization 目录

#### 保留在 `visualization/`（实现原理和细节）
- ✅ `visualization/密度矩阵可视化方法总结.md`
- ✅ `visualization/图像预览交互功能实现详解.md`
- ✅ `visualization/图像预览显示技术分析.md`
- ✅ `visualization/MATLAB与Python_3D可视化对比分析.md`（分析文档）
- ✅ `visualization/plot_density_matrix_python_分析.md`（分析文档）

> **说明**: Visualization 目录中的文档主要是实现原理和分析，因此全部保留。

---

### Teach 目录

#### 建议的子分类结构

```
teach/
├── architecture/          # 架构分析
│   ├── 1.Python程序架构分析.md
│   ├── 1.GUI数据流.md
│   ├── 1.GUI数据流图表.md
│   └── ...
├── formulas/             # 公式教学
│   ├── density公式教学.md
│   ├── linear公式教学.md
│   ├── mle公式教学.md
│   ├── projector公式教学.md
│   └── 似然函数.md
├── concepts/             # 概念解析
│   ├── density的结构概述.md
│   ├── linear的结构概述.md
│   ├── mle的结构概述.md
│   ├── projector的结构概述.md
│   ├── projectors_结构分析与集成.md
│   └── ...
├── interview/            # 面试准备
│   ├── os_interview_answers_detailed.md
│   ├── os_interview_answers.md
│   ├── os_interview_checklist.md
│   ├── os_review_quick_sheet.md
│   ├── 面试准备.md
│   └── 1.面试准备-三种算法.md
└── workflows/            # 流程说明
    ├── 代码调用流程图.md
    ├── 数据流示意图.md
    ├── 启动计算的流程.md
    ├── 流程总结.md
    └── ...
```

---

## 📝 执行步骤

### 步骤1: 创建子目录

```bash
# 已创建
mkdir -p docs/implemented/gui
mkdir -p docs/roadmap/gui
mkdir -p docs/implemented/visualization
```

### 步骤2: 移动GUI文件

```bash
# 已实现文档
mv docs/gui/gui_mvp_plan.md docs/implemented/gui/gui-mvp-implementation-status.md

# 未来计划
mv docs/gui/design_v2.md docs/roadmap/gui/gui-design-v2-plan.md
mv docs/gui/新计划.md docs/roadmap/gui/gui-new-plan-2025.md

# 已过时
mv docs/gui/disign.md docs/archive/gui-disign-deprecated.md
```

### 步骤3: 创建teach子目录（可选）

```bash
mkdir -p docs/teach/architecture
mkdir -p docs/teach/formulas
mkdir -p docs/teach/concepts
mkdir -p docs/teach/interview
mkdir -p docs/teach/workflows
```

### 步骤4: 更新README

- ✅ 已更新 `gui/README.md`
- ✅ 已更新 `visualization/README.md`
- ⏳ 需要更新 `docs/README.md`
- ⏳ 需要更新 `teach/README.md`（如果创建子分类）

---

## ✅ 已完成

1. ✅ 创建子目录结构
2. ✅ 更新 `gui/README.md`
3. ✅ 更新 `visualization/README.md`
4. ✅ 创建重组计划文档

---

## ⏳ 待执行

1. ⏳ 实际移动文件（由于路径问题，需要手动执行或使用正确路径）
2. ⏳ 更新 `docs/README.md` 中的链接
3. ⏳ 创建 `teach/` 子分类（可选）
4. ⏳ 更新 `teach/README.md`

---

## 🔗 相关文档

- [DOCS_DIRECTORY_STRUCTURE_EVALUATION.md](DOCS_DIRECTORY_STRUCTURE_EVALUATION.md) - 目录结构评估
- [docs/README.md](../README.md) - 文档索引

---

**最后更新**: 2025年11月

