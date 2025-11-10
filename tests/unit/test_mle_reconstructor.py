"""MLEReconstructor 单元测试。"""

import numpy as np
import pytest

from qtomography.domain.density import DensityMatrix
from qtomography.domain.reconstruction.mle import MLEReconstructor


def _random_density(dim: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mat = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    rho = mat @ mat.conj().T
    rho /= np.trace(rho)
    return rho


def _probabilities(projectors: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return np.real(np.einsum('aij,ji->a', projectors, rho, optimize=True))


class TestMLEReconstructorEncoding:
    def test_encode_decode_roundtrip(self):
        dim = 3
        rho = _random_density(dim, seed=123)
        params = MLEReconstructor.encode_density_to_params(rho)
        rho_back = MLEReconstructor.decode_params_to_density(params, dim)
        assert np.allclose(rho_back, rho, atol=1e-10)

    def test_decode_invalid_length(self):
        with pytest.raises(ValueError):
            MLEReconstructor.decode_params_to_density(np.zeros(5), 2)


class TestMLEReconstructorBasics:
    def test_reconstruct_pure_state(self):
        dim = 2
        mle = MLEReconstructor(dim)
        state = np.array([1.0, 0.0], dtype=complex)
        rho_true = np.outer(state, state.conj())
        probs = _probabilities(mle.projector_set.projectors, rho_true)
        density = mle.reconstruct(probs, initial_density=rho_true)
        assert np.allclose(density.matrix, rho_true, atol=1e-8)

    def test_invalid_probabilities_length(self):
        mle = MLEReconstructor(3)
        with pytest.raises(ValueError):
            mle.reconstruct(np.ones(5))


class TestMLEReconstructorAddsNoise:
    def test_random_density_with_noise(self):
        dim = 3
        rng = np.random.default_rng(42)
        mle = MLEReconstructor(dim, tolerance=1e-9, regularization=1e-3)
        rho_true = _random_density(dim, seed=24)
        probs = _probabilities(mle.projector_set.projectors, rho_true)
        noise = rng.normal(scale=1e-3, size=probs.shape)
        noisy_probs = probs + noise
        noisy_probs = np.clip(noisy_probs, 1e-9, None)

        result = mle.reconstruct_with_details(noisy_probs, initial_density=rho_true)
        frob = np.linalg.norm(result.density.matrix - rho_true)
        assert frob < 5e-2
