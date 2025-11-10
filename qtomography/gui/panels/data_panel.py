from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtWidgets


class DataPanel(QtWidgets.QWidget):
    """Panel handling dataset selection and basic metadata display."""

    dataset_changed = QtCore.Signal(Path)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._current_file: Optional[Path] = None
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setReadOnly(True)

        self.browse_button = QtWidgets.QPushButton("选择文件…")
        self.browse_button.clicked.connect(self._browse_file)

        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)

        self.info_label = QtWidgets.QLabel("未选择文件。")
        self.info_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(path_layout)
        layout.addWidget(self.info_label)
        layout.addStretch(1)

    # ------------------------------------------------------------------ API
    def _browse_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择测量数据文件",
            "",
            "Data files (*.csv *.xlsx *.xls);;All files (*)",
        )
        if path:
            self.set_file(Path(path))

    def set_file(self, path: Path) -> None:
        self._current_file = path
        self.path_edit.setText(str(path))
        try:
            stat = path.stat()
            info = f"大小: {stat.st_size:,} 字节\n更新时间: {QtCore.QDateTime.fromSecsSinceEpoch(int(stat.st_mtime)).toString()}"
        except OSError:
            info = "无法读取文件信息。"
        self.info_label.setText(info)
        self.dataset_changed.emit(path)

    def current_file(self) -> Optional[Path]:
        return self._current_file

    # ------------------------------------------------------------------ Configuration
    def save_config(self) -> dict:
        """Save current panel configuration to dictionary."""
        return {
            "last_file": str(self._current_file) if self._current_file else "",
        }

    def load_config(self, config: dict) -> None:
        """Load panel configuration from dictionary."""
        if "last_file" in config and config["last_file"]:
            try:
                path = Path(config["last_file"])
                if path.exists() and path.is_file():
                    self.set_file(path)
            except Exception:
                pass  # Ignore invalid paths
