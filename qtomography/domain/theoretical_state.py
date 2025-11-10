from __future__ import annotations

"""Generate theoretical states compatible with MATLAB easy_solve_ui."""

from dataclasses import dataclass
from typing import Literal, Optional, Sequence

import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.domain.projectors import ProjectorSet

# Default profiles derived from matlab/Theoretical_state.m
_PREDEFINED_PROFILES: dict[str, dict[str, np.ndarray]] = {
    "4D_custom": {
        "dimension": 4,
        "coefficients": np.array([0.5, 0.5, 0.5, 0.5], dtype=float),
        "phases": np.array([0.0, 0.0, 0.0, 1.0], dtype=float),
    },
    "16D_custom": {
        "dimension": 16,
        "coefficients": np.ones(16, dtype=float) * 0.25,
        "phases": np.array(
            [0, 0, 0, 0, 0, 0.5, 1, 1.5, 0, 1, 0, 1, 0, 1.5, 1, 0.5],
            dtype=float,
        ),
    },
}


@dataclass(frozen=True)
class TheoreticalStateResult:
    """Container for a generated theoretical state."""

    dimension: int
    state_type: str
    coefficients: np.ndarray
    phases: np.ndarray
    state_vector: np.ndarray
    density_matrix: DensityMatrix
    measurement_powers: np.ndarray
    fidelity: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "state_type": self.state_type,
            "coefficients": self.coefficients.tolist(),
            "phases": self.phases.tolist(),
            "fidelity": None if self.fidelity is None else float(self.fidelity),
        }


def generate_theoretical_state(
    dimension: int,
    state_type: Literal["4D_custom", "16D_custom", "custom"],
    *,
    coefficients: Optional[Sequence[float]] = None,
    phases: Optional[Sequence[float]] = None,
    reference_state: Optional[DensityMatrix | np.ndarray] = None,
    projector_design: str = "nopovm",
) -> TheoreticalStateResult:
    """Generate a theoretical pure state and optional fidelity metrics.

    Args:
        dimension: Hilbert space dimension (supports >= 2).
        state_type: Built-in or custom profile selection.
        coefficients: Amplitudes for |psi> expansion (custom mode only).
        phases: Phase offsets (in multiples of π) for custom coefficients.
        reference_state: Optional density matrix to compute fidelity.
        projector_design: Measurement design used to derive power spectrum.

    Returns:
        TheoreticalStateResult with density matrix and measurement powers.
    """

    dim = int(dimension)
    if dim < 2:
        raise ValueError("dimension must be >= 2")

    coeffs, phase_values = _resolve_profile(dim, state_type, coefficients, phases)
    state_vector = _build_state_vector(coeffs, phase_values)
    rho = np.outer(state_vector, state_vector.conj())

    density = DensityMatrix(rho, enforce="within_tol", strict=False, warn=False)
    measurement_powers = _compute_measurement_powers(rho, projector_design)

    fidelity_value: Optional[float] = None
    if reference_state is not None:
        reference_dm = (
            reference_state
            if isinstance(reference_state, DensityMatrix)
            else DensityMatrix(reference_state, enforce="within_tol", strict=False, warn=False)
        )
        fidelity_value = density.fidelity(reference_dm)

    return TheoreticalStateResult(
        dimension=dim,
        state_type=state_type,
        coefficients=coeffs.copy(),
        phases=phase_values.copy(),
        state_vector=state_vector,
        density_matrix=density,
        measurement_powers=measurement_powers,
        fidelity=fidelity_value,
    )


def _resolve_profile(
    dimension: int,
    state_type: str,
    coefficients: Optional[Sequence[float]],
    phases: Optional[Sequence[float]],
) -> tuple[np.ndarray, np.ndarray]:
    if state_type in _PREDEFINED_PROFILES:
        profile = _PREDEFINED_PROFILES[state_type]
        if profile["dimension"] != dimension:
            raise ValueError(
                f"{state_type} expects dimension={profile['dimension']}, got {dimension}"
            )
        return profile["coefficients"], profile["phases"]

    if state_type != "custom":
        raise ValueError(f"Unsupported state_type: {state_type}")

    if coefficients is None or phases is None:
        raise ValueError("Custom state requires both coefficients and phases.")

    coeff_array = np.asarray(coefficients, dtype=float)
    phase_array = np.asarray(phases, dtype=float)
    if coeff_array.size != dimension or phase_array.size != dimension:
        raise ValueError("Coefficient and phase lengths must match the dimension.")
    return coeff_array, phase_array


def _build_state_vector(coefficients: np.ndarray, phases: np.ndarray) -> np.ndarray:
    amplitudes = np.asarray(coefficients, dtype=float)
    phase_array = np.asarray(phases, dtype=float)
    state_vector = amplitudes * np.exp(1j * np.pi * phase_array)

    norm = np.linalg.norm(state_vector)
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError("State vector cannot be normalized (check coefficients).")
    return state_vector / norm


def _compute_measurement_powers(rho: np.ndarray, design: str) -> np.ndarray:
    projectors = ProjectorSet(rho.shape[0], design=design).projectors
    # trace(rho @ P_k) for each projector
    powers = np.einsum("ij,kji->k", rho, projectors, optimize=True)
    return np.real(powers).astype(float)
