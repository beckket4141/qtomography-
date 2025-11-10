# 在本仓库中新增“标准 MLE”重构算法的完整集成指南

> 适用范围：当前仓库已有“线性重构 linear”和“WLS（占位用于 MLE）”，需要补齐“标准 MLE（Maximum Likelihood Estimation）”的正式实现与端到端集成（CLI/GUI/批处理/记录持久化）。本文档结合现有代码结构与约定，给出从实现到联动的完整步骤与建议。


## 1. 背景与现状

- 已有算法与结构
  - 线性重构：`python/qtomography/domain/reconstruction/linear.py`
  - WLS：`python/qtomography/domain/reconstruction/wls.py`
  - MLE 文件：`python/qtomography/domain/reconstruction/mle.py` 当前为“弃用提示 + 指向 WLS 的别名包装”，并非标准 MLE。
- 业务端入口
  - 控制器：`python/qtomography/app/controller.py`（批量执行、记录落库、汇总 CSV 等）
  - CLI：`python/qtomography/cli/main.py`（已暴露 `--mle-regularization`、`--mle-max-iterations` 等参数）
  - 配置读写：`python/qtomography/app/config_io.py`（JSON 配置含 `mle_*` 字段）
  - GUI：`python/qtomography/gui/panels/config_panel.py`（当前为 Linear + WLS 开关，需要补充 MLE 开关/参数）

结论：仓库“接口层”已经以 MLE 为名完成了参数/配置/文案，但“算法层”尚未提供标准 MLE 的独立实现。我们需要在 `domain/reconstruction/mle.py` 内提供真正的 MLE，并在 Controller/GUI 等处接入 method="mle" 的完整路径。


## 2. 标准 MLE 的目标与接口一致性

- 目标：给定测量投影 {Π_a} 与观测概率（或频率）p_a，估计密度矩阵 ρ，使其满足
  - ρ ⪰ 0（半正定），Tr(ρ) = 1；
  - 最大化对数似然 L(ρ) = Σ_a f(p_a, tr(Π_a ρ))，常用多项式/泊松模型；
  - 数值稳定、可收敛、对初值鲁棒。
- 与现有接口保持一致：
  - 构造器参数风格与 `WLSReconstructor`、`LinearReconstructor` 对齐：`dimension`、`tolerance`、`cache_projectors`、`density_enforce/strict/warn` 等。
  - 公开方法：
    - `reconstruct(probabilities) -> DensityMatrix`
    - `reconstruct_with_details(probabilities, initial_density=None) -> MLEReconstructionResult`
  - 结果对象字段：包含 `density`、`rho_matrix_raw`、`normalized_probabilities`、`expected_probabilities`、`log_likelihood`、`success`、`n_iterations` 等（与 WLS 的 `objective`/`success` 字段风格对应）。


## 3. 目录结构与依赖

- 核心文件：`python/qtomography/domain/reconstruction/mle.py`
- 依赖对象：
  - `qtomography.domain.density.DensityMatrix`
  - `qtomography.domain.projectors.ProjectorSet`
- 计算工具：`numpy` 必选；如采用 L-BFGS-B 等通用优化器，可使用 `scipy.optimize`；如采用 RρR 迭代（Hradil/Řeháček 等），无需外部优化器。


## 4. 实现方案建议（两种常用实现路径）

- 方案 A：RρR 迭代（推荐起步）
  - 定义 R(ρ) = Σ_a [ p_a / max(tr(Π_a ρ), ε) ] Π_a，ε ~ 1e-12 防止除零；
  - 迭代：ρ_{k+1} = N · R(ρ_k) ρ_k R(ρ_k)，其中 N 做迹归一化，使 Tr(ρ_{k+1})=1；
  - 收敛性：监控对数似然增益 ΔL < tol 或 ||ρ_{k+1} - ρ_k||_F < tol；
  - 优点：实现简单、满足 PSD 与迹约束；
  - 注意：数值下溢/投影归一的稳定化处理。
- 方案 B：参数化 + 一般优化器
  - 用 Cholesky 参数化：ρ = T T† / Tr(T T†)，将 PSD + 迹约束内化；
  - 以负对数似然为目标，使用 L-BFGS-B/CG 最小化；
  - 可直接复用 WLS 中的 `encode_density_to_params`/`decode_params_to_density` 模板，替换目标函数为 NLL；
  - 优点：易与现有 WLS 结构统一；
  - 注意：步长/正则/初值对收敛速度影响较大。

