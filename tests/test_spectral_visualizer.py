import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from qtomography.infrastructure.visualization import (
    plot_amplitude_phase_from_coefficients,
)


def test_plot_amplitude_phase_from_coefficients_shapes():
    amplitudes = [0.5, 0.25, 0.25]
    phases = [0.0, np.pi / 2, np.pi]

    fig = plot_amplitude_phase_from_coefficients(amplitudes, phases, title="demo")
    try:
        assert len(fig.axes) == 2
        amp_bars = fig.axes[0].containers[0]
        heights = [bar.get_height() for bar in amp_bars]
        assert pytest.approx(heights[0], abs=1e-8) == amplitudes[0]
        assert fig.axes[1].get_ylim()[1] >= 2 * np.pi - 1e-8
        assert fig._suptitle.get_text() == "demo"
    finally:
        plt.close(fig)


def test_plot_amplitude_phase_from_coefficients_validates_length():
    with pytest.raises(ValueError):
        plot_amplitude_phase_from_coefficients([0.5, 0.5], [0.1])
