"""使用单一案例对齐线性重构结果。"""

from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio

from qtomography.domain.reconstruction.linear import LinearReconstructor


def test_linear_reconstruction_matches_matlab_case():
    base_dir = Path(__file__).resolve().parents[3]
    probs_path = base_dir / "01.csv"
    matlab_path = base_dir / "rho_MATLAB_liner.mat"

    if not probs_path.exists() or not matlab_path.exists():
        pytest.skip("缺少 01.csv 或 rho_MATLAB_liner.mat")

    probabilities = np.loadtxt(probs_path, dtype=float)
    reconstructor = LinearReconstructor(dimension=4, tolerance=1e-9)
    density = reconstructor.reconstruct(probabilities)

    mat_data = sio.loadmat(matlab_path)
    rho_key = next((k for k in mat_data if not k.startswith('_') and mat_data[k].ndim == 2), None)
    if rho_key is None:
        raise KeyError("MATLAB 文件中未找到密度矩阵字段")
    rho_matlab = mat_data[rho_key].astype(complex)

    assert np.allclose(density.matrix, rho_matlab, atol=2e-2)
