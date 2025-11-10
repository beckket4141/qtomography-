import numpy as np
import pytest

from qtomography.domain.density import DensityMatrix
from qtomography.domain.spectral_decomposition import perform_spectral_decomposition
from qtomography.domain.theoretical_state import generate_theoretical_state


def test_perform_spectral_decomposition_pure_state():
    psi = np.array([0.5, 0.5, 0.5, -0.5], dtype=complex)
    rho = np.outer(psi, psi.conj())
    density = DensityMatrix(rho)

    result = perform_spectral_decomposition(density)

    assert result.dimension == 4
    assert pytest.approx(result.dominant_eigenvalue, abs=1e-8) == 1.0
    np.testing.assert_allclose(result.amplitudes, np.full(4, 0.5), atol=1e-8)

    expected_phases = np.array([0.0, 0.0, 0.0, np.pi])
    phase_diff = np.exp(1j * (result.phases - expected_phases))
    np.testing.assert_allclose(phase_diff, np.ones(4), atol=1e-6)


def test_generate_theoretical_state_defaults_and_fidelity():
    base_result = generate_theoretical_state(4, "4D_custom")
    assert base_result.coefficients.shape == (4,)
    assert base_result.phases.shape == (4,)
    assert base_result.measurement_powers.shape == (16,)
    np.testing.assert_allclose(
        np.linalg.norm(base_result.state_vector), 1.0, atol=1e-8
    )

    reference = DensityMatrix(base_result.density_matrix.matrix)
    with_reference = generate_theoretical_state(
        4, "4D_custom", reference_state=reference
    )
    assert with_reference.fidelity == pytest.approx(1.0, abs=1e-8)


def test_generate_theoretical_state_custom_validates_inputs():
    with pytest.raises(ValueError):
        generate_theoretical_state(4, "custom")

    coeffs = [1.0, 0.0, 0.0, 0.0]
    phases = [0.0, 0.0, 0.0, 0.0]
    result = generate_theoretical_state(
        4, "custom", coefficients=coeffs, phases=phases
    )
    np.testing.assert_allclose(result.state_vector, np.array(coeffs, dtype=complex))