初次集成建议采用“方案 A（RρR）”，代码更短、收敛稳定；后续可在同一文件中提供备选优化器实现，便于切换对比。


## 5. 代码落地步骤（逐项）

1) 在 `python/qtomography/domain/reconstruction/mle.py` 中实现标准 MLE

- 替换当前“弃用包装”为完整实现：
  - 定义 `@dataclass class MLEReconstructionResult`，字段建议：
    - `density: DensityMatrix`
    - `rho_matrix_raw: np.ndarray`
    - `normalized_probabilities: np.ndarray`
    - `expected_probabilities: np.ndarray`
    - `log_likelihood: float`
    - `success: bool`
    - `n_iterations: int`
  - 定义 `class MLEReconstructor`，关键成员：
    - `__init__(dimension, *, tolerance=1e-10, max_iterations=2000, cache_projectors=True, density_enforce="within_tol", density_strict=False, density_warn=True)`
    - `reconstruct(probabilities)` 和 `reconstruct_with_details(probabilities, initial_density=None)`
    - `_normalize_probabilities(probabilities)`：与 linear/wls 同一归一规则（本仓库约定：长度 n^2，按前 n 项和归一）。
    - `_expected_probabilities(rho, projectors)`：`np.real(np.einsum('aij,ji->a', projectors, rho, optimize=True))`
    - RρR 主循环或 NLL 目标函数 + 解码编码工具（若走优化器方案）。

- 伪代码（RρR）：
  ```python
  def reconstruct_with_details(self, probs, initial_density=None):
      p = self._normalize_probabilities(probs)
      P = self.projector_set.projectors  # [A, n, n]

      rho = self._prepare_initial_density(p, initial_density)  # 线性解或 I/n
      last_L = -np.inf
      for it in range(self.max_iterations):
          exp_p = np.clip(self._expected_probabilities(rho, P), 1e-12, None)
          R = np.einsum('a, aij -> ij', p / exp_p, P, optimize=True)
          rho_next = R @ rho @ R
          rho_next /= np.trace(rho_next)

          L = np.sum(p * np.log(exp_p))  # 多项式模型常用写法
          if np.isfinite(L) and (L - last_L) < self.tolerance:
              break
          if np.linalg.norm(rho_next - rho, ord='fro') < self.tolerance:
              break
          rho, last_L = rho_next, L

      density = DensityMatrix(
          rho, tolerance=self.tolerance,
          enforce=self.density_enforce, strict=self.density_strict, warn=self.density_warn
      )
      return MLEReconstructionResult(
          density=density,
          rho_matrix_raw=rho,
          normalized_probabilities=p,
          expected_probabilities=self._expected_probabilities(rho, P),
          log_likelihood=float(L),
          success=True,  # 可结合收敛条件设置
          n_iterations=it + 1,
      )
  ```

2) 在控制器接入 method="mle"

- 修改允许列表：将 `python/qtomography/app/controller.py` 中 `_ALLOWED_METHODS = {"linear", "wls"}` 改为包含 `"mle"`（并保留 `"wls"` 用于向后兼容或比较）。
- 在构造阶段根据 `config.methods` 实例化 `MLEReconstructor`：
  - 维度、tolerance、cache_projectors 等与线性/WLS 对齐；
  - 初值：优先使用线性重构结果（若前一步已执行 linear），否则使用 `I/n`。
- 执行阶段：
  - 调用 `mle.reconstruct_with_details(...)`，生成记录 `method="mle"`；
  - 汇总 CSV 时，保持列对齐：`objective` → 换成 `log_likelihood`（或新增列名，不覆盖 WLS 的 `objective`）。

3) 配置与校验

- 若 `ReconstructionConfig` 中尚无 `mle_max_iterations`、`mle_regularization` 等字段，请按 CLI 与 `config_io.py` 的现有约定在 `controller.py` 的 `ReconstructionConfig` 补齐：
  - `mle_max_iterations: int = 2000`
  - `mle_regularization: Optional[float] = None`（如采用 NLL + L2 正则）
  - 在 `__post_init__` 中增加正数校验。
- `python/qtomography/app/config_io.py` 已支持 `mle_*` 字段的读写与默认值，无需修改。

4) CLI 与帮助信息

- `python/qtomography/cli/main.py` 已提供：
  - `--method {linear,mle,both}`
  - `--mle-regularization`、`--mle-max-iterations`
- 如采用 RρR 且不需要 `mle_regularization`，可保留参数但在说明中标注“可忽略/保留以兼容后续优化器方案”。

