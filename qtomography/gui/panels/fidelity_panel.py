from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6 import QtCore, QtWidgets

from qtomography.gui.services.fidelity_service import (
    FidelityComputationError,
    FidelityResult,
    compute_fidelity_from_files,
    compute_fidelity_with_custom_state,
)

__all__ = ["FidelityPanel"]


class FidelityPanel(QtWidgets.QWidget):
    """Panel providing quick fidelity calculations for density matrices."""

    MODE_FILE = "file"
    MODE_CUSTOM = "custom"

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._last_dir: Optional[Path] = None
        self._build_ui()
        self._update_mode_widgets()

    # ------------------------------------------------------------------ UI construction
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(self._build_experimental_group())
        layout.addWidget(self._build_theoretical_group())
        layout.addWidget(self._build_actions_group())
        layout.addWidget(self._build_result_group(), stretch=1)
        layout.addStretch()

    def _build_experimental_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("实验密度矩阵 ρₑ")
        group_layout = QtWidgets.QVBoxLayout(group)

        row = QtWidgets.QHBoxLayout()
        self.experimental_path_edit = QtWidgets.QLineEdit()
        self.experimental_path_edit.setReadOnly(True)
        browse_btn = QtWidgets.QPushButton("选择文件…")
        browse_btn.clicked.connect(self._browse_experimental_file)
        row.addWidget(self.experimental_path_edit)
        row.addWidget(browse_btn)

        self.experimental_info_label = QtWidgets.QLabel("未选择文件。")
        self.experimental_info_label.setWordWrap(True)
        self.experimental_info_label.setStyleSheet("color: #6c6c6c;")

        group_layout.addLayout(row)
        group_layout.addWidget(self.experimental_info_label)
        return group

    def _build_theoretical_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("理论密度矩阵 ρₜₕ")
        group_layout = QtWidgets.QVBoxLayout(group)
        group_layout.setSpacing(10)

        # Mode selection
        mode_layout = QtWidgets.QHBoxLayout()
        mode_layout.addWidget(QtWidgets.QLabel("选择方式:"))
        self.mode_file_radio = QtWidgets.QRadioButton("从文件读取")
        self.mode_custom_radio = QtWidgets.QRadioButton("自定义纯态")
        self.mode_file_radio.setChecked(True)

        self.mode_file_radio.toggled.connect(self._update_mode_widgets)
        self.mode_custom_radio.toggled.connect(self._update_mode_widgets)

        mode_layout.addWidget(self.mode_file_radio)
        mode_layout.addWidget(self.mode_custom_radio)
        mode_layout.addStretch(1)
        group_layout.addLayout(mode_layout)

        # File mode widgets
        self.file_mode_container = QtWidgets.QGroupBox("理论密度矩阵文件")
        file_layout = QtWidgets.QHBoxLayout(self.file_mode_container)
        self.theory_path_edit = QtWidgets.QLineEdit()
        self.theory_path_edit.setReadOnly(True)
        self.theory_browse_btn = QtWidgets.QPushButton("选择文件…")
        self.theory_browse_btn.clicked.connect(self._browse_theory_file)
        file_layout.addWidget(self.theory_path_edit)
        file_layout.addWidget(self.theory_browse_btn)

        # Custom mode widgets
        self.custom_mode_container = QtWidgets.QGroupBox("自定义纯态参数")
        custom_layout = QtWidgets.QVBoxLayout(self.custom_mode_container)

        dimension_row = QtWidgets.QHBoxLayout()
        dimension_row.addWidget(QtWidgets.QLabel("维度 d:"))
        self.custom_dimension_spin = QtWidgets.QSpinBox()
        self.custom_dimension_spin.setRange(2, 128)
        self.custom_dimension_spin.setValue(4)
        self.custom_dimension_spin.valueChanged.connect(self._dimension_changed)
        dimension_row.addWidget(self.custom_dimension_spin)
        dimension_row.addStretch(1)
        custom_layout.addLayout(dimension_row)

        self.custom_table = QtWidgets.QTableWidget()
        self.custom_table.setColumnCount(2)
        self.custom_table.setHorizontalHeaderLabels(["模长 |cᵢ|", "相位 φᵢ (π)"])
        self.custom_table.horizontalHeader().setStretchLastSection(True)
        self.custom_table.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        custom_layout.addWidget(self.custom_table)

        hint = QtWidgets.QLabel("提示: 相位以 π 为单位填写, 允许负值; 模长会自动归一化。")
        hint.setStyleSheet("color: #6c6c6c; font-size: 11px;")
        custom_layout.addWidget(hint)

        group_layout.addWidget(self.file_mode_container)
        group_layout.addWidget(self.custom_mode_container)
        return group

    def _build_actions_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("计算")
        layout = QtWidgets.QHBoxLayout(group)
        self.compute_button = QtWidgets.QPushButton("计算保真度")
        self.compute_button.clicked.connect(self._compute_fidelity)
        layout.addStretch(1)
        layout.addWidget(self.compute_button)
        return group

    def _build_result_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("结果")
        layout = QtWidgets.QVBoxLayout(group)

        self.result_label = QtWidgets.QLabel("尚未计算。")
        self.result_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.details_edit = QtWidgets.QTextEdit()
        self.details_edit.setReadOnly(True)
        self.details_edit.setPlaceholderText("详细信息将在此处显示。")

        layout.addWidget(self.result_label)
        layout.addWidget(self.details_edit, stretch=1)
        return group

    # ------------------------------------------------------------------ Slots
    def _browse_experimental_file(self) -> None:
        directory = str(self._last_dir) if self._last_dir else ""
        path_str, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择实验密度矩阵文件",
            directory,
            "Density matrix files (*.json *.csv *.txt *.xlsx *.xls *.mat);;All files (*)",
        )
        if path_str:
            self.experimental_path_edit.setText(path_str)
            self._last_dir = Path(path_str).parent
            self.experimental_info_label.setText(f"选定文件: {path_str}")

    def _browse_theory_file(self) -> None:
        directory = str(self._last_dir) if self._last_dir else ""
        path_str, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择理论密度矩阵文件",
            directory,
            "Density matrix files (*.json *.csv *.txt *.xlsx *.xls *.mat);;All files (*)",
        )
        if path_str:
            self.theory_path_edit.setText(path_str)
            self._last_dir = Path(path_str).parent

    def _update_mode_widgets(self) -> None:
        mode = self.current_mode()
        self.file_mode_container.setEnabled(mode == self.MODE_FILE)
        self.custom_mode_container.setEnabled(mode == self.MODE_CUSTOM)
        if mode == self.MODE_CUSTOM:
            self._ensure_rows_match_dimension()

    def _dimension_changed(self, value: int) -> None:
        if self.current_mode() == self.MODE_CUSTOM:
            self._ensure_rows_match_dimension(value)

    # ------------------------------------------------------------------ Helpers
    def current_mode(self) -> str:
        return self.MODE_CUSTOM if self.mode_custom_radio.isChecked() else self.MODE_FILE

    def _ensure_rows_match_dimension(self, dimension: Optional[int] = None) -> None:
        dim = dimension or self.custom_dimension_spin.value()
        current_rows = self.custom_table.rowCount()
        if current_rows != dim:
            self.custom_table.setRowCount(dim)
            for row in range(dim):
                self.custom_table.setVerticalHeaderItem(
                    row, QtWidgets.QTableWidgetItem(f"c{row + 1}")
                )
                if current_rows < dim:
                    if not self.custom_table.item(row, 0):
                        self.custom_table.setItem(row, 0, QtWidgets.QTableWidgetItem("0"))
                    if not self.custom_table.item(row, 1):
                        self.custom_table.setItem(row, 1, QtWidgets.QTableWidgetItem("0"))

    def _collect_custom_values(self) -> Tuple[List[float], List[float]]:
        dimension = self.custom_dimension_spin.value()
        self._ensure_rows_match_dimension(dimension)
        amplitudes: List[float] = []
        phases: List[float] = []

        for row in range(dimension):
            amp_item = self.custom_table.item(row, 0)
            phase_item = self.custom_table.item(row, 1)
            amp_text = amp_item.text().strip() if amp_item else "0"
            phase_text = phase_item.text().strip() if phase_item else "0"
            try:
                amplitude = float(amp_text or "0")
            except ValueError as exc:
                raise FidelityComputationError(f"第 {row + 1} 行的模长无效: {amp_text}") from exc
            try:
                phase = float(phase_text or "0")
            except ValueError as exc:
                raise FidelityComputationError(f"第 {row + 1} 行的相位无效: {phase_text}") from exc
            amplitudes.append(amplitude)
            phases.append(phase)
        return amplitudes, phases

    def _compute_fidelity(self) -> None:
        experimental_path = self.experimental_path_edit.text().strip()
        if not experimental_path:
            QtWidgets.QMessageBox.warning(self, "实验态", "请先选择实验密度矩阵文件。")
            return

        try:
            if self.current_mode() == self.MODE_FILE:
                theoretical_path = self.theory_path_edit.text().strip()
                if not theoretical_path:
                    QtWidgets.QMessageBox.warning(self, "理论态", "请选择理论密度矩阵文件。")
                    return
                result = compute_fidelity_from_files(
                    Path(experimental_path),
                    Path(theoretical_path),
                )
            else:
                amplitudes, phases = self._collect_custom_values()
                result = compute_fidelity_with_custom_state(
                    Path(experimental_path),
                    self.custom_dimension_spin.value(),
                    amplitudes,
                    phases,
                )
        except FidelityComputationError as exc:
            QtWidgets.QMessageBox.critical(self, "保真度计算失败", str(exc))
            return

        self._display_result(result)

    def _display_result(self, result: FidelityResult) -> None:
        self.result_label.setText(f"保真度 F = {result.fidelity:.8f}")

        info_lines = [
            f"实验态维度: {result.experimental_dimension}",
            f"理论态维度: {result.theoretical_dimension}",
        ]
        if result.theoretical_state:
            info_lines.append("自定义纯态已归一化并自动计算保真度。")
            coeffs = ", ".join(f"{v:.6f}" for v in result.theoretical_state.coefficients)
            phases = ", ".join(f"{v:.4f}π" for v in result.theoretical_state.phases)
            info_lines.append(f"系数模长: {coeffs}")
            info_lines.append(f"相位: {phases}")

        if result.warnings:
            info_lines.append("")
            info_lines.append("⚠️ 警告:")
            info_lines.extend(f"- {message}" for message in result.warnings)

        self.details_edit.setPlainText("\n".join(info_lines))

    # ------------------------------------------------------------------ Configuration persistence
    def save_config(self) -> Dict[str, object]:
        config: Dict[str, object] = {
            "experimental_path": self.experimental_path_edit.text().strip(),
            "mode": self.current_mode(),
        }
        if self.current_mode() == self.MODE_FILE:
            config["theory_path"] = self.theory_path_edit.text().strip()
        else:
            amplitudes, phases = self._collect_custom_values()
            config.update(
                {
                    "theory_path": "",
                    "custom_dimension": self.custom_dimension_spin.value(),
                    "custom_amplitudes": amplitudes,
                    "custom_phases": phases,
                }
            )
        return config

    def load_config(self, config: Dict[str, object]) -> None:
        experimental_path = str(config.get("experimental_path", "") or "")
        if experimental_path:
            self.experimental_path_edit.setText(experimental_path)
            self.experimental_info_label.setText(f"选定文件: {experimental_path}")

        mode = str(config.get("mode", self.MODE_FILE))
        if mode == self.MODE_CUSTOM:
            self.mode_custom_radio.setChecked(True)
        else:
            self.mode_file_radio.setChecked(True)

        theory_path = str(config.get("theory_path", "") or "")
        if theory_path:
            self.theory_path_edit.setText(theory_path)

        if mode == self.MODE_CUSTOM:
            dimension = int(config.get("custom_dimension", 4) or 4)
            amplitudes = config.get("custom_amplitudes") or []
            phases = config.get("custom_phases") or []
            self.custom_dimension_spin.setValue(dimension)
            self._ensure_rows_match_dimension(dimension)
            for row in range(dimension):
                amp_value = ""
                phase_value = ""
                if row < len(amplitudes):
                    amp_value = f"{float(amplitudes[row]):.6g}"
                if row < len(phases):
                    phase_value = f"{float(phases[row]):.6g}"
                self.custom_table.setItem(row, 0, QtWidgets.QTableWidgetItem(amp_value))
                self.custom_table.setItem(row, 1, QtWidgets.QTableWidgetItem(phase_value))
        self._update_mode_widgets()


