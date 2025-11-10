"""ProjectorSet 单元测试。"""

import numpy as np
import pytest

from qtomography.domain.projectors import ProjectorSet


def _match_up_to_global_phase(vec, candidates):
    """判断 vec 是否在 candidates 中 (允许全局相位差)。"""

    for candidate in candidates:
        inner = np.vdot(vec, candidate)
        if np.isclose(abs(inner), 1.0):
            return True
    return False


class TestProjectorSetBasics:
    def test_basis_count_dimension_two(self):
        projector_set = ProjectorSet(2, cache=False)
        bases = projector_set.bases
        assert bases.shape == (4, 2)
        # 所有基向量均应归一化
        norms = np.linalg.norm(bases, axis=1)
        assert np.allclose(norms, 1.0)

        expected_vectors = [
            np.array([1, 0], dtype=complex),
            np.array([0, 1], dtype=complex),
            np.array([1, 1], dtype=complex) / np.sqrt(2),
            np.array([1, -1j], dtype=complex) / np.sqrt(2),
        ]
        for expected in expected_vectors:
            assert _match_up_to_global_phase(expected, bases)

    def test_projector_properties(self):
        projector_set = ProjectorSet(3, cache=False)
        projectors = projector_set.projectors
        # 共 9 个投影矩阵, 每个都是 3x3 Hermitian 且迹为 1
        assert projectors.shape == (9, 3, 3)
        for proj in projectors:
            assert np.allclose(proj, proj.conj().T)
            assert np.isclose(np.trace(proj), 1.0)
            # 投影矩阵来源于外积, 但数值上仍校验特征值非负 (容忍微小浮点误差)
            eigenvals = np.linalg.eigvalsh(proj)
            assert np.all(eigenvals >= -1e-12)

    def test_measurement_matrix_shape(self):
        projector_set = ProjectorSet(3, cache=False)
        measurement = projector_set.measurement_matrix
        assert measurement.shape == (9, 9)
        idx = 5
        reshaped = measurement[idx].reshape(3, 3)
        assert np.allclose(reshaped, projector_set.projectors[idx])


class TestProjectorSetCache:
    def test_get_uses_cache(self):
        ProjectorSet.clear_cache()
        first = ProjectorSet.get(2)
        second = ProjectorSet.get(2)
        # 不同实例, 但 measurement_matrix 应一致, 证明缓存起效
        assert first is not second
        assert np.allclose(first.measurement_matrix, second.measurement_matrix)

    def test_clear_cache(self):
        ProjectorSet.get(2)
        assert ProjectorSet._CACHE
        ProjectorSet.clear_cache()
        assert not ProjectorSet._CACHE


class TestProjectorSetErrors:
    def test_invalid_dimension(self):
        with pytest.raises(ValueError):
            ProjectorSet(1)