5) GUI 集成

- 在 `python/qtomography/gui/panels/config_panel.py`：
  - 新增 `self.mle_checkbox = QtWidgets.QCheckBox("MLE")`，参与“方法选择”并在 `build_config_kwargs` 中将勾选推入 `methods`；
  - 如要暴露 MLE 超参（迭代次数、正则、步长），比照 WLS 的控件增加对应输入并写入 kwargs：
    - `"mle_max_iterations"`、`"mle_regularization"` 等（命名需与 `ReconstructionConfig` 对齐）。

6) 记录与汇总

- 记录仓库：`qtomography.infrastructure.persistence.result_repository.ResultRepository`
- 记录结构：控制器创建 `ReconstructionRecord`，写入 JSON；
- 汇总 CSV：控制器汇总 `summary.csv`，建议：
  - 为 MLE 增加 `log_likelihood` 列；
  - 保持线性/WLS 列名不变，避免破坏已生成数据的可读性。


## 6. 最小改动清单（按文件）

- `python/qtomography/domain/reconstruction/mle.py`
  - 替换为“标准 MLE”实现，提供 `MLEReconstructor` 与 `MLEReconstructionResult`，不再仅仅导入 WLS。
- `python/qtomography/app/controller.py`
  - `_ALLOWED_METHODS` 加入 `"mle"`；
  - 构造/执行流程中增加对 `mle` 的创建与分支处理；
  - 汇总列新增 `log_likelihood`（或与 `objective` 并存）。
- `python/qtomography/gui/panels/config_panel.py`
  - 新增 MLE 复选框和可选超参数输入；
  - 在 `build_config_kwargs` 中输出相应的 `mle_*` 字段。
- `python/qtomography/cli/main.py`
  - 文案与帮助说明确认（参数已具备）。
- `python/qtomography/app/config_io.py`
  - 已支持 `mle_*` 字段，无需更改。


## 7. 测试与验证建议

- 单元测试（可放置于 `python/tests/` 或项目既有测试结构中）：
  - 维度/长度校验：输入长度必须为 `dimension**2`，错误信息与 linear/wls 对齐；
  - 物理可行性：结果 `DensityMatrix` 满足 PSD 与 `|Tr(ρ)-1| < tol`；
  - 单调性：对同一初值，迭代的 `log_likelihood` 非降（或最终值 ≥ 初始值）；
  - 对比线性：随机合成数据下，MLE 的 `log_likelihood` 通常优于线性；
  - 边界稳定性：极小概率项剪裁稳定（`np.clip(..., 1e-12, None)`）。
- 快速验收脚本：重用 `python/demo_full_reconstruction.py` 的工作流，添加 `methods=("linear","mle")`，检查 `summary.csv` 新增列与记录。


## 8. 数值与性能建议

- 初值：默认使用线性结果作为 MLE 初值，通常能显著加速收敛；
- 投影缓存：沿用 `ProjectorSet.get(dimension)`，GUI/CLI 默认开启 `cache_projectors=True`；
- 停止条件：对数似然提升阈值 + Frobenius 范数双重判据；
- 正则化：RρR 路线通常无需 L2 正则；如采用优化器，可开放 `mle_regularization`；
- 日志与进度：复用控制器的 `ProgressEvent` 事件，GUI 进度条自动联动。


## 9. 常见问题（FAQ）

- 概率归一化为何按“前 n 项求和”？
  - 本仓库实验数据约定如此（参见 linear/wls 实现），保持一致可避免跨算法的输入歧义；如实验范式变更，应在三个算法中统一调整。
- 如果仅想替换“当前 WLS 作为 MLE”的行为？
  - 完成 `mle.py` 的标准实现后，Controller 中以 `method="mle"` 调用新实现；保留 `method="wls"` 作为历史/对照路径，便于论文或实验对比。


## 10. 参考实现骨架（可直接粘贴到 mle.py 起步）

