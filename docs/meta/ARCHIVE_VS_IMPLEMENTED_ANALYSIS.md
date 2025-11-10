# Archive vs Implemented 目录分析

> **创建日期**: 2025年11月  
> **目的**: 分析 `archive/` 和 `implemented/` 目录的语义差异和使用建议

---

## 📋 当前定义

### `archive/` 目录
**含义**: 历史归档，已过时的文档

**特点**:
- ✅ 文档内容已被新版本替代
- ✅ 问题已解决，不再需要参考
- ✅ 仅供历史回顾和背景了解
- ✅ 文档中明确标注"已归档"状态

**示例**:
- `density-initial-issues-analysis.md` - 初期问题分析，已被新版实现覆盖
- `matlab-gui-feature-comparison-v1.0-deprecated.md` - v1.0版本，已过时
- `project-status-corrections-2025-10-07.md` - 修正补丁，已整合到新文档

### `implemented/` 目录
**含义**: 已实现功能的当前有效文档

**特点**:
- ✅ 描述当前实现状态
- ✅ 作为开发和使用参考
- ✅ 文档内容仍然有效
- ⚠️ 但可能随时间过时（需要状态标记）

**示例**:
- `density-module-overview.md` - 当前Density模块实现说明
- `linear-reconstruction-guide.md` - Linear重构器使用指南
- `cli-usage-guide.md` - CLI工具使用指南

---

## 🔍 语义重叠分析

### 重叠点

1. **都包含"已实现"的内容**
   - `archive/` 中的文档描述的是"曾经实现"或"已解决的问题"
   - `implemented/` 中的文档描述的是"当前实现"

2. **时间维度模糊**
   - `implemented/` 中的文档也可能随时间过时
   - 例如：`project-status-2025-10-07.md` 标注了"部分过时"

3. **分类标准不统一**
   - 有些文档可能既属于"历史"又属于"已实现"
   - 需要人工判断何时从 `implemented/` 移到 `archive/`

---

## 💡 改进建议

### 方案1：保持现状，加强状态标记（推荐）

**优点**:
- 保持目录结构清晰
- 通过文档内的状态标记区分

**实施**:
- `archive/` 中的文档统一标注：`> **状态**: 已归档`
- `implemented/` 中的文档标注：`> **状态**: ✅ 当前有效` 或 `⚠️ 部分过时`
- 在 README 中明确说明两个目录的区别

### 方案2：合并目录，使用状态标记

**优点**:
- 避免目录分类的模糊性
- 所有实现文档在一个目录，通过状态区分

**实施**:
- 将 `archive/` 中的文档移到 `implemented/`
- 在文档开头添加状态标记
- 在 README 中按状态筛选显示

**缺点**:
- 需要移动文件
- 可能让 `implemented/` 目录变得庞大

### 方案3：重新定义目录用途

**新定义**:
- `archive/` → `deprecated/`（已废弃）
- `implemented/` → `current/`（当前实现）

**优点**:
- 语义更清晰
- `deprecated` 明确表示"不再使用"

**缺点**:
- 需要重命名目录和更新所有链接

---

## 🎯 推荐方案

**推荐使用方案1**：保持现状，加强状态标记

### 理由

1. **语义差异足够清晰**
   - `archive/` = 历史/过时/不再使用
   - `implemented/` = 当前/有效/正在使用

2. **符合常见实践**
   - 大多数项目都有 `archive/` 或 `deprecated/` 目录
   - `implemented/` 作为功能文档目录也很常见

3. **维护成本低**
   - 不需要移动文件
   - 只需要在文档中添加状态标记
   - 在 README 中明确说明即可

### 实施步骤

1. ✅ 在 `archive/` 中的文档统一添加状态标记
2. ✅ 在 `implemented/` 中的文档添加状态标记（当前有效/部分过时）
3. ✅ 在 README 中明确说明两个目录的区别
4. ✅ 建立文档迁移规则：当 `implemented/` 中的文档完全过时时，移到 `archive/`

---

## 📝 文档迁移规则

### 何时将文档从 `implemented/` 移到 `archive/`？

**条件**:
1. 文档描述的功能已被新版本完全替代
2. 文档中的信息已不再准确
3. 有更新的文档替代了它的作用
4. 文档仅供历史回顾，不再作为参考

**示例**:
- `project-status-2025-10-07.md` 如果完全过时，应移到 `archive/`
- `matlab-gui-feature-comparison-v2.md` 如果被 v3 替代，v2 应移到 `archive/`

---

## 🔗 相关文档

- [docs/README.md](../README.md) - 文档索引
- [DOCUMENT_REORGANIZATION_2025_11.md](DOCUMENT_REORGANIZATION_2025_11.md) - 文档重组报告

---

**最后更新**: 2025年11月

