"""LinearReconstructor 集成测试。"""

import numpy as np

from qtomography.domain.reconstruction.linear import LinearReconstructor


def _random_density(dim: int, rng: np.random.Generator) -> np.ndarray:
    mat = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
    rho = mat @ mat.conj().T
    return rho / np.trace(rho)


def _probabilities(recon: LinearReconstructor, rho: np.ndarray) -> np.ndarray:
    return np.array([
        np.real(np.trace(projector @ rho))
        for projector in recon.projector_set.projectors
    ])


def test_linear_reconstruction_pipeline_multiple_states():
    dim = 3
    rng = np.random.default_rng(123)
    reconstructor = LinearReconstructor(dim, tolerance=1e-9)

    for _ in range(5):
        rho = _random_density(dim, rng)
        probs = _probabilities(reconstructor, rho)
        density = reconstructor.reconstruct(probs)
        assert np.allclose(density.matrix, rho, atol=5e-8)


def test_linear_reconstruction_with_caching():
    dim = 2
    recon_a = LinearReconstructor(dim)
    recon_b = LinearReconstructor(dim)

    rho = np.eye(dim, dtype=complex) / dim
    probs = _probabilities(recon_a, rho)

    density_a = recon_a.reconstruct(probs)
    density_b = recon_b.reconstruct(probs)
    assert np.allclose(density_a.matrix, density_b.matrix, atol=1e-10)