```python
"""Maximum Likelihood Estimation (MLE) reconstruction."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal
import numpy as np
from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet

@dataclass
class MLEReconstructionResult:
    density: DensityMatrix
    rho_matrix_raw: np.ndarray
    normalized_probabilities: np.ndarray
    expected_probabilities: np.ndarray
    log_likelihood: float
    success: bool
    n_iterations: int

class MLEReconstructor:
    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        max_iterations: int = 2000,
        cache_projectors: bool = True,
        density_enforce: Literal["within_tol", "project", "none"] = "within_tol",
        density_strict: bool = False,
        density_warn: bool = True,
    ) -> None:
        if dimension < 2:
            raise ValueError("dimension must be >= 2")
        if tolerance <= 0:
            raise ValueError("tolerance must be positive")
        if max_iterations <= 0:
            raise ValueError("max_iterations must be positive")
        self.dimension = dimension
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.density_enforce = density_enforce
        self.density_strict = density_strict
        self.density_warn = density_warn
        self.projector_set = ProjectorSet.get(dimension) if cache_projectors else ProjectorSet(dimension, cache=False)

    def reconstruct(self, probabilities: np.ndarray) -> DensityMatrix:
        return self.reconstruct_with_details(probabilities).density

    def reconstruct_with_details(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> MLEReconstructionResult:
        p = self._normalize_probabilities(probabilities)
        P = self.projector_set.projectors
        rho = self._prepare_initial_density(p, initial_density)
        last_L = -np.inf
        it = 0
        for it in range(self.max_iterations):
            exp_p = np.clip(self._expected_probabilities(rho, P), 1e-12, None)
            R = np.einsum('a, aij -> ij', p / exp_p, P, optimize=True)
            rho_next = R @ rho @ R
            rho_next /= np.trace(rho_next)
            L = float(np.sum(p * np.log(exp_p)))
            if np.isfinite(L) and (L - last_L) < self.tolerance:
                rho = rho_next
                break
            if np.linalg.norm(rho_next - rho, ord='fro') < self.tolerance:
                rho = rho_next
                break
            rho, last_L = rho_next, L
        density = DensityMatrix(
            rho,
            tolerance=self.tolerance,
            enforce=self.density_enforce,
            strict=self.density_strict,
            warn=self.density_warn,
        )
        return MLEReconstructionResult(
            density=density,
            rho_matrix_raw=rho,
            normalized_probabilities=p,
            expected_probabilities=self._expected_probabilities(rho, P),
            log_likelihood=float(np.sum(p * np.log(np.clip(self._expected_probabilities(rho, P), 1e-12, None)))) ,
            success=True,
            n_iterations=it + 1,
        )

    def _prepare_initial_density(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray],
    ) -> np.ndarray:
        if initial_density is None:
            try:
                from .linear import LinearReconstructor
                rho_lin = LinearReconstructor(self.dimension, tolerance=self.tolerance, cache_projectors=False).reconstruct(probabilities).matrix
            except Exception:
                rho_lin = np.eye(self.dimension, dtype=complex) / self.dimension
            return rho_lin
        if isinstance(initial_density, DensityMatrix):
            return initial_density.matrix
        rho_array = np.asarray(initial_density, dtype=complex)
        if rho_array.shape != (self.dimension, self.dimension):
            raise ValueError("initial_density shape must be (n, n)")
        return rho_array

    def _normalize_probabilities(self, probabilities: np.ndarray) -> np.ndarray:
        probs = np.asarray(probabilities, dtype=float).reshape(-1)
        expected_len = self.dimension ** 2
        if probs.size != expected_len:
            raise ValueError(f"probability vector length must be {expected_len}")
        leading_sum = float(np.sum(probs[: self.dimension]))
        if np.isclose(leading_sum, 0.0, atol=self.tolerance):
            raise ValueError("leading n probabilities sum too small")
        return probs / leading_sum

    @staticmethod
    def _expected_probabilities(rho: np.ndarray, projectors: np.ndarray) -> np.ndarray:
        return np.real(np.einsum('aij,ji->a', projectors, rho, optimize=True))
```

> 注意：上面骨架以 RρR 为例；若改用优化器方案，请仿照 `wls.py` 的参数化工具，将目标函数替换为负对数似然，并将结果字段改为 `log_likelihood`。


## 11. 推进顺序建议（逐步合入）

1) 在 `mle.py` 提交最小可用 RρR 版本（仅命令行可用）。
2) 打通 `controller.py` 的 method="mle" 分支，确保 `summary.csv` 含 `log_likelihood`。
3) 增加基础单测与一个 demo（复用 `demo_full_reconstruction.py`）。
4) GUI 新增 MLE 开关与迭代次数输入；联调一遍端到端流程。
5) 根据实验需要，再评估是否补充“优化器方案”与 `mle_regularization` 的实际含义。


---

如需，我可以按本指南直接为你落地 `mle.py` 的标准实现，并完成 Controller/GUI 接入的小改动与基本测试脚本。 
