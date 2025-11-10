"""Report generation for spectral decomposition results."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from qtomography.gui.services.spectral_runner import SpectralResult

__all__ = ["write_text_report", "write_json_result"]


def write_text_report(result: "SpectralResult", output_path: Path) -> None:  # type: ignore
    """Write MATLAB-style text report for spectral decomposition.

    Args:
        result: SpectralResult containing decomposition and theoretical state.
        output_path: Path to save the report.
    """
    spec = result.spectral_result
    theory = result.theoretical_result

    lines = []
    lines.append("=" * 60)
    lines.append("谱分解结果报告")
    lines.append("=" * 60)
    lines.append(f"源文件: {result.source_path.name}")
    lines.append(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Dimension and eigenvalue
    lines.append(f"维度: {result.dimension}")
    lines.append(f"最大特征值: {spec.dominant_eigenvalue:.8f}")
    lines.append("")

    # Pure state vector
    lines.append("纯态向量 (最大特征值对应的本征向量):")
    lines.append("-" * 60)
    for i, (coeff, amp, phase) in enumerate(
        zip(spec.coefficients, spec.amplitudes, spec.phases)
    ):
        real_part = np.real(coeff)
        imag_part = np.imag(coeff)
        lines.append(
            f"  c{i+1} = {real_part:+.6f} {imag_part:+.6f}j  "
            f"(模长: {amp:.6f}, 相位: {phase/np.pi:.4f}π)"
        )
    lines.append("")

    # Theoretical state comparison
    if theory is not None:
        lines.append("理论态对比:")
        lines.append("-" * 60)
        lines.append(f"理论态类型: {theory.state_type}")
        lines.append("理论态系数:")
        for i, (coeff, phase) in enumerate(zip(theory.coefficients, theory.phases)):
            lines.append(f"  c{i+1} = {coeff:.6f}, φ{i+1} = {phase:.4f}π")
        lines.append("")

        if result.fidelity is not None:
            lines.append(f"保真度 (Fidelity): {result.fidelity:.8f}")
            lines.append("")

    # Plot paths
    if result.plot_amplitude_path:
        lines.append(f"振幅图: {result.plot_amplitude_path}")
    if result.plot_phase_path:
        lines.append(f"相位图: {result.plot_phase_path}")
    lines.append("")

    lines.append("=" * 60)

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_json_result(result: "SpectralResult", output_path: Path) -> None:  # type: ignore
    """Write JSON result file for spectral decomposition.

    Args:
        result: SpectralResult containing decomposition and theoretical state.
        output_path: Path to save the JSON file.
    """
    spec = result.spectral_result
    theory = result.theoretical_result

    # Build JSON structure
    data = {
        "source": result.source_path.name,
        "source_path": str(result.source_path),
        "dimension": result.dimension,
        "timestamp": datetime.now().isoformat(),
        "spectral_decomposition": {
            "dominant_eigenvalue": float(spec.dominant_eigenvalue),
            "eigenvalues": spec.eigenvalues.tolist(),
            "pure_state_vector": {
                "real": np.real(spec.pure_state_vector).tolist(),
                "imag": np.imag(spec.pure_state_vector).tolist(),
            },
            "coefficients": {
                "real": np.real(spec.coefficients).tolist(),
                "imag": np.imag(spec.coefficients).tolist(),
            },
            "amplitudes": spec.amplitudes.tolist(),
            "phases": (spec.phases / np.pi).tolist(),  # Convert to units of π
        },
    }

    # Add theoretical state if available
    if theory is not None:
        data["theoretical_state"] = {
            "type": theory.state_type,
            "coefficients": theory.coefficients.tolist(),
            "phases": theory.phases.tolist(),
            "measurement_powers": theory.measurement_powers.tolist(),
        }

    # Add fidelity if available
    if result.fidelity is not None:
        data["fidelity"] = float(result.fidelity)

    # Add plot paths
    if result.plot_amplitude_path or result.plot_phase_path:
        data["plots"] = {}
        if result.plot_amplitude_path:
            data["plots"]["amplitude"] = str(result.plot_amplitude_path)
        if result.plot_phase_path:
            data["plots"]["phase"] = str(result.plot_phase_path)

    # Add report path
    if result.report_path:
        data["report_path"] = str(result.report_path)

    # Add metadata
    data["metadata"] = {
        "processing_time": result.processing_time,
        "error": result.error if result.error else None,
    }

    # Write JSON
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

