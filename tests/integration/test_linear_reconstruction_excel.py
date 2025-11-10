"""使用 MATLAB 对齐结果校验多个 Excel 列的线性重构。"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import scipy.io as sio

from qtomography.domain.reconstruction.linear import LinearReconstructor


def _compare_excel_with_matlab(excel_path: Path, matlab_path: Path, dimension: int, atol: float) -> None:
    data = pd.read_excel(excel_path, header=None).to_numpy(dtype=float)
    assert data.shape[0] == dimension ** 2, (
        f"Excel {excel_path} 行数 {data.shape[0]} != {dimension**2}"
    )

    mat = sio.loadmat(matlab_path)
    if "results" not in mat:
        raise KeyError(f"MATLAB 文件 {matlab_path} 中未找到 'results'")
    matlab_results = mat["results"].ravel()
    assert len(matlab_results) == data.shape[1], "MATLAB 保存的结果数与 Excel 列数不匹配"

    reconstructor = LinearReconstructor(dimension, tolerance=1e-8)

    for col in range(data.shape[1]):
        probabilities = data[:, col]
        density = reconstructor.reconstruct(probabilities)
        rho_matlab = np.asarray(matlab_results[col], dtype=complex)

        diff = np.linalg.norm(density.matrix - rho_matlab)
        assert diff <= atol, f"列 {col} 差异 {diff} 超出容差 {atol}"


def test_alignment_4d():
    base = Path(__file__).resolve().parents[3]
    excel_path = base / "4维bell.xlsx"
    matlab_path = base / "matlab" / "rho_matlab_alignment_dim4.mat"
    if not excel_path.exists() or not matlab_path.exists():
        pytest.skip("缺少 4 维对齐所需文件")
    _compare_excel_with_matlab(excel_path, matlab_path, dimension=4, atol=2e-2)


def test_alignment_16d():
    base = Path(__file__).resolve().parents[3]
    excel_path = base / "16维bell15913.xlsx"
    matlab_path = base / "matlab" / "rho_matlab_alignment_dim16.mat"
    if not excel_path.exists() or not matlab_path.exists():
        pytest.skip("缺少 16 维对齐所需文件")
    _compare_excel_with_matlab(excel_path, matlab_path, dimension=16, atol=5e-2)
