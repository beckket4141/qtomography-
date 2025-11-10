# Density Module Overview

_Last updated: 2025-10-06_

## Purpose
- 对应 python/qtomography/domain/density.py，核心职责是封装密度矩阵并保证其满足 Hermitian、正半定、迹为 1 的物理约束。
- 提供与 MATLAB 工作流一致的便捷函数 make_physical、compute_fidelity 以及多种工厂方法，便于渐进式迁移。

## 已实现能力
- **输入守卫**：构造函数在矩阵数组化前拦截字符串、标量等非法输入，并统一抛出 TypeError（参见 python/qtomography/domain/density.py:55）。
- **物理化投影**：初始化与 ensure_physical() 共享 _make_physical_matrix，执行 Hermitian 化、谱裁剪、归一化，并在迹退化时回退到最大混合态（density.py:155-198）。
- **数值稳健接口**：eigenvalues、idelity、matrix_square_root 均使用 Hermitian 专用 eigh 并按容差裁剪微小负值，避免保真度与谱分析出现 
an 或负数（density.py:119-177, density.py:205-244）。
- **调试友好特性**：提供实部、虚部、振幅、相位访问器，__eq__ 通过 
p.allclose 支持带容差比较，matrix 属性返回副本以保护内部状态。

## 与历史文档的关系
- 《density-temp-design-notes-2024》与《density-initial-issues-analysis》记录了初期移植计划与存在的问题，目前功能均已纳入本文档描述的实现。
- 《density-step2-issues-and-fixes》中的 pytest 失败用例已通过输入守卫与特征值裁剪修复，可作为故障排查的背景资料。

## 维护与后续建议
1. **性能优化**：在高维或批量场景中，可考虑缓存 eigh 结果或为 matrix 属性提供只读视图以减少复制开销。
2. **快速检测**：若后续性能成为瓶颈，可在 _make_physical_matrix 调用前先进行轻量物理性检查，仅在失败时执行完整投影。
3. **日志与诊断**：为 ensure_physical() 添加可选的调试信息（裁剪量、归一化因子），便于定位数值不稳定的输入。
4. **接口拓展**：根据路线图继续补齐 ProjectorSet、LinearReconstructor 等模块后，可在此文档补充与它们的接口契约。
