from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout

from qtomography.domain.density import DensityMatrix
from qtomography.infrastructure.persistence import ResultRepository
from qtomography.infrastructure.persistence.result_repository import ReconstructionRecord
from qtomography.infrastructure.visualization import ReconstructionVisualizer
from qtomography.infrastructure.visualization.qt_adapter import figure_to_png_bytes
from qtomography.gui.widgets.image_viewer import ImageViewer


class _FigureRenderWorker(QtCore.QObject):
    """后台渲染任务：将密度矩阵绘制为位图字节."""

    finished = QtCore.Signal(tuple, bytes, bytes)
    failed = QtCore.Signal(tuple, str)

    def __init__(self, key: tuple[int, str], record: ReconstructionRecord, mode: str) -> None:
        super().__init__()
        self._key = key
        self._record = record
        self._mode = mode

    @QtCore.Slot()
    def run(self) -> None:
        try:
            density = DensityMatrix(self._record.density_matrix)
            metadata = self._record.metadata or {}
            sample_label = metadata.get("sample_index", metadata.get("sample", "?"))
            title = f"Sample {sample_label} - {self._record.method}"
            visualizer = ReconstructionVisualizer()

            if self._mode == FigurePanel.MODE_HEATMAP:
                fig_real, fig_imag = _build_heatmap_figures(density, title)
            else:
                fig_real, fig_imag = visualizer.plot_real_imag_3d(density, title=title)

            real_bytes = figure_to_png_bytes(fig_real, dpi=160)
            plt.close(fig_real)
            imag_bytes = figure_to_png_bytes(fig_imag, dpi=160)
            plt.close(fig_imag)

            self.finished.emit(self._key, real_bytes, imag_bytes)
        except Exception as exc:  # pylint: disable=broad-except
            self.failed.emit(self._key, str(exc))


def _build_heatmap_figures(density: DensityMatrix, title: str) -> tuple[plt.Figure, plt.Figure]:
    """为实部/虚部各生成一张热力图."""

    matrix = density.matrix

    def _make_fig(data, caption: str) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(5, 4))
        im = ax.imshow(data, cmap="RdBu", interpolation="nearest")
        ax.set_title(caption)
        fig.colorbar(im, ax=ax, shrink=0.8)
        fig.suptitle(title, fontsize=10)
        fig.tight_layout()
        return fig

    return _make_fig(matrix.real, "Real part"), _make_fig(matrix.imag, "Imag part")


