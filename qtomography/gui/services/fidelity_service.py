from __future__ import annotations

"""Utility helpers for GUI-triggered fidelity calculation workflows."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

from qtomography.domain.density import DensityMatrix
from qtomography.domain.theoretical_state import (
    TheoreticalStateResult,
    generate_theoretical_state,
)
from qtomography.infrastructure.io import load_density_matrix

__all__ = [
    "FidelityComputationError",
    "FidelityResult",
    "compute_fidelity_from_files",
    "compute_fidelity_with_custom_state",
]


class FidelityComputationError(RuntimeError):
    """Raised when fidelity computation cannot be completed."""


@dataclass(frozen=True)
class FidelityResult:
    """Container describing the outcome of a fidelity comparison."""

    fidelity: float
    experimental_dimension: int
    theoretical_dimension: int
    theoretical_state: Optional[TheoreticalStateResult] = None
    warnings: Optional[List[str]] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "warnings", list(self.warnings or []))


def _wrap_density(matrix: np.ndarray, *, label: str) -> DensityMatrix:
    try:
        return DensityMatrix(
            matrix,
            enforce="within_tol",
            strict=False,
            warn=False,
        )
    except Exception as exc:  # pylint: disable=broad-except
        raise FidelityComputationError(f"{label} 不是有效的密度矩阵: {exc}") from exc


def _load_density(path: Path, *, label: str) -> DensityMatrix:
    try:
        matrix = load_density_matrix(path)
    except Exception as exc:  # pylint: disable=broad-except
        raise FidelityComputationError(f"无法读取{label}文件: {exc}") from exc
    return _wrap_density(matrix, label=label)


def _validate_amplitudes_and_phases(
    dimension: int,
    amplitudes: Sequence[float],
    phases: Sequence[float],
) -> tuple[np.ndarray, np.ndarray]:
    if len(amplitudes) != dimension or len(phases) != dimension:
        raise FidelityComputationError(
            f"模长与相位数量应与维度 {dimension} 相同 "
            f"(当前模长 {len(amplitudes)} 个, 相位 {len(phases)} 个)."
        )

    amp_array = np.asarray(amplitudes, dtype=float)
    phase_array = np.asarray(phases, dtype=float)

    if np.any(~np.isfinite(amp_array)) or np.any(amp_array < 0):
        raise FidelityComputationError("模长必须是非负实数。")
    if np.any(~np.isfinite(phase_array)):
        raise FidelityComputationError("相位必须是实数。")

    if np.sum(amp_array) == 0:
        raise FidelityComputationError("模长全部为 0，无法构造纯态。")

    return amp_array.tolist(), phase_array.tolist()


def compute_fidelity_from_files(
    experimental_path: Path,
    theoretical_path: Path,
) -> FidelityResult:
    """Compute fidelity from two density-matrix files."""

    experimental_dm = _load_density(experimental_path, label="实验密度矩阵")
    theoretical_dm = _load_density(theoretical_path, label="理论密度矩阵")

    if experimental_dm.dimension != theoretical_dm.dimension:
        raise FidelityComputationError(
            f"维度不匹配：实验态 {experimental_dm.dimension} 维，"
            f"理论态 {theoretical_dm.dimension} 维。"
        )

    fidelity_value = experimental_dm.fidelity(theoretical_dm)

    return FidelityResult(
        fidelity=fidelity_value,
        experimental_dimension=experimental_dm.dimension,
        theoretical_dimension=theoretical_dm.dimension,
        theoretical_state=None,
        warnings=[],
    )


def compute_fidelity_with_custom_state(
    experimental_path: Path,
    dimension: int,
    amplitudes: Sequence[float],
    phases: Sequence[float],
    *,
    projector_design: str = "nopovm",
) -> FidelityResult:
    """Compute fidelity between experimental density matrix and custom pure state."""

    if dimension < 2:
        raise FidelityComputationError("维度必须大于等于 2。")

    experimental_dm = _load_density(experimental_path, label="实验密度矩阵")
    if experimental_dm.dimension != dimension:
        raise FidelityComputationError(
            f"维度不匹配：实验态为 {experimental_dm.dimension} 维，"
            f"自定义纯态设置为 {dimension} 维。"
        )

    amp_list, phase_list = _validate_amplitudes_and_phases(dimension, amplitudes, phases)

    try:
        theoretical_result = generate_theoretical_state(
            dimension,
            "custom",
            coefficients=amp_list,
            phases=phase_list,
            reference_state=experimental_dm,
            projector_design=projector_design,
        )
    except Exception as exc:  # pylint: disable=broad-except
        raise FidelityComputationError(f"无法生成自定义纯态: {exc}") from exc

    if theoretical_result.fidelity is None:
        raise FidelityComputationError("理论纯态生成失败，未返回保真度。")

    return FidelityResult(
        fidelity=float(theoretical_result.fidelity),
        experimental_dimension=experimental_dm.dimension,
        theoretical_dimension=theoretical_result.dimension,
        theoretical_state=theoretical_result,
        warnings=[],
    )


