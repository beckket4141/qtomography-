"""ReconstructionVisualizer 单元测试。"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.infrastructure.persistence.result_repository import ReconstructionRecord
from qtomography.infrastructure.visualization.reconstruction_visualizer import ReconstructionVisualizer


def _sample_density():
    matrix = np.array([[0.6, 0.2 - 0.1j], [0.2 + 0.1j, 0.4]], dtype=complex)
    return DensityMatrix(matrix)


def test_plot_density_heatmap(tmp_path):
    vis = ReconstructionVisualizer()
    density = _sample_density()
    fig = vis.plot_density_heatmap(density, title="heatmap")
    fig.savefig(tmp_path / "heatmap.png")
    plt.close(fig)


def test_plot_real_imag_3d(tmp_path):
    vis = ReconstructionVisualizer()
    density = _sample_density()
    fig_real, fig_imag = vis.plot_real_imag_3d(density, title="real-imag-3d")
    fig_real.savefig(tmp_path / "real_imag_3d_real.png")
    fig_imag.savefig(tmp_path / "real_imag_3d_imag.png")
    plt.close(fig_real)
    plt.close(fig_imag)


def test_plot_amplitude_phase(tmp_path):
    vis = ReconstructionVisualizer()
    density = _sample_density()
    fig = vis.plot_amplitude_phase(density, title="amp-phase")
    fig.savefig(tmp_path / "amp_phase.png")
    plt.close(fig)


def test_plot_metric(tmp_path):
    records = [
        ReconstructionRecord(
            method="linear",
            dimension=2,
            probabilities=np.array([0.5, 0.5, 0.25, 0.25]),
            density_matrix=np.eye(2) / 2,
            metrics={"fidelity": 0.95 + 0.01 * i},
            metadata=None,
            timestamp=f"2025-10-07T12:00:0{i}"
        )
        for i in range(3)
    ]
    vis = ReconstructionVisualizer()
    fig = vis.plot_metric(records, metric="fidelity", title="fidelity")
    fig.savefig(tmp_path / "metric.png")
    plt.close(fig)
