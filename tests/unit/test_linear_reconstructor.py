"""LinearReconstructor 单元测试。"""

import numpy as np
import pytest

from qtomography.domain.reconstruction.linear import (
    LinearReconstructionResult,
    LinearReconstructor,
)
from qtomography.domain.projectors import ProjectorSet


def _density_from_state(state: np.ndarray) -> np.ndarray:
    vec = np.asarray(state, dtype=complex)
    vec = vec / np.linalg.norm(vec)
    return np.outer(vec, vec.conj())


def _probabilities_from_density(projectors: np.ndarray, density: np.ndarray) -> np.ndarray:
    # 观测概率 = Tr(P_i @ rho)
    return np.array([np.real(np.trace(p @ density)) for p in projectors], dtype=float)


class TestLinearReconstructorBasics:
    def test_reconstruct_pure_state(self):
        reconstructor = LinearReconstructor(dimension=2)
        rho_expected = _density_from_state(np.array([1, 0], dtype=complex))
        probs = _probabilities_from_density(reconstructor.projector_set.projectors, rho_expected)

        result = reconstructor.reconstruct_with_details(probs)
        assert isinstance(result, LinearReconstructionResult)
        assert np.allclose(result.density.matrix, rho_expected, atol=1e-10)
        # 残差应接近 0 (完全可解的情形, numpy 会返回空数组)
        if result.residuals.size > 0:
            assert np.all(result.residuals >= -1e-12)
            assert np.all(result.residuals <= 1e-10)

    def test_reconstruct_maximally_mixed(self):
        dim = 3
        reconstructor = LinearReconstructor(dim)
        rho_expected = np.eye(dim, dtype=complex) / dim
        probs = _probabilities_from_density(reconstructor.projector_set.projectors, rho_expected)
        density = reconstructor.reconstruct(probs)
        assert np.allclose(density.matrix, rho_expected, atol=1e-10)

    def test_invalid_length(self):
        reconstructor = LinearReconstructor(2)
        with pytest.raises(ValueError):
            reconstructor.reconstruct([0.5, 0.5, 0.5])  # 长度不为 n²

    def test_zero_normalization_sum(self):
        reconstructor = LinearReconstructor(2)
        with pytest.raises(ValueError):
            reconstructor.reconstruct([0.0, 0.0, 0.1, 0.1])


class TestLinearReconstructorAdvanced:
    def test_random_density_reconstruction(self):
        dim = 2
        rng = np.random.default_rng(42)
        random_matrix = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        rho = random_matrix @ random_matrix.conj().T
        rho /= np.trace(rho)

        reconstructor = LinearReconstructor(dim, tolerance=1e-9)
        probs = _probabilities_from_density(reconstructor.projector_set.projectors, rho)
        rebuilt = reconstructor.reconstruct(probs)
        assert np.allclose(rebuilt.matrix, rho, atol=1e-8)

    def test_regularized_solution(self):
        dim = 2
        reconstructor = LinearReconstructor(dim, regularization=1e-3)
        rho_expected = np.eye(dim, dtype=complex) / dim
        probs = _probabilities_from_density(reconstructor.projector_set.projectors, rho_expected)
        result = reconstructor.reconstruct_with_details(probs)

        # verify residual computed for regularized path
        assert result.residuals.size == 1
        assert result.rank >= dim