class FigurePanel(QtWidgets.QWidget):
    """面板：显示重构结果的图像，可选择 3D 柱状或热力图。"""

    MODE_3D = "3d"
    MODE_HEATMAP = "heatmap"

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._records_by_key: Dict[Tuple[int, str], ReconstructionRecord] = {}
        self._render_thread: Optional[QtCore.QThread] = None
        self._render_worker: Optional[_FigureRenderWorker] = None
        self._pending_key: Optional[Tuple[int, str]] = None

        self._build_ui()

    def _build_ui(self) -> None:
        self.sample_combo = QtWidgets.QComboBox()
        self.method_combo = QtWidgets.QComboBox()
        self.display_mode_combo = QtWidgets.QComboBox()
        self.display_mode_combo.addItem("3D 柱状", self.MODE_3D)
        self.display_mode_combo.addItem("热力图", self.MODE_HEATMAP)

        self.sample_combo.currentIndexChanged.connect(self._refresh_figure)
        self.method_combo.currentIndexChanged.connect(self._refresh_figure)
        self.display_mode_combo.currentIndexChanged.connect(self._refresh_figure)

        selector_layout = QtWidgets.QHBoxLayout()
        selector_layout.addWidget(QtWidgets.QLabel("样本:"))
        selector_layout.addWidget(self.sample_combo)
        selector_layout.addSpacing(12)
        selector_layout.addWidget(QtWidgets.QLabel("方法:"))
        selector_layout.addWidget(self.method_combo)
        selector_layout.addSpacing(12)
        selector_layout.addWidget(QtWidgets.QLabel("显示:"))
        selector_layout.addWidget(self.display_mode_combo)
        selector_layout.addStretch(1)

        self.real_viewer = ImageViewer()
        self.real_viewer.setMinimumSize(400, 300)
        self.imag_viewer = ImageViewer()
        self.imag_viewer.setMinimumSize(400, 300)

        real_controls = self._create_controls(self.real_viewer, "实部图")
        imag_controls = self._create_controls(self.imag_viewer, "虚部图")

        images_layout = QtWidgets.QVBoxLayout()
        images_layout.addWidget(QtWidgets.QLabel("实部图"))
        images_layout.addWidget(self.real_viewer, stretch=1)
        images_layout.addLayout(real_controls)
        images_layout.addSpacing(10)
        images_layout.addWidget(QtWidgets.QLabel("虚部图"))
        images_layout.addWidget(self.imag_viewer, stretch=1)
        images_layout.addLayout(imag_controls)

        self.status_label = QtWidgets.QLabel("请选择样本与方法以显示图像。")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(selector_layout)
        layout.addLayout(images_layout)
        layout.addWidget(self.status_label)

    def _create_controls(self, viewer: ImageViewer, title: str) -> QHBoxLayout:
        controls_layout = QHBoxLayout()

        zoom_in_btn = QPushButton("放大")
        zoom_in_btn.clicked.connect(viewer.zoom_in)
        zoom_out_btn = QPushButton("缩小")
        zoom_out_btn.clicked.connect(viewer.zoom_out)
        reset_btn = QPushButton("复位")
        reset_btn.clicked.connect(viewer.reset_view)
        fullscreen_btn = QPushButton("全屏")
        fullscreen_btn.clicked.connect(lambda: self._show_fullscreen(viewer, title))

        controls_layout.addWidget(zoom_in_btn)
        controls_layout.addWidget(zoom_out_btn)
        controls_layout.addWidget(reset_btn)
        controls_layout.addWidget(fullscreen_btn)
        controls_layout.addStretch()
        return controls_layout

    # ------------------------------------------------------------------ Public API
    def clear(self) -> None:
        self._records_by_key.clear()
        self.sample_combo.clear()
        self.method_combo.clear()
        self.real_viewer.set_pixmap(None)
        self.imag_viewer.set_pixmap(None)
        self._set_status("未加载任何记录。")

    def load_from_records(self, records_dir: Path) -> None:
        try:
            repo = ResultRepository(records_dir, fmt="json")
            records = repo.load_all()
        except Exception as exc:  # pylint: disable=broad-except
            QtWidgets.QMessageBox.warning(
                self, "加载记录失败", f"无法读取记录目录 {records_dir}:\n{exc}"
            )
            return

        if not records:
            self.clear()
            return

        self._records_by_key.clear()
        samples: List[str] = []
        methods: List[str] = []

        for record in records:
            sample_index = int(record.metadata.get("sample_index", 0))
            key = (sample_index, record.method)
            self._records_by_key[key] = record
            if record.method not in methods:
                methods.append(record.method)
            label = f"{sample_index}"
            if label not in samples:
                samples.append(label)

        self.sample_combo.blockSignals(True)
        self.method_combo.blockSignals(True)

        self.sample_combo.clear()
        self.sample_combo.addItems(samples)

        self.method_combo.clear()
        self.method_combo.addItems(methods)

        self.sample_combo.blockSignals(False)
        self.method_combo.blockSignals(False)

        self._refresh_figure()

    # ------------------------------------------------------------------ helpers
    def _current_key(self) -> Optional[Tuple[int, str]]:
        if self.sample_combo.currentIndex() < 0 or self.method_combo.currentIndex() < 0:
            return None
        try:
            sample = int(self.sample_combo.currentText())
        except ValueError:
            return None
        method = self.method_combo.currentText()
        return sample, method

    def _current_display_mode(self) -> str:
        return self.display_mode_combo.currentData() or self.MODE_3D

    def _refresh_figure(self) -> None:
        key = self._current_key()
        if key is None or key not in self._records_by_key:
            self.real_viewer.set_pixmap(None)
            self.imag_viewer.set_pixmap(None)
            self._set_status("请选择有效的样本与方法。")
            return

        record = self._records_by_key[key]
        self._start_render_job(key, record)

    def _start_render_job(self, key: Tuple[int, str], record: ReconstructionRecord) -> None:
        self._pending_key = key
        self._set_status("正在渲染图像...", busy=True)
        self._cleanup_render_thread()

        self._render_thread = QtCore.QThread(self)
        self._render_worker = _FigureRenderWorker(key, record, self._current_display_mode())
        self._render_worker.moveToThread(self._render_thread)

        self._render_worker.finished.connect(self._handle_render_finished)
        self._render_worker.failed.connect(self._handle_render_failed)
        self._render_worker.finished.connect(self._render_thread.quit)
        self._render_worker.failed.connect(self._render_thread.quit)
        self._render_thread.finished.connect(self._cleanup_render_thread)

        self._render_thread.started.connect(self._render_worker.run)
        self._render_thread.start()

    def _handle_render_finished(self, key: tuple[int, str], real_bytes: bytes, imag_bytes: bytes) -> None:
        if key != self._current_key():
            return  # 过期结果

        pix_real = QtGui.QPixmap()
        pix_real.loadFromData(real_bytes)
        pix_imag = QtGui.QPixmap()
        pix_imag.loadFromData(imag_bytes)

        self.real_viewer.set_pixmap(pix_real)
        self.imag_viewer.set_pixmap(pix_imag)
        self._set_status("图像渲染完成。")

    def _handle_render_failed(self, key: tuple[int, str], message: str) -> None:  # noqa: ARG002
        self.real_viewer.set_pixmap(None)
        self.imag_viewer.set_pixmap(None)
        self._set_status(f"渲染失败：{message}")

    def _cleanup_render_thread(self) -> None:
        if self._render_thread:
            if self._render_thread.isRunning():
                self._render_thread.quit()
                self._render_thread.wait()
        self._render_thread = None
        self._render_worker = None

    def _set_status(self, message: str, *, busy: bool = False) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("busy", busy)

    def _show_fullscreen(self, viewer: ImageViewer, title: str) -> None:
        pixmap = viewer.current_pixmap()
        if pixmap is None or pixmap.isNull():
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        dialog.showFullScreen()

        fullscreen_viewer = ImageViewer()
        fullscreen_viewer.set_pixmap(pixmap)

        close_btn = QPushButton("退出全屏")
        close_btn.clicked.connect(dialog.close)

        layout = QVBoxLayout(dialog)
        layout.addWidget(fullscreen_viewer, stretch=1)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        dialog.exec()
