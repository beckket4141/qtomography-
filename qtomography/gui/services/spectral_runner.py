"""Batch spectral decomposition service runner."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event
from typing import Optional

import numpy as np
from PySide6 import QtCore

from qtomography.domain.density import DensityMatrix
from qtomography.domain.spectral_decomposition import (
    SpectralDecompositionResult,
    perform_spectral_decomposition,
)
from qtomography.domain.theoretical_state import (
    TheoreticalStateResult,
    generate_theoretical_state,
)
from qtomography.infrastructure.io import load_density_matrix

__all__ = ["SpectralJobConfig", "SpectralRunner"]


@dataclass
class SpectralJobConfig:
    """Configuration for spectral decomposition batch job."""

    files: list[Path]
    output_dir: Optional[Path] = None
    dimension_hint: str = "自动推断"  # "自动推断", "4", "16", etc.
    theory_mode: str = "4D_custom"  # "4D_custom", "16D_custom", "custom"
    custom_coefficients: Optional[list[float]] = None
    custom_phases: Optional[list[float]] = None
    save_plots: bool = True
    save_reports: bool = True
    save_json: bool = False
    figure_format: str = "png"  # "png", "pdf", "svg"
    dpi: int = 100
    verbose: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> SpectralJobConfig:
        """Create config from dictionary (from GUI payload)."""
        files = [Path(f) for f in data.get("files", [])]
        output_dir_str = data.get("output_dir")
        output_dir = Path(output_dir_str) if output_dir_str else None

        return cls(
            files=files,
            output_dir=output_dir,
            dimension_hint=data.get("dimension_hint", "自动推断"),
            theory_mode=data.get("theory_mode", "4D_custom"),
            custom_coefficients=data.get("custom_coefficients"),
            custom_phases=data.get("custom_phases"),
            save_plots=data.get("save_plots", True),
            save_reports=data.get("save_reports", True),
            save_json=data.get("save_json", False),
            figure_format=data.get("figure_format", "png"),
            dpi=data.get("dpi", 100),
            verbose=data.get("verbose", True),
        )


@dataclass
class SpectralResult:
    """Result for a single file spectral decomposition."""

    source_path: Path
    dimension: int
    spectral_result: SpectralDecompositionResult
    theoretical_result: Optional[TheoreticalStateResult] = None
    fidelity: Optional[float] = None
    plot_amplitude_path: Optional[Path] = None
    plot_phase_path: Optional[Path] = None
    report_path: Optional[Path] = None
    json_path: Optional[Path] = None
    error: Optional[str] = None
    processing_time: float = 0.0


class SpectralRunner(QtCore.QObject):
    """Execute batch spectral decomposition in a worker thread."""

    started = QtCore.Signal()
    progress = QtCore.Signal(int, str)  # percent, message
    finished = QtCore.Signal(Path)  # result_dir
    error = QtCore.Signal(str, str)  # path, error_message
    log = QtCore.Signal(str)  # log_message
    cancelled = QtCore.Signal()

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._cancel_event: Optional[Event] = None
        self._worker_thread: Optional[QtCore.QThread] = None
        self._worker: Optional[_SpectralWorker] = None  # Keep reference to prevent garbage collection

    def start(self, config: SpectralJobConfig) -> None:
        """Start batch processing in background thread."""
        if self._worker_thread and self._worker_thread.isRunning():
            raise RuntimeError("已有任务正在执行，请先取消或等待完成。")

        self._cancel_event = Event()
        self.started.emit()

        # Create worker thread
        self._worker_thread = QtCore.QThread()
        self._worker = _SpectralWorker(config, self._cancel_event)
        self._worker.moveToThread(self._worker_thread)

        # Connect signals
        self._worker.progress.connect(self.progress.emit)
        self._worker.log.connect(self.log.emit)
        self._worker.error.connect(self.error.emit)
        self._worker.finished.connect(self._handle_finished)
        self._worker.finished.connect(self._worker_thread.quit)

        # Start thread
        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

    def cancel(self) -> None:
        """Cancel current batch processing."""
        if self._cancel_event:
            self._cancel_event.set()
            self.cancelled.emit()

    def _handle_finished(self, result_dir: Path) -> None:
        """Handle worker completion."""
        self.finished.emit(result_dir)
        if self._worker_thread:
            self._worker_thread.wait()
            self._worker_thread = None
        self._worker = None  # Release worker reference
        self._cancel_event = None


class _SpectralWorker(QtCore.QObject):
    """Worker object that runs in background thread."""

    progress = QtCore.Signal(int, str)
    log = QtCore.Signal(str)
    error = QtCore.Signal(str, str)
    finished = QtCore.Signal(Path)

    def __init__(self, config: SpectralJobConfig, cancel_event: Event) -> None:
        super().__init__()
        self.config = config
        self.cancel_event = cancel_event
        self.logger = logging.getLogger(__name__)

    def run(self) -> None:
        """Execute batch processing."""
        import time

        # Send initial log to confirm worker is running
        self.log.emit("工作线程已启动，开始处理...")
        
        try:
            # Setup output directory
            if self.config.output_dir:
                output_dir = Path(self.config.output_dir)
            else:
                # Default: create timestamped directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = Path.cwd() / "spectral_results" / timestamp

            output_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            reports_dir = output_dir / "reports"
            plots_dir = output_dir / "plots"
            json_dir = output_dir / "json"
            reports_dir.mkdir(exist_ok=True)
            plots_dir.mkdir(exist_ok=True)
            if self.config.save_json:
                json_dir.mkdir(exist_ok=True)

            self.log.emit(f"输出目录: {output_dir}")
            self.log.emit(f"待处理文件数: {len(self.config.files)}")

            results: list[SpectralResult] = []
            total = len(self.config.files)

            for idx, file_path in enumerate(self.config.files):
                if self.cancel_event.is_set():
                    self.log.emit("任务已取消")
                    return

                start_time = time.time()
                self.log.emit(f"[{idx + 1}/{total}] 处理: {file_path.name}")

                try:
                    result = self._process_single_file(
                        file_path, output_dir, reports_dir, plots_dir, json_dir
                    )
                    results.append(result)
                    elapsed = time.time() - start_time
                    self.log.emit(f"  完成 (耗时 {elapsed:.2f}s)")

                except Exception as exc:
                    error_msg = str(exc)
                    self.logger.exception("处理文件失败: %s", file_path)
                    self.error.emit(str(file_path), error_msg)
                    # Create error result with dummy spectral_result
                    dummy_spectral = SpectralDecompositionResult(
                        dimension=0,
                        dominant_eigenvalue=0.0,
                        pure_state_vector=np.array([]),
                        coefficients=np.array([]),
                        amplitudes=np.array([]),
                        phases=np.array([]),
                        eigenvalues=np.array([]),
                    )
                    results.append(
                        SpectralResult(
                            source_path=file_path,
                            dimension=0,
                            spectral_result=dummy_spectral,
                            error=error_msg,
                        )
                    )

                # Update progress
                percent = int((idx + 1) / total * 100)
                self.progress.emit(percent, f"已处理 {idx + 1}/{total} 个文件")

            # Generate summary
            self._write_summary(results, output_dir)

            self.log.emit(f"批处理完成，结果保存在: {output_dir}")
            self.finished.emit(output_dir)

        except Exception as exc:
            error_msg = f"批处理失败: {str(exc)}"
            self.logger.exception("批处理失败")
            self.log.emit(f"错误: {error_msg}")
            self.error.emit("", error_msg)
            self.finished.emit(Path())

    def _process_single_file(
        self,
        file_path: Path,
        output_dir: Path,
        reports_dir: Path,
        plots_dir: Path,
        json_dir: Path,
    ) -> SpectralResult:
        """Process a single density matrix file."""
        import time

        start_time = time.time()

        # Load density matrix
        rho_matrix = load_density_matrix(file_path)
        density = DensityMatrix(rho_matrix, enforce="within_tol", strict=False, warn=False)

        # Determine dimension
        if self.config.dimension_hint == "自动推断":
            dimension = density.dimension
        else:
            dimension = int(self.config.dimension_hint)

        if dimension != density.dimension:
            self.log.emit(
                f"  警告: 维度不匹配 (预期: {dimension}, 实际: {density.dimension})，使用实际维度"
            )
            dimension = density.dimension

        # Perform spectral decomposition
        spectral_result = perform_spectral_decomposition(density)

        # Generate theoretical state
        theory_coeffs = self.config.custom_coefficients
        theory_phases = self.config.custom_phases
        if self.config.theory_mode == "custom" and (theory_coeffs is None or theory_phases is None):
            # Custom mode but no coefficients provided - skip theoretical comparison
            theoretical_result = None
            fidelity = None
        else:
            theoretical_result = generate_theoretical_state(
                dimension,
                self.config.theory_mode,
                coefficients=theory_coeffs,
                phases=theory_phases,
                reference_state=density,
            )
            fidelity = theoretical_result.fidelity

        # Generate plots
        plot_amp_path = None
        plot_phase_path = None
        if self.config.save_plots:
            # Set non-interactive backend for thread safety (must be before importing pyplot)
            import matplotlib
            matplotlib.use("Agg")  # Non-interactive backend
            import matplotlib.pyplot as plt
            
            base_name = file_path.stem
            plot_amp_path = plots_dir / f"{base_name}_amplitude.{self.config.figure_format}"
            plot_phase_path = plots_dir / f"{base_name}_phase.{self.config.figure_format}"

            # Amplitude plot
            fig_amp, ax_amp = plt.subplots(figsize=(6, 4))
            indices = np.arange(1, len(spectral_result.amplitudes) + 1)
            ax_amp.bar(indices, spectral_result.amplitudes, color="#1f77b4", width=0.7)
            ax_amp.set_title("Amplitude (Magnitude)")
            ax_amp.set_xlabel("Coefficient c_i")
            ax_amp.set_ylabel("Magnitude |r|")
            ax_amp.set_xticks(indices)
            ax_amp.set_xticklabels([f"c{i}" for i in indices])
            ax_amp.grid(axis="y", linestyle="--", alpha=0.3)
            fig_amp.tight_layout()
            fig_amp.savefig(plot_amp_path, dpi=self.config.dpi, bbox_inches="tight")
            plt.close(fig_amp)

            # Phase plot
            fig_phase, ax_phase = plt.subplots(figsize=(6, 4))
            phase_values = np.mod(spectral_result.phases, 2 * np.pi)
            ax_phase.bar(indices, phase_values, color="#ff7f0e", width=0.7)
            ax_phase.set_title("Phase")
            ax_phase.set_xlabel("Coefficient c_i")
            ax_phase.set_ylabel("Phase φ (in units of π)")
            ax_phase.set_xticks(indices)
            ax_phase.set_xticklabels([f"c{i}" for i in indices])
            ax_phase.set_ylim(0, 2 * np.pi)
            phase_ticks = [0.0, 0.5 * np.pi, np.pi, 1.5 * np.pi, 2.0 * np.pi]
            phase_labels = ["0", "π/2", "π", "3π/2", "2π"]
            ax_phase.set_yticks(phase_ticks)
            ax_phase.set_yticklabels(phase_labels)
            ax_phase.grid(axis="y", linestyle="--", alpha=0.3)
            fig_phase.tight_layout()
            fig_phase.savefig(plot_phase_path, dpi=self.config.dpi, bbox_inches="tight")
            plt.close(fig_phase)

        # Generate reports
        report_path = None
        if self.config.save_reports:
            from qtomography.infrastructure.persistence.spectral_reporter import (
                write_text_report,
            )

            base_name = file_path.stem
            report_path = reports_dir / f"{base_name}_spectral_report.txt"
            write_text_report(
                SpectralResult(
                    source_path=file_path,
                    dimension=dimension,
                    spectral_result=spectral_result,
                    theoretical_result=theoretical_result,
                    fidelity=fidelity,
                    plot_amplitude_path=plot_amp_path,
                    plot_phase_path=plot_phase_path,
                ),
                report_path,
            )

        # Generate JSON
        json_path = None
        if self.config.save_json:
            from qtomography.infrastructure.persistence.spectral_reporter import (
                write_json_result,
            )

            base_name = file_path.stem
            json_path = json_dir / f"{base_name}.json"
            write_json_result(
                SpectralResult(
                    source_path=file_path,
                    dimension=dimension,
                    spectral_result=spectral_result,
                    theoretical_result=theoretical_result,
                    fidelity=fidelity,
                    plot_amplitude_path=plot_amp_path,
                    plot_phase_path=plot_phase_path,
                ),
                json_path,
            )

        processing_time = time.time() - start_time

        return SpectralResult(
            source_path=file_path,
            dimension=dimension,
            spectral_result=spectral_result,
            theoretical_result=theoretical_result,
            fidelity=fidelity,
            plot_amplitude_path=plot_amp_path,
            plot_phase_path=plot_phase_path,
            report_path=report_path,
            json_path=json_path,
            processing_time=processing_time,
        )

    def _write_summary(self, results: list[SpectralResult], output_dir: Path) -> None:
        """Write summary CSV file."""
        import csv

        summary_path = output_dir / "spectral_summary.csv"
        with summary_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "文件名",
                    "维度",
                    "最大特征值",
                    "保真度",
                    "处理时间(s)",
                    "状态",
                    "报告路径",
                    "图像路径",
                ]
            )

            for result in results:
                if result.error:
                    writer.writerow(
                        [
                            result.source_path.name,
                            "",
                            "",
                            "",
                            f"{result.processing_time:.2f}",
                            f"错误: {result.error}",
                            "",
                            "",
                        ]
                    )
                else:
                    writer.writerow(
                        [
                            result.source_path.name,
                            result.dimension,
                            f"{result.spectral_result.dominant_eigenvalue:.6f}",
                            f"{result.fidelity:.6f}" if result.fidelity else "",
                            f"{result.processing_time:.2f}",
                            "成功",
                            str(result.report_path.relative_to(output_dir))
                            if result.report_path
                            else "",
                            str(result.plot_amplitude_path.relative_to(output_dir))
                            if result.plot_amplitude_path
                            else "",
                        ]
                    )

        self.log.emit(f"汇总文件已保存: {summary_path}")

