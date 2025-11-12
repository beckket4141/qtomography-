from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from qtomography.gui.services.fidelity_service import (
    FidelityComputationError,
    compute_fidelity_from_files,
    compute_fidelity_with_custom_state,
)


def _write_density_json(path: Path, matrix: np.ndarray) -> None:
    payload = {
        "density_matrix": {
            "real": matrix.real.tolist(),
            "imag": matrix.imag.tolist(),
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_compute_fidelity_from_files(tmp_path: Path) -> None:
    rho = np.array([[1, 0], [0, 0]], dtype=complex)
    experimental_file = tmp_path / "exp.json"
    theory_file = tmp_path / "th.json"
    _write_density_json(experimental_file, rho)
    _write_density_json(theory_file, rho)

    result = compute_fidelity_from_files(experimental_file, theory_file)

    assert pytest.approx(result.fidelity, abs=1e-8) == 1.0
    assert result.experimental_dimension == 2
    assert result.theoretical_dimension == 2


def test_compute_fidelity_with_custom_state(tmp_path: Path) -> None:
    rho = np.array([[1, 0], [0, 0]], dtype=complex)
    experimental_file = tmp_path / "exp.json"
    _write_density_json(experimental_file, rho)

    result = compute_fidelity_with_custom_state(
        experimental_file,
        dimension=2,
        amplitudes=[1.0, 0.0],
        phases=[0.0, 0.0],
    )

    assert pytest.approx(result.fidelity, abs=1e-8) == 1.0
    assert result.experimental_dimension == 2
    assert result.theoretical_dimension == 2
    assert result.theoretical_state is not None


def test_compute_fidelity_dimension_mismatch(tmp_path: Path) -> None:
    rho2 = np.eye(2, dtype=complex) / 2
    rho4 = np.eye(4, dtype=complex) / 4
    experimental_file = tmp_path / "exp.json"
    theory_file = tmp_path / "th.json"
    _write_density_json(experimental_file, rho2)
    _write_density_json(theory_file, rho4)

    with pytest.raises(FidelityComputationError):
        compute_fidelity_from_files(experimental_file, theory_file)


def test_compute_fidelity_custom_invalid_amplitudes(tmp_path: Path) -> None:
    rho = np.eye(2, dtype=complex) / 2
    experimental_file = tmp_path / "exp.json"
    _write_density_json(experimental_file, rho)

    with pytest.raises(FidelityComputationError):
        compute_fidelity_with_custom_state(
            experimental_file,
            dimension=2,
            amplitudes=[0.0],  # wrong length
            phases=[0.0, 0.0],
        )


