from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6 import QtCore, QtWidgets


class SpectralDecompositionPanel(QtWidgets.QWidget):
    """Batch spectral decomposition workflow panel."""

    start_requested = QtCore.Signal(dict)
    cancel_requested = QtCore.Signal()

    SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".mat", ".json")

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._current_dir: Optional[Path] = None
        self._is_running = False
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.folder_edit = QtWidgets.QLineEdit()
        self.folder_edit.setReadOnly(True)
        browse_button = QtWidgets.QPushButton("浏览文件夹")
        browse_button.clicked.connect(self._browse_folder)

        folder_row = QtWidgets.QHBoxLayout()
        folder_row.addWidget(self.folder_edit)
        folder_row.addWidget(browse_button)

        self.file_list = QtWidgets.QListWidget()
        self.file_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

        select_buttons = QtWidgets.QHBoxLayout()
        select_all_btn = QtWidgets.QPushButton("全选")
        select_all_btn.clicked.connect(self.file_list.selectAll)
        select_none_btn = QtWidgets.QPushButton("清除选择")
        select_none_btn.clicked.connect(self.file_list.clearSelection)
        refresh_btn = QtWidgets.QPushButton("刷新列表")
        refresh_btn.clicked.connect(self._refresh_file_list)
        select_buttons.addWidget(select_all_btn)
        select_buttons.addWidget(select_none_btn)
        select_buttons.addStretch(1)
        select_buttons.addWidget(refresh_btn)

        file_group = QtWidgets.QGroupBox("待处理文件（支持 .mat/.csv/.xlsx/.xls）")
        file_layout = QtWidgets.QVBoxLayout(file_group)
        file_layout.addWidget(self.file_list)
        file_layout.addLayout(select_buttons)

        self.save_plots_checkbox = QtWidgets.QCheckBox("保存振幅/相位图")
        self.save_reports_checkbox = QtWidgets.QCheckBox("保存文本报告")
        self.save_json_checkbox = QtWidgets.QCheckBox("保存 JSON 结果")
        self.save_plots_checkbox.setChecked(True)
        self.save_reports_checkbox.setChecked(True)

        self.figure_format_combo = QtWidgets.QComboBox()
        self.figure_format_combo.addItems(["png", "pdf", "svg"])

        self.dimension_combo = QtWidgets.QComboBox()
        self.dimension_combo.addItems(["自动推断", "4", "16"])

        self.theory_mode_combo = QtWidgets.QComboBox()
        self.theory_mode_combo.addItems(["4D_custom", "16D_custom", "custom"])
        self.theory_mode_combo.setCurrentText("4D_custom")

        options_form = QtWidgets.QFormLayout()
        options_form.addRow("预期维度", self.dimension_combo)
        options_form.addRow("理论态模板", self.theory_mode_combo)
        options_form.addRow("图像格式", self.figure_format_combo)

        options_group = QtWidgets.QGroupBox("处理选项")
        options_layout = QtWidgets.QVBoxLayout(options_group)
        options_layout.addWidget(self.save_plots_checkbox)
        options_layout.addWidget(self.save_reports_checkbox)
        options_layout.addWidget(self.save_json_checkbox)
        options_layout.addLayout(options_form)

        self.output_edit = QtWidgets.QLineEdit()
        self.output_edit.setPlaceholderText("默认存放在输入目录下的 spectral_results")
        output_button = QtWidgets.QPushButton("输出目录")
        output_button.clicked.connect(self._choose_output_dir)

        output_row = QtWidgets.QHBoxLayout()
        output_row.addWidget(self.output_edit)
        output_row.addWidget(output_button)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)

        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("执行日志将在此处显示……")

        control_row = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("开始处理")
        self.start_button.clicked.connect(self._emit_start)
        self.cancel_button = QtWidgets.QPushButton("停止")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        control_row.addWidget(self.start_button)
        control_row.addWidget(self.cancel_button)
        control_row.addStretch(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(folder_row)
        layout.addWidget(file_group)
        layout.addWidget(options_group)
        layout.addLayout(output_row)
        layout.addLayout(control_row)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_view)

    # ------------------------------------------------------------------ Slots
    def _browse_folder(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "选择包含密度矩阵的文件夹")
        if directory:
            self.set_directory(Path(directory))

    def _choose_output_dir(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_edit.setText(directory)

    def _refresh_file_list(self) -> None:
        self.file_list.clear()
        if not self._current_dir or not self._current_dir.exists():
            return

        files = [
            path for path in self._current_dir.iterdir()
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]
        files.sort()

        for path in files:
            item = QtWidgets.QListWidgetItem(path.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, str(path))
            self.file_list.addItem(item)

    def _emit_start(self) -> None:
        if not self.selected_files():
            QtWidgets.QMessageBox.warning(self, "谱分解", "请选择至少一个待处理文件。")
            return
        payload = {
            "files": [str(p) for p in self.selected_files()],
            "save_plots": self.save_plots_checkbox.isChecked(),
            "save_reports": self.save_reports_checkbox.isChecked(),
            "save_json": self.save_json_checkbox.isChecked(),
            "figure_format": self.figure_format_combo.currentText(),
            "dimension_hint": self.dimension_combo.currentText(),
            "theory_mode": self.theory_mode_combo.currentText(),
            "output_dir": self.output_edit.text().strip() or None,
        }
        self.start_requested.emit(payload)

    # ------------------------------------------------------------------ API
    def set_directory(self, path: Path) -> None:
        self._current_dir = path
        self.folder_edit.setText(str(path))
        self._refresh_file_list()

    def selected_files(self) -> List[Path]:
        selection = self.file_list.selectedItems()
        paths: List[Path] = []
        for item in selection:
            raw = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if raw:
                paths.append(Path(raw))
        return paths

    def set_running(self, running: bool) -> None:
        self._is_running = running
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.file_list.setEnabled(not running)

    def append_log(self, message: str) -> None:
        self.log_view.append(message)

    def reset_progress(self) -> None:
        self.progress_bar.setValue(0)

    def update_progress(self, percent: int, message: str = "") -> None:
        self.progress_bar.setValue(percent)
        if message:
            self.append_log(message)

    # ------------------------------------------------------------------ Configuration
    def save_config(self) -> dict:
        """Save current panel configuration to dictionary."""
        return {
            "folder_path": str(self._current_dir) if self._current_dir else "",
            "output_dir": self.output_edit.text().strip(),
            "dimension_hint": self.dimension_combo.currentText(),
            "theory_mode": self.theory_mode_combo.currentText(),
            "figure_format": self.figure_format_combo.currentText(),
            "save_plots": self.save_plots_checkbox.isChecked(),
            "save_reports": self.save_reports_checkbox.isChecked(),
            "save_json": self.save_json_checkbox.isChecked(),
        }

    def load_config(self, config: dict) -> None:
        """Load panel configuration from dictionary."""
        if "folder_path" in config and config["folder_path"]:
            try:
                path = Path(config["folder_path"])
                if path.exists() and path.is_dir():
                    self.set_directory(path)
            except Exception:
                pass  # Ignore invalid paths

        if "output_dir" in config and config["output_dir"]:
            self.output_edit.setText(config["output_dir"])

        if "dimension_hint" in config:
            index = self.dimension_combo.findText(config["dimension_hint"])
            if index >= 0:
                self.dimension_combo.setCurrentIndex(index)

        if "theory_mode" in config:
            index = self.theory_mode_combo.findText(config["theory_mode"])
            if index >= 0:
                self.theory_mode_combo.setCurrentIndex(index)

        if "figure_format" in config:
            index = self.figure_format_combo.findText(config["figure_format"])
            if index >= 0:
                self.figure_format_combo.setCurrentIndex(index)

        if "save_plots" in config:
            self.save_plots_checkbox.setChecked(config["save_plots"])

        if "save_reports" in config:
            self.save_reports_checkbox.setChecked(config["save_reports"])

        if "save_json" in config:
            self.save_json_checkbox.setChecked(config["save_json"])
