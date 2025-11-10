"""严格 RρR（迭代最大似然）重建器，使用 H-sandwich 方法处理非 POVM 测量集。

对于测量集满足 ∑ M_j ≠ I 的情况，通过在 σ 空间中工作并使用归一化 POVM Ē_j，
然后将解映射回 ρ 空间，实现严格处理。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal, Tuple

import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet


@dataclass
class RrhoStrictReconstructionResult:
    """严格 RρR 重建的结果。

    属性:
        density: 物理密度矩阵包装器。
        rho_matrix_raw: 原始重建的 ρ（厄米矩阵，迹为1），在 DensityMatrix 强制物理性之前。
        sigma_matrix: 支撑子空间中的最终 σ（在支撑上的迹为1）。
        expected_probabilities: 收敛时的期望条件概率 q_j。
        log_likelihood: 收敛时条件模型的对数似然。
        iterations: 执行的迭代次数。
        converged: 是否满足停止条件。
        diagnostics: 可选的诊断信息（字典），包含支撑维度、H 的最小/最大特征值等。
    """

    density: DensityMatrix
    rho_matrix_raw: np.ndarray
    sigma_matrix: np.ndarray
    expected_probabilities: np.ndarray
    log_likelihood: float
    iterations: int
    converged: bool
    diagnostics: dict


class RrhoStrictReconstructor:
    """使用 H-sandwich 归一化的严格 RρR 重建器。

    接受单个测量设计的计数或按组概率。
    构造 H = ∑ M_j，限制到其支撑 Π（基为 US），定义
    Ē_j = H^{-1/2} M_j H^{-1/2}（约化到支撑），并在 σ 空间中执行标准
    RρR。最后通过 ρ = H^{-1/2} σ H^{-1/2} / Tr(H^{-1} σ) 映射回原空间。
    """

    def __init__(
        self,
        dimension: int,
        *,
        design: str = "nopovm",
        tolerance: float = 1e-10,
        max_iterations: int = 5000,
        tol_state: float = 1e-8,
        tol_ll: float = 1e-9,
        eps_prob: float = 1e-12,
        use_diluted: bool = False,
        diluted_mu: float = 0.9,
        cache_projectors: bool = True,
        eig_rel_thresh: float = 1e-10,
        eig_abs_thresh: Optional[float] = None,
        verbose: bool = False,
        validate_etilde_strict: bool = False,
    ) -> None:
        if dimension < 2:
            raise ValueError("维度必须 >= 2")
        if not (0 < diluted_mu <= 1.0):
            raise ValueError("diluted_mu 必须在 (0,1] 范围内")
        if max_iterations <= 0:
            raise ValueError("max_iterations 必须为正数")

        self.dimension = dimension
        self.design = design
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.tol_state = tol_state
        self.tol_ll = tol_ll
        self.eps_prob = eps_prob
        self.use_diluted = use_diluted
        self.diluted_mu = diluted_mu
        self.eig_rel_thresh = eig_rel_thresh
        self.eig_abs_thresh = eig_abs_thresh
        self.verbose = verbose
        self.validate_etilde_strict = validate_etilde_strict
        self.projector_set = (
            ProjectorSet.get(dimension, design=design)
            if cache_projectors
            else ProjectorSet(dimension, design=design, cache=False)
        )

    # ------------------------------------------------------------------
    def reconstruct(
        self,
        counts_or_probs: np.ndarray,
    ) -> DensityMatrix:
        """重建并仅返回 DensityMatrix。"""

        return self.reconstruct_with_details(counts_or_probs).density

    def reconstruct_with_details(
        self,
        counts_or_probs: np.ndarray,
    ) -> RrhoStrictReconstructionResult:
        """运行严格 RρR 并返回详细结果。"""

        # 按组归一化，将输入解释为条件频率
        f = self._normalize_per_group(counts_or_probs)

        # 准备 H、支撑 Π/US，以及支撑上的 Ē
        projectors = self.projector_set.projectors  # (m, d, d)
        H = np.sum(projectors, axis=0)
        (Pi, H_sqrt, H_sqrt_inv, H_inv, support_dim, w_min, w_max, US) = self._prepare_support_operators(H)

        # 在支撑基上构建约化的 Ē: (m, d_supp, d_supp)
        E_tilde, etilde_diagnostics = self._build_normalized_povm(projectors, US, H_sqrt_inv, support_dim)

        # 在支撑上的 σ 空间中执行 RρR
        sigma0 = np.eye(support_dim, dtype=complex) / float(support_dim)
        sigma, q, iters, converged, ll, iter_diagnostics = self._iterate_rrr_sigma(E_tilde, f, sigma0)

        # 映射回 ρ 空间：通过 US 提升 σ，然后进行 H^{-1/2} sandwich
        sigma_full = US @ sigma @ US.conj().T
        rho_raw = H_sqrt_inv @ sigma_full @ H_sqrt_inv
        denom = np.real(np.trace(H_inv @ sigma_full))
        denom = float(max(denom, self.eps_prob))
        rho_raw = rho_raw / denom
        rho_raw = (rho_raw + rho_raw.conj().T) / 2

        density = DensityMatrix(
            rho_raw,
            tolerance=self.tolerance,
            enforce="within_tol",
            strict=False,
            warn=True,
        )

        diagnostics = {
            "support_dim": int(support_dim),
            "eig_min_H": float(w_min),
            "eig_max_H": float(w_max),
            "converged": bool(converged),
            **etilde_diagnostics,  # 包含 E_tilde 验证诊断信息
            **iter_diagnostics,  # 包含迭代诊断信息
        }

        return RrhoStrictReconstructionResult(
            density=density,
            rho_matrix_raw=rho_raw,
            sigma_matrix=sigma,
            expected_probabilities=q,
            log_likelihood=ll,
            iterations=iters,
            converged=converged,
            diagnostics=diagnostics,
        )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _normalize_per_group(self, counts_or_probs: np.ndarray) -> np.ndarray:
        v = np.asarray(counts_or_probs, dtype=float).reshape(-1)
        m = self.projector_set.projectors.shape[0]
        if v.size != m:
            raise ValueError(f"输入长度必须为 {m}，得到 {v.size}")
        groups = getattr(self.projector_set, "groups", None)
        if groups is None or len(groups) != m:
            total = float(np.sum(v))
            if np.isclose(total, 0.0, atol=self.tolerance):
                raise ValueError("总和为零；无法归一化")
            return v / total
        out = v.astype(float).copy()
        for g in np.unique(groups):
            idx = np.where(groups == g)[0]
            s = float(np.sum(out[idx]))
            if np.isclose(s, 0.0, atol=self.tolerance):
                raise ValueError("组总和为零；无法归一化")
            out[idx] = out[idx] / s
        return out

    def _prepare_support_operators(
        self, H: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, float, float, np.ndarray]:
        # 厄米对称化
        Hh = (H + H.conj().T) / 2
        w, U = np.linalg.eigh(Hh)
        w = np.real(w)
        w_max = float(np.max(w))
        tau_abs = float(self.eig_abs_thresh) if self.eig_abs_thresh is not None else 0.0
        tau_rel = float(self.eig_rel_thresh) * max(w_max, 1.0)
        tau = max(tau_abs, tau_rel)
        S = w > tau
        if not np.any(S):
            idx = int(np.argmax(w))
            S = np.zeros_like(w, dtype=bool)
            S[idx] = True
        wS = w[S]
        US = U[:, S]  # (d, d_supp)
        Pi = US @ US.conj().T  # (d, d)
        sqrt_wS = np.sqrt(wS)
        inv_sqrt_wS = 1.0 / np.maximum(sqrt_wS, self.eps_prob)
        inv_wS = 1.0 / np.maximum(wS, self.eps_prob)
        H_sqrt = US @ np.diag(sqrt_wS) @ US.conj().T  # (d, d)
        H_sqrt_inv = US @ np.diag(inv_sqrt_wS) @ US.conj().T  # (d, d)
        H_inv = US @ np.diag(inv_wS) @ US.conj().T  # (d, d)
        return Pi, H_sqrt, H_sqrt_inv, H_inv, US.shape[1], float(np.min(wS)), float(np.max(wS)), US

    def _build_normalized_povm(
        self,
        projectors: np.ndarray,
        US: np.ndarray,
        H_sqrt_inv: np.ndarray,
        support_dim: int,
    ) -> Tuple[np.ndarray, dict]:
        """在支撑基上构建约化的 Ē_j: Ẽ_a = B† M_a B，其中 B = H^{-1/2} US。
        
        返回:
            E_tilde: 支撑上的归一化 POVM，形状为 (m, d_supp, d_supp)
            diagnostics: 包含验证指标的字典
        """
        B = H_sqrt_inv @ US  # (d, d_supp)
        E_tilde = np.einsum('pi,apq,qj->aij', B.conj(), projectors, B, optimize=True)
        E_tilde = (E_tilde + np.transpose(E_tilde.conj(), (0, 2, 1))) / 2
        
        # 验证：Σ Ē_j 在支撑上应该等于 I
        E_sum = np.sum(E_tilde, axis=0)
        expected_I = np.eye(support_dim, dtype=complex)
        
        # 计算偏差
        E_sum_diff = E_sum - expected_I
        max_dev_abs = float(np.max(np.abs(E_sum_diff)))
        max_dev_fro = float(np.linalg.norm(E_sum_diff, ord='fro'))
        
        # 基于支撑维度的自适应容差
        atol_adaptive = 1e-8 * max(support_dim, 1.0)
        
        diagnostics = {
            "etilde_sum_max_dev_abs": max_dev_abs,
            "etilde_sum_max_dev_fro": max_dev_fro,
            "etilde_sum_valid": bool(np.allclose(E_sum, expected_I, atol=atol_adaptive)),
        }
        
        # 可选的严格验证
        if self.validate_etilde_strict and max_dev_abs > atol_adaptive:
            raise RuntimeError(
                f"归一化 POVM 验证失败（严格模式）："
                f"最大偏差 {max_dev_abs:.2e} > 容差 {atol_adaptive:.2e}"
            )
        
        # 可选：对样本进行快速正定性检查
        if support_dim <= 10:  # 仅适用于小维度
            sample_idx = min(2, E_tilde.shape[0])
            min_eig_sample = []
            for i in range(sample_idx):
                eigvals = np.linalg.eigvalsh(E_tilde[i])
                min_eig_sample.append(float(np.min(eigvals)))
            diagnostics["etilde_min_eig_sample"] = float(np.min(min_eig_sample)) if min_eig_sample else None
        
        return E_tilde, diagnostics

    def _iterate_rrr_sigma(
        self,
        E_tilde: np.ndarray,
        f: np.ndarray,
        sigma0: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, int, bool, float, dict]:
        """在 σ 空间中使用约化的 Ē_j 执行标准 RρR 迭代。
        
        返回:
            sigma: 最终的 σ 矩阵
            q: 最终概率
            iterations: 迭代次数
            converged: 是否收敛
            log_likelihood: 最终对数似然
            diagnostics: 包含迭代统计信息的字典
        """
        d_supp = sigma0.shape[0]
        sigma = sigma0.copy()
        ll_prev = -np.inf
        converged = False
        
        # 诊断计数器
        decrease_ll_count = 0
        reset_count = 0
        reset_first_iter = None
        min_q = float('inf')
        min_trace = float('inf')
        final_dn = None
        final_dll = None

        for it in range(1, self.max_iterations + 1):
            sigma = (sigma + sigma.conj().T) / 2
            q = np.real(np.einsum('aij,ji->a', E_tilde, sigma, optimize=True))
            q = np.clip(q, self.eps_prob, None)
            min_q = min(min_q, float(np.min(q)))
            
            ll = float(np.sum(f * np.log(q)))

            # 单调性监控
            if it > 1:
                delta_logL = ll - ll_prev
                if delta_logL < -1e-10:  # 允许小的数值误差
                    decrease_ll_count += 1
                    if self.verbose:
                        print(f"警告：迭代 {it} 时对数似然下降 {delta_logL:.2e}（可能实现问题）")

            r = f / q
            R = np.einsum('a,aij->ij', r, E_tilde, optimize=True)
            R = (R + R.conj().T) / 2
            if self.use_diluted:
                R = self.diluted_mu * R + (1.0 - self.diluted_mu) * np.eye(d_supp, dtype=complex)

            sigma_prev = sigma
            sigma = R @ sigma @ R
            sigma = (sigma + sigma.conj().T) / 2
            tr = float(np.real(np.trace(sigma)))
            min_trace = min(min_trace, tr)
            
            if tr <= self.eps_prob:
                reset_count += 1
                if reset_first_iter is None:
                    reset_first_iter = int(it)
                sigma = np.eye(d_supp, dtype=complex) / float(d_supp)
                if self.verbose:
                    print(f"警告：迭代 {it} 时迹过小 ({tr:.2e} ≤ {self.eps_prob:.2e})，重置")
            else:
                sigma = sigma / tr

            dn = float(np.linalg.norm(sigma - sigma_prev, ord='fro'))
            dll = float(abs(ll - ll_prev))
            final_dn = dn
            final_dll = dll
            
            if dn < self.tol_state and dll < self.tol_ll:
                converged = True
                ll_prev = ll
                break
            ll_prev = ll

        if not converged and self.verbose:
            print(f"警告：已达最大迭代次数 {self.max_iterations}，可能未完全收敛")

        diagnostics = {
            "decrease_ll_count": int(decrease_ll_count),
            "reset_count": int(reset_count),
            "reset_first_iter": reset_first_iter,
            "min_q": float(min_q),
            "min_trace": float(min_trace),
            "final_dn": float(final_dn) if final_dn is not None else None,
            "final_dll": float(final_dll) if final_dll is not None else None,
        }

        return sigma, q, (it if converged else self.max_iterations), converged, ll_prev, diagnostics


__all__ = [
    "RrhoStrictReconstructor",
    "RrhoStrictReconstructionResult",
]

