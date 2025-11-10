from __future__ import annotations

import numpy as np
from dataclasses import dataclass


@dataclass
class SICDesign:
    dimension: int
    projectors: np.ndarray  # (m, d, d)
    groups: np.ndarray      # (m,)
    measurement_matrix: np.ndarray  # (m, d*d)


def _sic_qubit() -> np.ndarray:
    """Return 4 SIC qubit states as column vectors (d=2).

    A standard tetrahedral SIC set on Bloch sphere:
      |psi1> = |0>
      |psi2> = (|0> + sqrt(2)|1>) / sqrt(3)
      |psi3> = (|0> + sqrt(2) e^{2pi i/3} |1>) / sqrt(3)
      |psi4> = (|0> + sqrt(2) e^{4pi i/3} |1>) / sqrt(3)
    """
    d = 2
    states = []
    # |0>
    v1 = np.array([1.0, 0.0], dtype=complex)
    states.append(v1)
    # common factor
    s2 = np.sqrt(2.0)
    w = np.exp(2j * np.pi / 3.0)
    v2 = (np.array([1.0, s2], dtype=complex)) / np.sqrt(3.0)
    v3 = (np.array([1.0, s2 * w], dtype=complex)) / np.sqrt(3.0)
    v4 = (np.array([1.0, s2 * w.conjugate()], dtype=complex)) / np.sqrt(3.0)
    states.extend([v2, v3, v4])
    return np.stack(states, axis=1)  # shape (d, m)


def build_sic_projectors(dimension: int) -> SICDesign:
    """Build a SIC-POVM design for given dimension.

    Currently supports d=2 (tetrahedral SIC). For other d, raise NotImplementedError.
    Returns POVM elements E_k with sum_k E_k = I, i.e., E_k = (1/d) |psi_k><psi_k|.
    """
    d = int(dimension)
    if d <= 1:
        raise ValueError("dimension must be >= 2")

    if d == 2:
        vecs = _sic_qubit()  # (2, 4)
        m = vecs.shape[1]
        projectors = []
        weight = 1.0 / d
        for k in range(m):
            v = vecs[:, k]
            P = weight * np.outer(v, v.conj())
            projectors.append(P)
        proj = np.stack(projectors, axis=0)  # (m, d, d)
        groups = np.zeros((m,), dtype=int)  # single-group SIC
        meas = proj.reshape(m, -1)
        return SICDesign(dimension=d, projectors=proj, groups=groups, measurement_matrix=meas)

    raise NotImplementedError("SIC-POVM currently implemented for d=2 only")

