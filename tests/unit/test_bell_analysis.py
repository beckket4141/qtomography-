import numpy as np
import pytest

from qtomography.analysis.bell import (
    BellAnalysisResult,
    analyze_density_matrix,
    analyze_record,
    analyze_records,
    generate_generalized_bell_states,
)
from qtomography.domain.density import DensityMatrix
from qtomography.infrastructure.persistence.result_repository import ReconstructionRecord


def _pure_bell_density(local_dim: int, index: int = 0) -> np.ndarray:
    states = generate_generalized_bell_states(local_dim)
    psi = states[index]
    return np.outer(psi, psi.conj())


def test_generate_generalized_bell_states_orthonormal():
    states = generate_generalized_bell_states(3)
    assert len(states) == 9
    # Orthonormality check
    for i, psi in enumerate(states):
        assert np.isclose(np.vdot(psi, psi), 1.0)
        for j in range(i + 1, len(states)):
            assert np.isclose(np.vdot(psi, states[j]), 0.0)


def test_analyze_density_matrix_matches_pure_state():
    rho = _pure_bell_density(2, index=0)
    result = analyze_density_matrix(rho)
    assert isinstance(result, BellAnalysisResult)
    assert result.local_dimension == 2
    assert pytest.approx(result.fidelities[0], rel=1e-12) == 1.0
    assert result.to_dict()["dominant_index"] == 0


def test_analyze_record_and_aggregate():
    rho = _pure_bell_density(2, index=1)
    record = ReconstructionRecord(
        method="linear",
        dimension=4,
        probabilities=np.full(16, 1/16),
        density_matrix=rho,
        metrics={},
        metadata={"sample_index": 0},
    )
    result = analyze_record(record)
    assert pytest.approx(result.fidelities[1], rel=1e-12) == 1.0

    df = analyze_records([record])
    assert "bell_max_fidelity" in df.columns
    assert pytest.approx(df.loc[0, "bell_max_fidelity"], rel=1e-12) == 1.0


def test_analyze_density_matrix_rejects_non_square():
    with pytest.raises(ValueError):
        analyze_density_matrix(np.array([1, 0, 0]))


def test_generate_generalized_bell_states_invalid_dimension():
    with pytest.raises(ValueError):
        generate_generalized_bell_states(1)
