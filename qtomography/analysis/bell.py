"""Bell-state analysis utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd

from qtomography.domain.density import DensityMatrix
from qtomography.infrastructure.persistence.result_repository import ReconstructionRecord


@dataclass
class BellAnalysisResult:
    """Summary of Bell-state fidelity analysis."""

    dimension: int
    local_dimension: int
    fidelities: np.ndarray

    def to_dict(self) -> dict:
        values = self.fidelities
        return {
            "dimension": self.dimension,
            "local_dimension": self.local_dimension,
            "max_fidelity": float(np.max(values)) if values.size else float("nan"),
            "min_fidelity": float(np.min(values)) if values.size else float("nan"),
            "avg_fidelity": float(np.mean(values)) if values.size else float("nan"),
            "dominant_index": int(np.argmax(values)) if values.size else -1,
        }


def analyze_density_matrix(
    density: DensityMatrix | np.ndarray,
    *,
    dimension: Optional[int] = None,
) -> BellAnalysisResult:
    """Compute Bell-state fidelities for a reconstructed density matrix."""

    if isinstance(density, DensityMatrix):
        rho = density.matrix
    else:
        rho = np.array(density, dtype=complex)

    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("rho must be a square matrix")

    dim = dimensions = rho.shape[0]
    if dimension is not None:
        if dimension != dim:
            raise ValueError("Provided dimension does not match matrix shape")
        dim = dimension

    local_dim = _infer_local_dimension(dim)
    basis = generate_bell_basis(local_dim)
    fidelities = _compute_fidelities(rho, basis)
    return BellAnalysisResult(dimension=dim, local_dimension=local_dim, fidelities=fidelities)


def analyze_record(record: ReconstructionRecord) -> BellAnalysisResult:
    """Run Bell analysis for a persistent reconstruction record."""

    rho = record.density_matrix
    return analyze_density_matrix(rho, dimension=record.dimension)


def generate_bell_basis(local_dimension: int) -> np.ndarray:
    """Return the generalized Bell basis for a given local dimension."""

    states = generate_generalized_bell_states(local_dimension)
    return np.stack(states, axis=0)


def generate_generalized_bell_states(local_dimension: int) -> list[np.ndarray]:
    """Generate generalized Bell states for qudit dimension ``local_dimension``."""

    if local_dimension < 2:
        raise ValueError("local_dimension must be >= 2")

    d = local_dimension
    omega = np.exp(2j * np.pi / d)
    basis_states: list[np.ndarray] = []

    for m in range(d):
        for n in range(d):
            state = np.zeros(d * d, dtype=complex)
            for k in range(d):
                i = k
                j = (k + n) % d
                idx = i * d + j
                state[idx] += omega ** (m * k)
            state /= np.sqrt(d)
            basis_states.append(state)
    return basis_states


def _compute_fidelities(rho: np.ndarray, basis: np.ndarray) -> np.ndarray:
    values = []
    for psi in basis:
        fidelity = np.real_if_close(np.vdot(psi, rho @ psi))
        values.append(float(np.real(fidelity)))
    return np.array(values, dtype=float)


def _infer_local_dimension(dimension: int) -> int:
    local_dim = int(round(np.sqrt(dimension)))
    if local_dim * local_dim != dimension:
        raise ValueError(
            f"Bell analysis requires a perfect-square dimension; got {dimension}"
        )
    return local_dim


def analyze_records(
    records: Sequence[ReconstructionRecord],
) -> pd.DataFrame:
    """Aggregate Bell analysis over a sequence of records."""

    rows = []
    for record in records:
        result = analyze_record(record)
        metrics = result.to_dict()
        row = {
            "bell_dimension": metrics["dimension"],
            "bell_local_dimension": metrics["local_dimension"],
            "bell_max_fidelity": metrics["max_fidelity"],
            "bell_min_fidelity": metrics["min_fidelity"],
            "bell_avg_fidelity": metrics["avg_fidelity"],
            "bell_dominant_index": metrics["dominant_index"],
            "sample": record.metadata.get("sample_index", "?") if record.metadata else "?",
            "method": record.method,
        }
        rows.append(row)
    return pd.DataFrame(rows)
