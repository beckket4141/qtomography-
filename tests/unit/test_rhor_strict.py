import numpy as np

from qtomography.domain.reconstruction.rhor_strict import RrhoStrictReconstructor
from qtomography.domain.projectors import ProjectorSet
from qtomography.domain.density import DensityMatrix


def simulate_counts_conditional(rho: np.ndarray, projectors: np.ndarray, N: int) -> np.ndarray:
    """Simulate counts from conditional model p_j' = Tr(rho M_j) / Tr(rho H)."""
    p_raw = np.real(np.einsum('aij,ji->a', projectors, rho, optimize=True))
    p_raw = np.clip(p_raw, 0.0, None)
    H = np.sum(projectors, axis=0)
    total = float(np.real(np.trace(rho @ H)))
    if total <= 0:
        raise ValueError("invalid total probability in simulation")
    p = p_raw / total
    p = p / float(np.sum(p))
    return np.random.multinomial(int(N), p)


def random_pure_state(d: int) -> np.ndarray:
    v = np.random.randn(d) + 1j * np.random.randn(d)
    v = v / np.linalg.norm(v)
    return np.outer(v, v.conj())


def test_rhor_strict_nopovm_reconstruction_high_fidelity():
    np.random.seed(7)
    for d in (2, 3):
        ps = ProjectorSet.get(d, design="nopovm")
        rho_true = random_pure_state(d)
        counts = simulate_counts_conditional(rho_true, ps.projectors, N=30000)

        recon = RrhoStrictReconstructor(
            d,
            design="nopovm",
            max_iterations=2000,
            tol_state=5e-9,
            tol_ll=5e-10,
            use_diluted=False,
        )
        result = recon.reconstruct_with_details(counts)

        dm_true = DensityMatrix(rho_true)
        fidelity = dm_true.fidelity(result.density)

        # Expect high fidelity reconstruction
        assert fidelity > 0.97, f"low fidelity for d={d}: {fidelity}"

        # Expected probabilities are valid conditionals
        q = result.expected_probabilities
        assert np.isclose(np.sum(q), 1.0, atol=1e-6)

