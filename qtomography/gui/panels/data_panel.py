from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Optional, Union

from PySide6 import QtCore, QtWidgets

from qtomography.app.controller import (
    _load_probabilities,
    get_empty_columns,
    get_valid_columns,
)

SheetAccessor = Callable[[], Optional[Union[str, int]]]


class DataPanel(QtWidgets.QWidget):
    """Panel handling dataset selection and column-range configuration."""

    dataset_changed = QtCore.Signal(Path)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._current_file: Optional[Path] = None
        self._sheet_accessor: Optional[SheetAccessor] = None
        self._column_stats: Optional[Dict[str, Union[int, list[int]]]] = None
        self._analysis_timer = QtCore.QTimer(self)
        self._analysis_timer.setSingleShot(True)
        self._analysis_timer.timeout.connect(self._analyze_file)
        self._range_valid = True

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
        layout.addWidget(self._build_column_card())
        layout.addStretch(1)

    def _build_column_card(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("数据列信息")
        group_layout = QtWidgets.QVBoxLayout(group)

        self.column_info_label = QtWidgets.QLabel("尚未分析列信息。")
        self.column_info_label.setWordWrap(True)
        self.column_empty_label = QtWidgets.QLabel("")
        self.column_empty_label.setStyleSheet("color: #6c6c6c;")

        group_layout.addWidget(self.column_info_label)
        group_layout.addWidget(self.column_empty_label)

        self.columns_all_radio = QtWidgets.QRadioButton("处理所有列")
        self.columns_custom_radio = QtWidgets.QRadioButton("自定义列范围")
        self.columns_all_radio.setChecked(True)

        mode_layout = QtWidgets.QHBoxLayout()
        mode_layout.addWidget(self.columns_all_radio)
        mode_layout.addWidget(self.columns_custom_radio)
        mode_layout.addStretch(1)
        group_layout.addLayout(mode_layout)

        self.columns_all_radio.toggled.connect(self._update_range_enabled)
        self.columns_custom_radio.toggled.connect(self._update_range_enabled)

        self.range_container = QtWidgets.QWidget()
        range_container_layout = QtWidgets.QVBoxLayout(self.range_container)
        range_container_layout.setContentsMargins(0, 0, 0, 0)

        range_layout = QtWidgets.QHBoxLayout()
        range_layout.addWidget(QtWidgets.QLabel("从"))
        self.from_col_spin = QtWidgets.QSpinBox()
        self.from_col_spin.setRange(1, 1)
        range_layout.addWidget(self.from_col_spin)
        range_layout.addWidget(QtWidgets.QLabel("列 到"))
        self.to_col_spin = QtWidgets.QSpinBox()
        self.to_col_spin.setRange(1, 1)
        range_layout.addWidget(self.to_col_spin)
        range_layout.addWidget(QtWidgets.QLabel("列"))
        range_layout.addStretch(1)

        self.from_col_spin.valueChanged.connect(self._validate_range)
        self.to_col_spin.valueChanged.connect(self._validate_range)

        self.range_hint_label = QtWidgets.QLabel("ⓘ 输入相同数字表示只处理单列。")
        self.range_hint_label.setStyleSheet("color: #6c6c6c; font-size: 11px;")
        self.range_error_label = QtWidgets.QLabel("")
        self.range_error_label.setStyleSheet("color: #b3261e; font-size: 11px;")
        self.range_error_label.setVisible(False)

        range_container_layout.addLayout(range_layout)
        range_container_layout.addWidget(self.range_hint_label)
        range_container_layout.addWidget(self.range_error_label)

        group_layout.addWidget(self.range_container)
        self._update_range_enabled()
        return group

    # ------------------------------------------------------------------ API
    def set_sheet_accessor(self, accessor: SheetAccessor) -> None:
        """Allow the panel to query the latest sheet selection from ConfigPanel."""
        self._sheet_accessor = accessor

    def notify_sheet_changed(self) -> None:
        """Request re-analysis when the sheet input changes."""
        if self._current_file is None:
            return
        self._schedule_analysis()

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
            timestamp = QtCore.QDateTime.fromSecsSinceEpoch(int(stat.st_mtime)).toString()
            info = f"大小: {stat.st_size:,} 字节\n更新时间: {timestamp}"
        except OSError:
            info = "无法读取文件信息。"
        self.info_label.setText(info)
        self._schedule_analysis(delay_ms=0)
        self.dataset_changed.emit(path)

    def current_file(self) -> Optional[Path]:
        return self._current_file

    def build_dataset_options(self) -> Dict[str, Optional[tuple[int, int]]]:
        """Return dataset-related kwargs for ReconstructionConfig."""
        if not self.columns_custom_radio.isChecked():
            return {}
        if not self._column_stats:
            raise ValueError("列信息尚未加载，无法自定义列范围。")
        if not self._validate_range():
            message = self.range_error_label.text().strip() or "列范围无效。"
            raise ValueError(message)
        start = self.from_col_spin.value()
        end = self.to_col_spin.value()
        return {"column_range": (start, end)}

    # ------------------------------------------------------------------ Configuration persistence
    def save_config(self) -> dict:
        """Save current panel configuration to dictionary."""
        return {
            "last_file": str(self._current_file) if self._current_file else "",
            "selection_mode": "range" if self.columns_custom_radio.isChecked() else "all",
            "column_from": self.from_col_spin.value(),
            "column_to": self.to_col_spin.value(),
        }

    def load_config(self, config: dict) -> None:
        """Load panel configuration from dictionary."""
        selection_mode = str(config.get("selection_mode", "all")).lower()
        start = self._coerce_positive_int(config.get("column_from"), default=1)
        end = self._coerce_positive_int(config.get("column_to"), default=start)
        self._set_spin_value(self.from_col_spin, start)
        self._set_spin_value(self.to_col_spin, end)
        if selection_mode == "range":
            self.columns_custom_radio.setChecked(True)
        else:
            self.columns_all_radio.setChecked(True)

        if config.get("last_file"):
            try:
                path = Path(config["last_file"])
                if path.exists() and path.is_file():
                    self.set_file(path)
            except Exception:
                pass  # Ignore invalid paths

    # ------------------------------------------------------------------ Internal helpers
    def _schedule_analysis(self, *, delay_ms: int = 200) -> None:
        if self._current_file is None:
            self._column_stats = None
            self.column_info_label.setText("未选择文件。")
            self.column_empty_label.setText("")
            self._update_range_enabled()
            return
        self.column_info_label.setText("正在分析列信息…")
        self.column_empty_label.setText("")
        self._analysis_timer.stop()
        self._analysis_timer.start(max(0, delay_ms))

    def _analyze_file(self) -> None:
        path = self._current_file
        if path is None:
            return
        sheet = self._sheet_accessor() if self._sheet_accessor else None
        try:
            data = _load_probabilities(path, sheet, column_range=None)
        except Exception as exc:
            self._column_stats = None
            self.column_info_label.setText(f"无法读取列信息：{exc}")
            self.column_empty_label.setText("")
            self._set_range_valid(False, "列信息不可用。")
            self._update_range_enabled()
            return

        total_cols = data.shape[1]
        valid_cols = get_valid_columns(data)
        empty_cols = get_empty_columns(data)
        self._column_stats = {
            "total": total_cols,
            "valid": valid_cols,
            "empty": empty_cols,
        }

        self.column_info_label.setText(
            f"检测到 {len(valid_cols)} 个有效列 / 共 {total_cols} 列。"
        )
        if empty_cols:
            formatted = self._format_column_list(empty_cols)
            self.column_empty_label.setText(
                f"空列: {len(empty_cols)}（{formatted}）"
            )
        else:
            self.column_empty_label.setText("空列: 0")

        self.from_col_spin.setRange(1, max(1, total_cols))
        self.to_col_spin.setRange(1, max(1, total_cols))
        if self.to_col_spin.value() > total_cols:
            self.to_col_spin.setValue(total_cols)
        if self.from_col_spin.value() > total_cols:
            self.from_col_spin.setValue(total_cols)

        self._update_range_enabled()
        self._validate_range()

    def _format_column_list(self, columns: list[int], limit: int = 8) -> str:
        if not columns:
            return "-"
        if len(columns) <= limit:
            return ", ".join(str(col) for col in columns)
        head = ", ".join(str(col) for col in columns[:limit])
        return f"{head} …"

    def _update_range_enabled(self) -> None:
        custom = self.columns_custom_radio.isChecked()
        has_stats = self._column_stats is not None
        enabled = custom and has_stats
        self.range_container.setEnabled(enabled)
        self.range_hint_label.setVisible(custom)
        self.range_error_label.setVisible(custom and not self._range_valid and bool(self.range_error_label.text()))
        if not custom:
            self._set_range_valid(True, "")
        elif has_stats:
            self._validate_range()

    def _validate_range(self) -> bool:
        if not self.columns_custom_radio.isChecked():
            self._set_range_valid(True, "")
            return True
        if not self._column_stats:
            self._set_range_valid(False, "列信息尚未准备好。")
            return False

        start = self.from_col_spin.value()
        end = self.to_col_spin.value()
        total = int(self._column_stats.get("total", 0))
        if start < 1 or end < 1 or start > total or end > total:
            self._set_range_valid(False, f"列范围需在 1~{total} 之间。")
            return False
        if end < start:
            self._set_range_valid(False, "结束列必须大于等于开始列。")
            return False

        empty_cols: list[int] = list(self._column_stats.get("empty", []))
        invalid = [col for col in range(start, end + 1) if col in empty_cols]
        if invalid:
            formatted = ", ".join(str(col) for col in invalid[:6])
            if len(invalid) > 6:
                formatted += " …"
            self._set_range_valid(False, f"所选范围包含空列：{formatted}")
            return False

        self._set_range_valid(True, "")
        return True

    def _set_range_valid(self, valid: bool, message: str) -> None:
        self._range_valid = valid
        self.range_error_label.setText(message)
        self.range_error_label.setVisible(not valid and bool(message) and self.columns_custom_radio.isChecked())

    @staticmethod
    def _coerce_positive_int(value, *, default: int) -> int:
        try:
            candidate = int(value)
            if candidate >= 1:
                return candidate
        except (TypeError, ValueError):
            pass
        return default

    @staticmethod
    def _set_spin_value(spin: QtWidgets.QSpinBox, value: int) -> None:
        if value > spin.maximum():
            spin.setMaximum(value)
        if value < spin.minimum():
            spin.setMinimum(value)
        spin.setValue(value)
