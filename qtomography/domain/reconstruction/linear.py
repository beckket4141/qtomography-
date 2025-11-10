"""线性层析重构器，实现 MATLAB `reconstruct_density_matrix_nD.m` 的 Python 对应版本。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal

import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet


@dataclass
class LinearReconstructionResult:
    """线性重构运行产生的完整结果。

    属性:
        density: 经过物理化处理后的密度矩阵，可直接用于后续计算或分析。
        rho_matrix_raw: 在线性方程求解后、物理化前的原始矩阵，便于检查噪声或调试差异。
        normalized_probabilities: 按 MATLAB 流程归一化后的观测概率向量，重构的实际输入。
        residuals: 最小二乘求解返回的残差；若方程完全可解，则该数组可能为空。
        rank: 测量矩阵的数值秩，可帮助判断是否存在秩亏或条件不良。
        singular_values: 测量矩阵的奇异值序列，用于评估条件数和重构稳定性。
    """

    density: DensityMatrix
    rho_matrix_raw: np.ndarray
    normalized_probabilities: np.ndarray
    residuals: np.ndarray
    rank: int
    singular_values: np.ndarray


class LinearReconstructor:
    """线性层析重构器。

    参数:
        dimension: 希尔伯特空间维度 n。
        tolerance: 传递给 DensityMatrix 的数值容差。
        regularization: 可选的岭回归系数 λ。若提供，则求解
            (M^T M + λ I) rho_vec = M^T P，这在噪声较大时更稳定。
        cache_projectors: 是否复用 ProjectorSet 缓存。
        density_enforce: DensityMatrix 的物理化策略。
        density_strict: 是否对显著非物理输入抛出异常。
        density_warn: 是否对显著非物理输入发出警告。
    """

    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        regularization: Optional[float] = None,
        cache_projectors: bool = True,
        design: str = "mub",
        density_enforce: Literal["within_tol", "project", "none"] = "within_tol",
        density_strict: bool = False,
        density_warn: bool = True,
    ) -> None:
        # 简单的输入守卫
        if dimension < 2:
            raise ValueError("维度必须大于等于 2")
        if tolerance <= 0:
            raise ValueError("tolerance 必须为正数")
        if regularization is not None and regularization < 0:
            raise ValueError("regularization 必须为非负数")

        self.dimension = dimension
        self.tolerance = tolerance
        self.regularization = regularization # 正则化中的λ参数(目前只支持岭回归:(M^T * M + λ * I) * rho_vec = M^T * P)
        self.density_enforce = density_enforce
        self.density_strict = density_strict
        self.density_warn = density_warn
        self.projector_set = (
            ProjectorSet.get(dimension, design=design)
            if cache_projectors
            else ProjectorSet(dimension, design=design, cache=False)
        )

    # ------------------------------------------------------------------
    def _normalize_probabilities_grouped(self, probabilities: np.ndarray) -> np.ndarray:
        """Per-group normalization using ProjectorSet.groups.

        - If input are counts, this converts to per-group probabilities.
        - If input are already per-group probabilities, this is idempotent
          up to numerical tolerance.
        """
        probs = np.asarray(probabilities, dtype=float).reshape(-1)
        m = self.projector_set.projectors.shape[0]
        if probs.size != m:
            raise ValueError(f"probability vector length must be {m}, got {probs.size}")

        groups = getattr(self.projector_set, "groups", None)
        if groups is None or len(groups) != m:
            total = float(np.sum(probs))
            if np.isclose(total, 0.0, atol=self.tolerance):
                raise ValueError("sum of probabilities is zero")
            return probs / total

        out = probs.astype(float).copy()
        for g in np.unique(groups):
            idx = np.where(groups == g)[0]
            s = float(np.sum(out[idx]))
            if np.isclose(s, 0.0, atol=self.tolerance):
                raise ValueError("group sum is zero; cannot normalize")
            out[idx] = out[idx] / s
        return out

    def reconstruct(self, probabilities: np.ndarray) -> DensityMatrix:
        """仅返回物理化后的密度矩阵。"""

        result = self.reconstruct_with_details(probabilities)
        return result.density

    def reconstruct_with_details(
        self, probabilities: np.ndarray
    ) -> LinearReconstructionResult:
        """执行线性重构并返回包含详细调试信息的结果对象。"""

        probs = self._normalize_probabilities_grouped(probabilities)
        measurement_matrix = self.projector_set.measurement_matrix

        if self.regularization is None:
            rho_vec, residuals, rank, singular_values = np.linalg.lstsq(
                measurement_matrix, probs, rcond=None
            )
        else:
            # 岭回归: (M^T M + λ I) rho_vec = M^T P
            mtm = measurement_matrix.T @ measurement_matrix
            lambda_eye = self.regularization * np.eye(mtm.shape[0])
            right_hand = measurement_matrix.T @ probs
            rho_vec = np.linalg.solve(mtm + lambda_eye, right_hand)
            # 对于 solve 没有直接返回残差/奇异值，这里手工计算
            residuals = probs - measurement_matrix @ rho_vec
            residuals = np.array([np.linalg.norm(residuals) ** 2])
            rank = np.linalg.matrix_rank(measurement_matrix)
            singular_values = np.linalg.svd(measurement_matrix, compute_uv=False)

        rho_matrix = rho_vec.reshape(self.dimension, self.dimension)
        rho_matrix = rho_matrix.conj()

        density = DensityMatrix(
            rho_matrix, 
            tolerance=self.tolerance,
            enforce=self.density_enforce,
            strict=self.density_strict,
            warn=self.density_warn
        )

        return LinearReconstructionResult(
            density=density,
            rho_matrix_raw=rho_matrix,
            normalized_probabilities=probs,
            residuals=residuals,
            rank=rank,
            singular_values=singular_values,
        )

    # ------------------------------------------------------------------
    def _normalize_probabilities(self, probabilities: np.ndarray) -> np.ndarray:
        """对测量概率向量做安全归一化。"""

        probs = np.asarray(probabilities, dtype=float).reshape(-1)
        expected_len = self.dimension ** 2
        if probs.size != expected_len:
            raise ValueError(
                f"概率向量长度应为 {expected_len}, 实际为 {probs.size}"
            )

        leading_sum = np.sum(probs[: self.dimension])
        if np.isclose(leading_sum, 0.0, atol=self.tolerance):
            raise ValueError("前 n 个分量之和过小, 无法安全归一化")

        probs_normalized = probs / leading_sum
        return probs_normalized






