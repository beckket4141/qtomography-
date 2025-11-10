from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from qtomography.app.controller import ProgressEvent


class ProgressPanel(QtWidgets.QWidget):
    """Display progress updates and log messages."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.stage_label = QtWidgets.QLabel("状态: Idle")
        self.sample_label = QtWidgets.QLabel("样本: --/--")

        header = QtWidgets.QHBoxLayout()
        header.addWidget(self.stage_label)
        header.addSpacing(12)
        header.addWidget(self.sample_label)
        header.addStretch(1)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.progress_bar)
        layout.addLayout(header)
        layout.addWidget(self.log_view)

    def reset(self) -> None:
        self.progress_bar.setValue(0)
        self.stage_label.setText("状态: Idle")
        self.sample_label.setText("样本: --/--")
        self.log_view.clear()

    def update_event(self, event: ProgressEvent) -> None:
        percent = int(event.fraction * 100)
        self.progress_bar.setValue(percent)
        self.stage_label.setText(f"状态: {event.stage}")
        if event.sample_index is not None:
            self.sample_label.setText(
                f"样本: {event.sample_index + 1}/{event.total_samples}"
            )
        else:
            self.sample_label.setText(f"样本: --/{event.total_samples}")

        if event.message:
            self._append_log(event.message)

    def _append_log(self, message: str) -> None:
        cursor = self.log_view.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertText(message + "\n")
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()
