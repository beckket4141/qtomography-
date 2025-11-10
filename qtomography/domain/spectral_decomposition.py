from __future__ import annotations

"""Spectral decomposition utilities for density matrices."""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from qtomography.domain.density import DensityMatrix


@dataclass(frozen=True)
class SpectralDecompositionResult:
    """Encapsulates the dominant pure state extracted from a density matrix."""

    dimension: int
    dominant_eigenvalue: float
    pure_state_vector: np.ndarray
    coefficients: np.ndarray
    amplitudes: np.ndarray
    phases: np.ndarray
    eigenvalues: np.ndarray


def perform_spectral_decomposition(
    density_matrix: DensityMatrix | np.ndarray,
    *,
    phase_tolerance: float = 1e-9,
) -> SpectralDecompositionResult:
    """Perform eigen-decomposition and extract the dominant pure state.

    Mirrors MATLAB's ``perform_spectral_decomposition`` helper:
    1. Hermitian-eigen decomposition of the density matrix.
    2. Select the eigenvector corresponding to the largest eigenvalue.
    3. Project onto the computational basis to obtain coefficients,
       magnitudes ``r`` and relative phases ``phi``.

    Args:
        density_matrix: DensityMatrix instance or raw ndarray.
        phase_tolerance: Threshold used to pick the reference phase
            when determining relative phases (first amplitude > tol).

    Returns:
        SpectralDecompositionResult with amplitudes/phases suitable for plotting.
    """

    rho = _coerce_density_matrix(density_matrix)
    hermitian = (rho + rho.conj().T) / 2.0

    eigenvalues, eigenvectors = np.linalg.eigh(hermitian)
    dominant_index = int(np.argmax(np.real(eigenvalues)))
    dominant_value = float(np.real(eigenvalues[dominant_index]))

    pure_state = eigenvectors[:, dominant_index]
    # Ensure normalized (np.linalg.eigh already returns normalized vectors, but safeguard)
    norm = np.linalg.norm(pure_state)
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError("Failed to normalize dominant eigenvector.")
    pure_state = pure_state / norm

    coefficients = pure_state.copy()
    amplitudes = np.abs(coefficients)
    raw_phases = np.angle(coefficients)

    reference_index = _first_significant_index(amplitudes, tol=phase_tolerance)
    reference_phase = raw_phases[reference_index] if reference_index is not None else 0.0
    phases = raw_phases - reference_phase

    return SpectralDecompositionResult(
        dimension=rho.shape[0],
        dominant_eigenvalue=dominant_value,
        pure_state_vector=pure_state,
        coefficients=coefficients,
        amplitudes=amplitudes,
        phases=phases,
        eigenvalues=np.sort(np.real(eigenvalues))[::-1],
    )


def _coerce_density_matrix(matrix: DensityMatrix | np.ndarray) -> np.ndarray:
    if isinstance(matrix, DensityMatrix):
        return matrix.matrix
    array = np.array(matrix, dtype=complex)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("density_matrix must be a square matrix.")
    return array


def _first_significant_index(amplitudes: np.ndarray, *, tol: float) -> Optional[int]:
    for idx, value in enumerate(amplitudes):
        if value > tol:
            return idx
    return None
