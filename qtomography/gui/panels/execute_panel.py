from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtWidgets


class ExecutePanel(QtWidgets.QWidget):
    """Panel with output directory selection and run/cancel triggers."""

    run_requested = QtCore.Signal()
    cancel_requested = QtCore.Signal()
    open_output_requested = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._output_dir: Optional[Path] = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.output_edit = QtWidgets.QLineEdit()
        self.output_edit.setReadOnly(True)

        browse_btn = QtWidgets.QPushButton("选择输出目录…")
        browse_btn.clicked.connect(self._browse_output)

        open_btn = QtWidgets.QPushButton("打开目录")
        open_btn.clicked.connect(self.open_output_requested)

        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.output_edit)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(open_btn)

        self.run_button = QtWidgets.QPushButton("运行")
        self.run_button.clicked.connect(self.run_requested)

        self.cancel_button = QtWidgets.QPushButton("取消")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_requested)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(path_layout)
        layout.addLayout(button_layout)
        layout.addStretch(1)

    def _browse_output(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.set_output_directory(Path(path))

    def set_output_directory(self, path: Path) -> None:
        self._output_dir = path
        self.output_edit.setText(str(path))

    def output_directory(self) -> Optional[Path]:
        return self._output_dir

    def set_running(self, running: bool) -> None:
        self.run_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)

    # ------------------------------------------------------------------ Configuration
    def save_config(self) -> dict:
        """Save current panel configuration to dictionary."""
        return {
            "output_dir": str(self._output_dir) if self._output_dir else "",
        }

    def load_config(self, config: dict) -> None:
        """Load panel configuration from dictionary."""
        if "output_dir" in config and config["output_dir"]:
            try:
                path = Path(config["output_dir"])
                if path.exists() and path.is_dir():
                    self.set_output_directory(path)
            except Exception:
                pass  # Ignore invalid paths