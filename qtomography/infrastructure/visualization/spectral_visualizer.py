from __future__ import annotations

"""Amplitude/phase plotting helpers for spectral decomposition results."""

from typing import Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np

__all__ = ["plot_amplitude_phase_from_coefficients"]

_PHASE_TICKS: Tuple[float, ...] = (
    0.0,
    0.5 * np.pi,
    np.pi,
    1.5 * np.pi,
    2.0 * np.pi,
)
_PHASE_TICK_LABELS: Tuple[str, ...] = ("0", "1/2π", "π", "3/2π", "2π")


def plot_amplitude_phase_from_coefficients(
    amplitudes: Sequence[float],
    phases: Sequence[float],
    *,
    title: str = "",
    wrap_phase: bool = True,
) -> plt.Figure:
    """Render MATLAB-style amplitude/phase bar plots based on coefficients."""

    amp = np.asarray(amplitudes, dtype=float)
    phi = np.asarray(phases, dtype=float)
    if amp.shape != phi.shape:
        raise ValueError("Amplitude and phase arrays must have the same length.")
    if amp.ndim != 1:
        raise ValueError("Amplitude/phase inputs must be 1-D sequences.")

    phase_values = np.mod(phi, 2 * np.pi) if wrap_phase else phi
    indices = np.arange(1, amp.size + 1)
    xtick_labels = [f"c{i}" for i in indices]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].bar(indices, amp, color="#1f77b4", width=0.7)
    axes[0].set_title("模长（振幅图）")
    axes[0].set_xlabel("系数 c_i")
    axes[0].set_ylabel("模长 r")
    axes[0].set_xticks(indices)
    axes[0].set_xticklabels(xtick_labels)
    axes[0].grid(axis="y", linestyle="--", alpha=0.3)

    axes[1].bar(indices, phase_values, color="#ff7f0e", width=0.7)
    axes[1].set_title("相位图")
    axes[1].set_xlabel("系数 c_i")
    axes[1].set_ylabel("相位 φ（单位 π）")
    axes[1].set_xticks(indices)
    axes[1].set_xticklabels(xtick_labels)
    axes[1].set_ylim(0, 2 * np.pi if wrap_phase else None)
    axes[1].set_yticks(_PHASE_TICKS)
    axes[1].set_yticklabels(_PHASE_TICK_LABELS)
    axes[1].grid(axis="y", linestyle="--", alpha=0.3)

    if title:
        fig.suptitle(title)
    fig.tight_layout()
    return fig
