"""
pytest配置文件

提供测试用的fixtures和配置
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
import numpy as np
from qtomography.domain.density import DensityMatrix


@pytest.fixture
def simple_2d_matrix():
    """简单的2维密度矩阵"""
    return np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)


@pytest.fixture
def pure_state_matrix():
    """纯态密度矩阵"""
    state_vector = np.array([1, 0], dtype=complex)
    return np.outer(state_vector, state_vector.conj())


@pytest.fixture
def maximally_mixed_2d():
    """2维最大混合态"""
    return np.eye(2) / 2


@pytest.fixture
def non_physical_matrix():
    """不满足物理条件的矩阵"""
    return np.array([[1.5, 0.1], [0.1, -0.3]], dtype=complex)


@pytest.fixture
def complex_matrix():
    """复数密度矩阵"""
    return np.array([[0.5+0.1j, 0.2-0.3j], [0.2+0.3j, 0.5-0.1j]], dtype=complex)


@pytest.fixture
def density_matrix_2d(simple_2d_matrix):
    """2维DensityMatrix实例"""
    return DensityMatrix(simple_2d_matrix)


@pytest.fixture
def density_matrix_pure(pure_state_matrix):
    """纯态DensityMatrix实例"""
    return DensityMatrix(pure_state_matrix)


@pytest.fixture
def density_matrix_mixed(maximally_mixed_2d):
    """最大混合态DensityMatrix实例"""
    return DensityMatrix(maximally_mixed_2d)


# 测试数据生成器
@pytest.fixture
def random_density_matrices():
    """生成随机密度矩阵用于测试"""
    def _generate_random_density_matrix(dim, seed=None):
        if seed is not None:
            np.random.seed(seed)
        
        # 生成随机复数矩阵
        real_part = np.random.randn(dim, dim)
        imag_part = np.random.randn(dim, dim)
        matrix = real_part + 1j * imag_part
        
        # 确保Hermitian性
        matrix = (matrix + matrix.conj().T) / 2
        
        # 归一化
        matrix = matrix / np.trace(matrix)
        
        return DensityMatrix(matrix)
    
    return _generate_random_density_matrix


# 测试参数化数据
@pytest.fixture(params=[2, 3, 4, 5])
def dimension(request):
    """测试不同维度"""
    return request.param


@pytest.fixture(params=[1e-10, 1e-12, 1e-15])
def tolerance(request):
    """测试不同容差"""
    return request.param
