"""Strict RρR (iterative MLE) reconstructor with H-sandwich for non-POVM sets.

Implements the rigorous treatment for measurement sets where
∑ M_j ≠ I by working in the σ-space with a normalized POVM Ē_j and then
mapping the solution back to ρ-space.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal, Tuple

import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet


@dataclass
class RrhoStrictReconstructionResult:
    """Result for strict RρR reconstruction.

    Attributes:
        density: Physical density matrix wrapper.
        rho_matrix_raw: Raw reconstructed ρ (Hermitian, trace-1) before DensityMatrix enforcement.
        sigma_matrix: Final σ in the support subspace (trace-1 on support).
        expected_probabilities: Expected conditional probabilities q_j at convergence.
        log_likelihood: Log-likelihood in conditional model at convergence.
        iterations: Number of iterations executed.
        converged: Whether stopping criteria met.
        diagnostics: Optional diagnostics (dict) with support dimension, min/max eig of H, etc.
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
    """Strict RρR reconstructor using H-sandwich normalization.

    Accepts counts or per-group probabilities for a single measurement design.
    Constructs H = ∑ M_j, restricts to its support Π with basis US, defines
    Ē_j = H^{-1/2} M_j H^{-1/2} reduced to the support, and performs standard
    RρR in σ-space. Finally maps back via ρ = H^{-1/2} σ H^{-1/2} / Tr(H^{-1} σ).
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
            raise ValueError("dimension must be >= 2")
        if not (0 < diluted_mu <= 1.0):
            raise ValueError("diluted_mu must be in (0,1]")
        if max_iterations <= 0:
            raise ValueError("max_iterations must be positive")

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
        """Reconstruct and return only the DensityMatrix."""

        return self.reconstruct_with_details(counts_or_probs).density

    def reconstruct_with_details(
        self,
        counts_or_probs: np.ndarray,
    ) -> RrhoStrictReconstructionResult:
        """Run strict RρR and return detailed result."""

        # Normalize per group to interpret input as conditional frequencies
        f = self._normalize_per_group(counts_or_probs)

        # Prepare H, support Π/US, and Ē on support
        projectors = self.projector_set.projectors  # (m, d, d)
        H = np.sum(projectors, axis=0)
        (Pi, H_sqrt, H_sqrt_inv, H_inv, support_dim, w_min, w_max, US) = self._prepare_support_operators(H)

        # Build Ē reduced on support basis: (m, d_supp, d_supp)
        E_tilde, etilde_diagnostics = self._build_normalized_povm(projectors, US, H_sqrt_inv, support_dim)

        # RρR in σ-space on support
        sigma0 = np.eye(support_dim, dtype=complex) / float(support_dim)
        sigma, q, iters, converged, ll, iter_diagnostics = self._iterate_rrr_sigma(E_tilde, f, sigma0)

        # Map back to ρ-space: lift σ via US, then H^{-1/2} sandwich
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
            **etilde_diagnostics,  # Include E_tilde validation diagnostics
            **iter_diagnostics,  # Include iteration diagnostics
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
    # Internals
    # ------------------------------------------------------------------
    def _normalize_per_group(self, counts_or_probs: np.ndarray) -> np.ndarray:
        v = np.asarray(counts_or_probs, dtype=float).reshape(-1)
        m = self.projector_set.projectors.shape[0]
        if v.size != m:
            raise ValueError(f"input length must be {m}, got {v.size}")
        groups = getattr(self.projector_set, "groups", None)
        if groups is None or len(groups) != m:
            total = float(np.sum(v))
            if np.isclose(total, 0.0, atol=self.tolerance):
                raise ValueError("sum is zero; cannot normalize")
            return v / total
        out = v.astype(float).copy()
        for g in np.unique(groups):
            idx = np.where(groups == g)[0]
            s = float(np.sum(out[idx]))
            if np.isclose(s, 0.0, atol=self.tolerance):
                raise ValueError("group sum is zero; cannot normalize")
            out[idx] = out[idx] / s
        return out

    def _prepare_support_operators(
        self, H: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, float, float, np.ndarray]:
        # Hermitian symmetrize
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
        """Build reduced Ē_j on the support basis: Ẽ_a = B† M_a B, B = H^{-1/2} US.
        
        Returns:
            E_tilde: (m, d_supp, d_supp) normalized POVM on support
            diagnostics: dict with validation metrics
        """
        B = H_sqrt_inv @ US  # (d, d_supp)
        E_tilde = np.einsum('pi,apq,qj->aij', B.conj(), projectors, B, optimize=True)
        E_tilde = (E_tilde + np.transpose(E_tilde.conj(), (0, 2, 1))) / 2
        
        # Validate: Σ Ē_j should equal I on support
        E_sum = np.sum(E_tilde, axis=0)
        expected_I = np.eye(support_dim, dtype=complex)
        
        # Compute deviations
        E_sum_diff = E_sum - expected_I
        max_dev_abs = float(np.max(np.abs(E_sum_diff)))
        max_dev_fro = float(np.linalg.norm(E_sum_diff, ord='fro'))
        
        # Adaptive tolerance based on support dimension
        atol_adaptive = 1e-8 * max(support_dim, 1.0)
        
        diagnostics = {
            "etilde_sum_max_dev_abs": max_dev_abs,
            "etilde_sum_max_dev_fro": max_dev_fro,
            "etilde_sum_valid": bool(np.allclose(E_sum, expected_I, atol=atol_adaptive)),
        }
        
        # Optional strict validation
        if self.validate_etilde_strict and max_dev_abs > atol_adaptive:
            raise RuntimeError(
                f"归一化 POVM 验证失败（严格模式）："
                f"最大偏差 {max_dev_abs:.2e} > 容差 {atol_adaptive:.2e}"
            )
        
        # Optional: Quick positive-definiteness check on a sample
        if support_dim <= 10:  # Only for small dimensions
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
        """Standard RρR iteration in σ-space using reduced Ē_j.
        
        Returns:
            sigma: Final σ matrix
            q: Final probabilities
            iterations: Number of iterations
            converged: Whether converged
            log_likelihood: Final log-likelihood
            diagnostics: dict with iteration statistics
        """
        d_supp = sigma0.shape[0]
        sigma = sigma0.copy()
        ll_prev = -np.inf
        converged = False
        
        # Diagnostic counters
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

            # Monotonicity monitoring
            if it > 1:
                delta_logL = ll - ll_prev
                if delta_logL < -1e-10:  # Allow small numerical error
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

