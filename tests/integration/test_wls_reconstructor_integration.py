"""WLS 重构集成测试。"""

import numpy as np

from qtomography.domain.reconstruction.linear import LinearReconstructor
from qtomography.domain.reconstruction.wls import WLSReconstructor


def _random_density(dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    mat = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    rho = mat @ mat.conj().T
    rho /= np.trace(rho)
    return rho


def _probabilities(projectors: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return np.real(np.einsum('aij,ji->a', projectors, rho, optimize=True))


def test_wls_matches_linear_without_noise():
    dim = 3
    rho_true = _random_density(dim, seed=17)

    linear = LinearReconstructor(dim)
    wls = WLSReconstructor(dim)

    probs = _probabilities(linear.projector_set.projectors, rho_true)
    density_linear = linear.reconstruct(probs)
    density_wls = wls.reconstruct(probs, initial_density=rho_true)

    assert np.allclose(density_linear.matrix, rho_true, atol=1e-8)
    assert np.allclose(density_wls.matrix, rho_true, atol=1e-8)


def test_wls_improves_over_linear_with_noise():
    dim = 3
    rng = np.random.default_rng(9)
    rho_true = _random_density(dim, seed=21)

    linear = LinearReconstructor(dim)
    wls = WLSReconstructor(dim, regularization=1e-3)

    probs = _probabilities(linear.projector_set.projectors, rho_true)
    noise = rng.normal(scale=1e-3, size=probs.shape)
    noisy_probs = np.clip(probs + noise, 1e-9, None)

    density_linear = linear.reconstruct(noisy_probs)
    result_wls = wls.reconstruct_with_details(noisy_probs, initial_density=density_linear.matrix)

    frob_linear = np.linalg.norm(density_linear.matrix - rho_true)
    frob_wls = np.linalg.norm(result_wls.density.matrix - rho_true)

    assert frob_wls < 2e-2
    assert frob_linear < 2e-2

