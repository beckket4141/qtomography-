"""
Utility helpers for exporting reconstruction figures to disk.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt

from qtomography.domain.density import DensityMatrix
from qtomography.infrastructure.persistence.result_repository import ReconstructionRecord

from .reconstruction_visualizer import ReconstructionVisualizer

__all__ = ["save_density_heatmap"]


def save_density_heatmap(
    record: ReconstructionRecord,
    path: Path,
    *,
    title: Optional[str] = None,
    dpi: int = 300,
) -> tuple[Path, Path]:
    """
    Render and save density matrix visualization figures for *record*.
    
    Saves two separate figures: real part and imaginary part (3D bar charts).

    Parameters
    ----------
    record:
        A reconstruction record containing the complex density matrix.
    path:
        Base file path (PNG recommended). Will be extended with "_Real.png" and "_Imag.png".
        Parent directories are created automatically.
    title:
        Optional figure title. Defaults to ``Sample {index} - {method}``.
    dpi:
        Matplotlib DPI used when saving the figure. Default is 300 for high quality.

    Returns
    -------
    (real_path, imag_path): Paths to the saved real and imaginary part figures.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    metadata = record.metadata or {}
    sample_label = metadata.get("sample_index", metadata.get("sample", "?"))
    default_title = f"Sample {sample_label} - {record.method}"

    density = DensityMatrix(record.density_matrix)
    visualizer = ReconstructionVisualizer()
    
    # Get two separate figures
    fig_real, fig_imag = visualizer.plot_real_imag_3d(density, title=title or default_title)
    
    # Generate file paths
    path_stem = path.stem
    path_suffix = path.suffix or ".png"
    path_parent = path.parent
    
    real_path = path_parent / f"{path_stem}_Real{path_suffix}"
    imag_path = path_parent / f"{path_stem}_Imag{path_suffix}"
    
    # Save both figures
    fig_real.savefig(real_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig_real)
    
    fig_imag.savefig(imag_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig_imag)
    
    return real_path, imag_path

