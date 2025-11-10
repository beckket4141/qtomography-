"""Metric utilities for reconstructed density matrices and related artefacts."""

from __future__ import annotations

from typing import Optional

import numpy as np

__all__ = [
    "eigenvalue_entropy",
    "condition_number",
]


def eigenvalue_entropy(
    eigenvalues: np.ndarray,
    *,
    epsilon: float = 1e-15,
    base: str = "natural",
) -> float:
    """Compute the (normalised) von Neumann entropy of a set of eigenvalues.

    Parameters
    ----------
    eigenvalues:
        Eigenvalues of a density matrix (not necessarily normalised).
    epsilon:
        Threshold used to discard extremely small eigenvalues to avoid log(0).
    base:
        Logarithm base, ``"natural"`` (default) or ``"2"``.

    Returns
    -------
    float
        Von Neumann entropy ``S = -Tr(ρ log ρ)`` measured in the requested base.
    """

    if eigenvalues.size == 0:
        return 0.0

    trace = np.sum(eigenvalues)
    if not np.isclose(trace, 1.0, atol=1e-6):
        eigenvalues = eigenvalues / trace

    eigs = eigenvalues[eigenvalues > epsilon]
    if eigs.size == 0:
        return 0.0

    if base == "natural":
        return -float(np.sum(eigs * np.log(eigs)))
    if base == "2":
        return -float(np.sum(eigs * np.log2(eigs)))
    raise ValueError(f"不支持的对数底数: {base}")


def condition_number(
    singular_values: np.ndarray,
    *,
    tolerance: Optional[float] = None,
) -> float:
    """Compute a numerically stable condition number for a singular spectrum.

    Parameters
    ----------
    singular_values:
        Singular values obtained from a reconstruction algorithm.
    tolerance:
        Optional relative tolerance. Values below the tolerance are discarded.
        Default uses ``max(singular_values) * 1e-10``.

    Returns
    -------
    float
        Ratio ``σ_max / σ_min`` with safeguards to avoid ``inf`` or ``nan``.
        Returns ``1e16`` if there is not enough information to compute a ratio.
    """

    if singular_values.size == 0:
        return 1e16

    max_sv = float(np.max(singular_values))
    if tolerance is None:
        tolerance = max_sv * 1e-10

    finite_sv = singular_values[singular_values > tolerance]
    if finite_sv.size == 0:
        return 1e16

    return float(max_sv / np.min(finite_sv))

