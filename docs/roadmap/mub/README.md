# MUB实现文档索引

本目录包含MUB（Mutually Unbiased Bases，相互无偏基）实现的完整文档。

## 文档列表

### 1. 使用指南
- **[MUB使用指南.md](MUB使用指南.md)** - 完整的使用文档
  - 快速开始
  - 支持的维度
  - 构造方法说明
  - 完整示例
  - 常见问题

### 2. 理论文档
- **[相互无偏基矢构造.markdown](相互无偏基矢构造.markdown)** - 理论背景
  - MUB的数学定义
  - 构造方法
  - 适用范围

### 3. 实现分析
- **[MUB_IMPLEMENTATION_ANALYSIS.md](MUB_IMPLEMENTATION_ANALYSIS.md)** - 详细实现分析
  - 代码结构分析
  - 数学公式验证
  - 与文献的一致性检查

- **[MUB_检查总结.md](MUB_检查总结.md)** - 检查总结
  - 科学验证结果
  - 主要发现
  - 最终评估

### 4. 维度支持
- **[MUB支持的维度分析.md](MUB支持的维度分析.md)** - 维度支持详细分析
  - 理论支持范围
  - 实际支持情况
  - 合理性评估

### 5. 测试报告
- **[MUB_运行测试报告.md](MUB_运行测试报告.md)** - 运行测试报告
  - 测试结果
  - 功能验证
  - 结论

### 6. 参考文献
- **[参考文献.md](参考文献.md)** - 完整参考文献
  - 标准文献引用
  - BibTeX格式
  - 与实现的对应关系

## 快速参考

### 支持的维度

**安装galois库后（推荐）**：
- ✅ 所有素数幂维度：2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 25, 27, 32...

**未安装galois库**：
- ✅ 所有素数：2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31...
- ✅ d=4, d=9, d=16
- ❌ 不支持：d=8, 25, 27, 32等其他素数幂

### 安装galois库

```bash
pip install galois
```

### 基本使用

```python
from qtomography.domain.measurement.mub import build_mub_projectors

# 创建MUB
design = build_mub_projectors(dimension=5)

# 访问投影算符
projectors = design.projectors  # shape: (d², d, d) for compact
groups = design.groups          # shape: (d²,)
```

## 相关代码

- 实现文件：`python/qtomography/domain/measurement/mub.py`
- 集成接口：`python/qtomography/domain/projectors.py`

## 更新历史

- **2025年1月**：
  - 修复galois库API兼容性问题
  - 实现特征2的完整支持
  - 完善文档和使用指南

