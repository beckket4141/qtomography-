"""加权最小二乘 (WLS) 层析重构实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal

import numpy as np
from scipy.optimize import minimize
from scipy.linalg import cholesky

from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet


@dataclass
class WLSReconstructionResult:
    """加权最小二乘重构的完整输出。

    属性:
        density: 经过物理化处理后的密度矩阵，可直接用于后续分析。
        rho_matrix_raw: 由优化参数直接构造出的原始密度矩阵（已归一化、未再次物理化）。
        normalized_probabilities: 按照 MATLAB 流程归一化后的观测概率向量。
        expected_probabilities: 由最终密度矩阵计算得到的理论概率，用于比对残差。
        objective_value: 优化结束时的目标函数值（chi²）。
        success: 优化器是否标记为成功。
        status: 优化器返回的状态码。
        message: 优化器返回的信息，用于调试。
        n_iterations: 优化器迭代次数（若优化器未提供则为 0）。
        n_function_evaluations: 目标函数调用次数（若优化器未提供则为 0）。
    """

    density: DensityMatrix
    rho_matrix_raw: np.ndarray
    normalized_probabilities: np.ndarray
    expected_probabilities: np.ndarray
    objective_value: float
    success: bool
    status: int
    message: str
    n_iterations: int
    n_function_evaluations: int


class WLSReconstructor:
    """加权最小二乘层析重构器。"""

    def __init__(
        self,
        dimension: int,
        *,
        tolerance: float = 1e-10,
        optimizer: str = "SLSQP",
        regularization: Optional[float] = None,
        max_iterations: int = 1_000_000,
        optimizer_tolerance: float = 1e-12,
        cache_projectors: bool = True,
        design: str = "mub",
        density_enforce: Literal["within_tol", "project", "none"] = "within_tol",
        density_strict: bool = False,
        density_warn: bool = True,
    ) -> None:
        if dimension < 2:
            raise ValueError("维度必须大于等于 2")
        if tolerance <= 0:
            raise ValueError("tolerance 必须为正数")
        if regularization is not None and regularization < 0:
            raise ValueError("regularization 必须为非负数")
        if max_iterations <= 0:
            raise ValueError("max_iterations 必须为正整数")
        if optimizer_tolerance <= 0:
            raise ValueError("optimizer_tolerance 必须为正数")

        self.dimension = dimension
        self.tolerance = tolerance
        self.optimizer = optimizer
        self.regularization = regularization
        self.max_iterations = max_iterations
        self.optimizer_tolerance = optimizer_tolerance
        self.density_enforce = density_enforce
        self.density_strict = density_strict
        self.density_warn = density_warn
        self.projector_set = (
            ProjectorSet.get(dimension, design=design)
            if cache_projectors
            else ProjectorSet(dimension, design=design, cache=False)
        )

    # ------------------------------------------------------------------
    def reconstruct(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> DensityMatrix:
        """仅返回最终物理化后的密度矩阵。"""

        result = self.reconstruct_with_details(probabilities, initial_density=initial_density)
        return result.density

    def reconstruct_with_details(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray] = None,
    ) -> WLSReconstructionResult:
        """执行 WLS 重构并返回包含详细信息的结果对象。"""

        probs_normalized = self._normalize_probabilities_grouped(probabilities)
        projectors = self.projector_set.projectors

        rho_initial = self._prepare_initial_density(probs_normalized, initial_density)
        params0 = self.encode_density_to_params(rho_initial)

        minimize_options = {
            "maxiter": self.max_iterations,
            "ftol": self.optimizer_tolerance,
            "disp": False,
        }

        res = minimize(
            fun=self._objective_function,
            x0=params0,
            args=(probs_normalized, projectors, self.regularization),
            method=self.optimizer,
            options=minimize_options,
            tol=self.optimizer_tolerance,
        )

        rho_opt = self.decode_params_to_density(res.x, self.dimension)
        density = DensityMatrix(
            rho_opt, 
            tolerance=self.tolerance,
            enforce=self.density_enforce,
            strict=self.density_strict,
            warn=self.density_warn
        )
        expected_probs = self._expected_probabilities(rho_opt, projectors)
        objective_val = self._objective_function(res.x, probs_normalized, projectors, self.regularization)

        return WLSReconstructionResult(
            density=density,
            rho_matrix_raw=rho_opt,
            normalized_probabilities=probs_normalized,
            expected_probabilities=expected_probs,
            objective_value=float(objective_val),
            success=bool(res.success),
            status=int(res.status),
            message=str(res.message),
            n_iterations=int(getattr(res, "nit", 0) or 0),
            n_function_evaluations=int(getattr(res, "nfev", 0) or 0),
        )

    # ------------------------------------------------------------------
    def _prepare_initial_density(
        self,
        probabilities: np.ndarray,
        initial_density: Optional[DensityMatrix | np.ndarray],
    ) -> np.ndarray:
        if initial_density is None:
            try:
                from .linear import LinearReconstructor

                linear = LinearReconstructor(
                    self.dimension,
                    tolerance=self.tolerance,
                    cache_projectors=False,
                )
                rho_lin = linear.reconstruct(probabilities).matrix
            except Exception:
                rho_lin = np.eye(self.dimension, dtype=complex) / self.dimension
            return rho_lin

        if isinstance(initial_density, DensityMatrix):
            return initial_density.matrix

        rho_array = np.asarray(initial_density, dtype=complex)
        if rho_array.shape != (self.dimension, self.dimension):
            raise ValueError("initial_density 形状必须为 (n, n)")
        return rho_array

    # ------------------------------------------------------------------
    def _normalize_probabilities(self, probabilities: np.ndarray) -> np.ndarray:
        probs = np.asarray(probabilities, dtype=float).reshape(-1)
        expected_len = self.dimension ** 2
        if probs.size != expected_len:
            raise ValueError(
                f"概率向量长度应为 {expected_len}, 实际为 {probs.size}"
            )

        leading_sum = np.sum(probs[: self.dimension])
        if np.isclose(leading_sum, 0.0, atol=self.tolerance):
            raise ValueError("前 n 个分量之和过小, 无法安全归一化")
        return probs / leading_sum

    def _normalize_probabilities_grouped(self, probabilities: np.ndarray) -> np.ndarray:
        """Normalize per measurement group using ProjectorSet.groups.

        Accepts counts or already-normalized per-group probabilities.
        
        特殊处理：对于 nopovm 设计，使用前 n 个数据之和作为归一化因子。
        """
        # 特殊处理：nopovm 设计使用前 n 个数据之和归一化
        if self.projector_set.design == "nopovm":
            return self._normalize_probabilities(probabilities)
        
        probs = np.asarray(probabilities, dtype=float).reshape(-1)
        m = self.projector_set.projectors.shape[0]
        if probs.size != m:
            raise ValueError(
                f"probability vector length must be {m}, got {probs.size}"
            )
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

    # ------------------------------------------------------------------
    @staticmethod
    def encode_density_to_params(rho: np.ndarray) -> np.ndarray:
        """将物理密度矩阵编码为实参数向量。"""

        if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
            raise ValueError("rho 必须是方阵")
        dimension = rho.shape[0]

        # 使用 Cholesky 分解，必要时添加小的对角补偿
        eps = 1e-12
        for _ in range(5):
            try:
                lower = cholesky(rho, lower=True)
                break
            except np.linalg.LinAlgError:
                rho = rho + eps * np.eye(dimension, dtype=complex)
                eps *= 10
        else:
            raise np.linalg.LinAlgError("无法对密度矩阵执行 Cholesky 分解")

        params = []
        for i in range(dimension):
            params.append(np.log(np.real(lower[i, i]).clip(min=1e-18)))
            for j in range(i):
                params.append(np.real(lower[i, j]))
                params.append(np.imag(lower[i, j]))
        return np.array(params, dtype=float)

    @staticmethod
    def decode_params_to_density(params: np.ndarray, dimension: int) -> np.ndarray:
        """将实参数向量解码为密度矩阵。"""

        params = np.asarray(params, dtype=float)
        if params.size != dimension ** 2:
            raise ValueError(
                f"参数长度应为 {dimension ** 2}, 实际为 {params.size}"
            )

        lower = np.zeros((dimension, dimension), dtype=complex)
        idx = 0
        for i in range(dimension):
            lower[i, i] = np.exp(params[idx])
            idx += 1
            for j in range(i):
                real_part = params[idx]
                imag_part = params[idx + 1]
                lower[i, j] = real_part + 1j * imag_part
                idx += 2

        rho = lower @ lower.conj().T
        trace_val = np.trace(rho)
        if not np.isclose(trace_val, 1.0, atol=1e-12):
            rho = rho / trace_val
        return rho

    # ------------------------------------------------------------------
    def _objective_function(
        self,
        params: np.ndarray,
        probabilities: np.ndarray,
        projectors: np.ndarray,
        regularization: Optional[float],
    ) -> float:
        rho = self.decode_params_to_density(params, self.dimension)
        expected = self._expected_probabilities(rho, projectors)
        diff = probabilities - expected
        denom = np.sqrt(np.maximum(probabilities, 0.0) + 1.0)
        chi2 = np.sum((diff ** 2) / denom)
        if regularization:
            chi2 += regularization * np.sum(params ** 2)
        return float(chi2)

    @staticmethod
    def _expected_probabilities(rho: np.ndarray, projectors: np.ndarray) -> np.ndarray:
        return np.real(np.einsum('aij,ji->a', projectors, rho, optimize=True))


__all__ = ["WLSReconstructor", "WLSReconstructionResult"]

