"""Load density matrices from various file formats."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    import scipy.io as sio
except ImportError:
    sio = None

__all__ = ["load_density_matrix"]


def _load_from_json(path: Path) -> np.ndarray:
    """Load density matrix from JSON file (ReconstructionRecord format)."""
    import json

    data = json.loads(path.read_text(encoding="utf-8"))

    # Check if it's a ReconstructionRecord format
    if "density_matrix" in data and isinstance(data["density_matrix"], dict):
        # ReconstructionRecord format: {real: [...], imag: [...]}
        real_part = np.array(data["density_matrix"]["real"], dtype=float)
        imag_part = np.array(data["density_matrix"]["imag"], dtype=float)
        matrix = real_part + 1j * imag_part
    elif "density_matrix" in data and isinstance(data["density_matrix"], list):
        # Direct matrix format (list of lists)
        matrix = np.array(data["density_matrix"], dtype=complex)
    else:
        raise ValueError(
            f"JSON file does not contain a valid density_matrix field. "
            f"Expected format: {{'density_matrix': {{'real': [...], 'imag': [...]}}}} "
            f"or {{'density_matrix': [[...], [...]]}}"
        )

    if matrix.ndim != 2:
        raise ValueError(f"Density matrix must be 2D, got shape: {matrix.shape}")

    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(
            f"Density matrix must be square, got shape: {matrix.shape}. "
            f"Expected: ({matrix.shape[0]}, {matrix.shape[0]})"
        )

    return matrix


def load_density_matrix(
    path: Path,
    *,
    sheet: Optional[str | int] = None,
    variable_names: Optional[list[str]] = None,
) -> np.ndarray:
    """Load a density matrix from file.

    Supports multiple formats:
    - JSON (.json): Reads from ReconstructionRecord format (density_matrix.real/imag)
    - MATLAB (.mat): Automatically detects density matrix variable
    - CSV/TXT (.csv, .txt): Reads as square matrix
    - Excel (.xlsx, .xls): Reads from specified sheet

    Args:
        path: File path to load.
        sheet: Sheet name or index for Excel files (None = first sheet).
        variable_names: Preferred variable names for .mat files.
            Default: ["rho_final", "rho", "density_matrix", "rho_matrix"]

    Returns:
        Complex density matrix as numpy array (shape: [d, d]).

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file format is unsupported or matrix is invalid.
        ImportError: If scipy is required but not installed (for .mat files).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Density matrix file not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".json":
        return _load_from_json(path)
    elif suffix == ".mat":
        return _load_from_mat(path, variable_names=variable_names)
    elif suffix in {".csv", ".txt"}:
        return _load_from_csv(path)
    elif suffix in {".xlsx", ".xls"}:
        return _load_from_excel(path, sheet=sheet)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _load_from_mat(
    path: Path,
    *,
    variable_names: Optional[list[str]] = None,
) -> np.ndarray:
    """Load density matrix from MATLAB .mat file."""
    if sio is None:
        raise ImportError(
            "scipy is required to load .mat files. "
            "Install with: pip install scipy"
        )

    mat_data = sio.loadmat(str(path))

    # Default variable names to search
    if variable_names is None:
        variable_names = ["rho_final", "rho", "density_matrix", "rho_matrix"]

    # Try preferred names first
    for name in variable_names:
        if name in mat_data:
            arr = np.asarray(mat_data[name])
            if arr.ndim == 2 and arr.shape[0] == arr.shape[1]:
                return arr.astype(complex)

    # Search for any 2D square matrix (skip metadata starting with '_')
    for key, value in mat_data.items():
        if key.startswith("_"):
            continue
        arr = np.asarray(value)
        if arr.ndim == 2 and arr.shape[0] == arr.shape[1]:
            return arr.astype(complex)

    raise ValueError(
        f"No valid density matrix found in {path}. "
        f"Expected a square 2D array in one of: {variable_names}"
    )


def _load_from_csv(path: Path) -> np.ndarray:
    """Load density matrix from CSV file."""
    frame = pd.read_csv(path, header=None)

    # Remove rows/columns that are all NaN
    frame = frame.dropna(how="all").dropna(axis=1, how="all")

    data = frame.to_numpy(dtype=complex)

    if data.ndim != 2:
        raise ValueError(f"CSV file must contain a 2D matrix, got shape: {data.shape}")

    if data.shape[0] != data.shape[1]:
        raise ValueError(
            f"Density matrix must be square, got shape: {data.shape}. "
            f"Expected: ({data.shape[0]}, {data.shape[0]})"
        )

    return data


def _load_from_excel(
    path: Path,
    *,
    sheet: Optional[str | int] = None,
) -> np.ndarray:
    """Load density matrix from Excel file."""
    frame = pd.read_excel(path, sheet_name=sheet, header=None)

    # If multiple sheets returned, use first
    if isinstance(frame, dict):
        frame = list(frame.values())[0]

    # Remove rows/columns that are all NaN
    frame = frame.dropna(how="all").dropna(axis=1, how="all")

    data = frame.to_numpy(dtype=complex)

    if data.ndim != 2:
        raise ValueError(f"Excel file must contain a 2D matrix, got shape: {data.shape}")

    if data.shape[0] != data.shape[1]:
        raise ValueError(
            f"Density matrix must be square, got shape: {data.shape}. "
            f"Expected: ({data.shape[0]}, {data.shape[0]})"
        )

    return data

