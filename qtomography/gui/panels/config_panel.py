from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Union

from PySide6 import QtCore, QtWidgets


class ConfigPanel(QtWidgets.QWidget):
    """Panel exposing algorithm configuration controls."""

    sheet_changed = QtCore.Signal(object)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.linear_checkbox = QtWidgets.QCheckBox("Linear")
        self.linear_checkbox.setChecked(True)
        self.wls_checkbox = QtWidgets.QCheckBox("WLS")
        self.wls_checkbox.setChecked(True)
        self.rhor_checkbox = QtWidgets.QCheckBox("RρR Strict")
        self.rhor_checkbox.setChecked(False)

        # Measurement design selector (MUB / SIC / NoPOVM)
        self.design_combo = QtWidgets.QComboBox()
        self.design_combo.addItem("MUB", userData="mub")
        self.design_combo.addItem("SIC-POVM", userData="sic")
        self.design_combo.addItem("NoPOVM", userData="nopovm")
        self.design_combo.setCurrentIndex(0)

        methods_layout = QtWidgets.QHBoxLayout()
        methods_layout.addWidget(QtWidgets.QLabel("重构方法:"))
        methods_layout.addWidget(self.linear_checkbox)
        methods_layout.addWidget(self.wls_checkbox)
        methods_layout.addWidget(self.rhor_checkbox)
        methods_layout.addSpacing(12)
        methods_layout.addWidget(QtWidgets.QLabel("测量设计:"))
        methods_layout.addWidget(self.design_combo)
        methods_layout.addStretch(1)

        self.auto_dimension_checkbox = QtWidgets.QCheckBox("自动推断维度")
        self.auto_dimension_checkbox.setChecked(True)
        self.dimension_spin = QtWidgets.QSpinBox()
        self.dimension_spin.setRange(2, 128)
        self.dimension_spin.setValue(4)
        self.dimension_spin.setEnabled(False)
        self.auto_dimension_checkbox.toggled.connect(self.dimension_spin.setDisabled)

        dimension_layout = QtWidgets.QHBoxLayout()
        dimension_layout.addWidget(QtWidgets.QLabel("维度:"))
        dimension_layout.addWidget(self.dimension_spin)
        dimension_layout.addWidget(self.auto_dimension_checkbox)
        dimension_layout.addStretch(1)

        self.sheet_edit = QtWidgets.QLineEdit()
        self.sheet_edit.setPlaceholderText("Excel 工作表 (可选)")
        self.sheet_edit.textChanged.connect(
            lambda *_: self.sheet_changed.emit(self.current_sheet())
        )

        sheet_layout = QtWidgets.QHBoxLayout()
        sheet_layout.addWidget(QtWidgets.QLabel("工作表:"))
        sheet_layout.addWidget(self.sheet_edit)

        self.linear_reg_spin = QtWidgets.QDoubleSpinBox()
        self.linear_reg_spin.setDecimals(8)
        self.linear_reg_spin.setRange(0.0, 1.0)
        self.linear_reg_spin.setSingleStep(0.0001)
        self.linear_reg_spin.setSpecialValueText("默认")

        self.wls_reg_spin = QtWidgets.QDoubleSpinBox()
        self.wls_reg_spin.setDecimals(8)
        self.wls_reg_spin.setRange(0.0, 1.0)
        self.wls_reg_spin.setSingleStep(0.0001)
        self.wls_reg_spin.setSpecialValueText("默认")

        reg_layout = QtWidgets.QFormLayout()
        reg_layout.addRow("Linear 正则化:", self.linear_reg_spin)
        reg_layout.addRow("WLS 正则化:", self.wls_reg_spin)

        self.wls_iterations_spin = QtWidgets.QSpinBox()
        self.wls_iterations_spin.setRange(100, 10000)
        self.wls_iterations_spin.setValue(2000)

        self.tolerance_spin = QtWidgets.QDoubleSpinBox()
        self.tolerance_spin.setDecimals(12)
        self.tolerance_spin.setRange(1e-12, 1e-3)
        self.tolerance_spin.setValue(1e-9)
        self.tolerance_spin.setSingleStep(1e-9)

        advanced_layout = QtWidgets.QFormLayout()
        advanced_layout.addRow("WLS 最大迭代:", self.wls_iterations_spin)
        advanced_layout.addRow("容差:", self.tolerance_spin)

        self.cache_projectors_checkbox = QtWidgets.QCheckBox("缓存投影算子")
        self.cache_projectors_checkbox.setChecked(True)

        self.bell_checkbox = QtWidgets.QCheckBox("执行 Bell 分析")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(methods_layout)
        layout.addLayout(dimension_layout)
        layout.addLayout(sheet_layout)
        layout.addLayout(reg_layout)
        layout.addLayout(advanced_layout)
        layout.addWidget(self.cache_projectors_checkbox)
        layout.addWidget(self.bell_checkbox)
        layout.addStretch(1)

    # ------------------------------------------------------------------ API
    def build_config_kwargs(self, dataset_path: Path) -> Dict:
        methods = []
        if self.linear_checkbox.isChecked():
            methods.append("linear")
        if self.wls_checkbox.isChecked():
            methods.append("wls")
        if self.rhor_checkbox.isChecked():
            methods.append("rhor")
        if not methods:
            raise ValueError("至少需要选择一种重构方法。")

        kwargs = {
            "input_path": dataset_path,
            "methods": tuple(methods),
            "design": str(self.design_combo.currentData() or "mub"),
            "dimension": None if self.auto_dimension_checkbox.isChecked() else self.dimension_spin.value(),
            "linear_regularization": self._value_or_none(self.linear_reg_spin),
            "wls_regularization": self._value_or_none(self.wls_reg_spin),
            "wls_max_iterations": self.wls_iterations_spin.value(),
            "tolerance": float(self.tolerance_spin.value()),
            "cache_projectors": self.cache_projectors_checkbox.isChecked(),
            "analyze_bell": self.bell_checkbox.isChecked(),
        }

        kwargs["sheet"] = self.current_sheet()

        return kwargs

    def current_sheet(self) -> Optional[Union[str, int]]:
        """Return current sheet selection (None/name/index)."""
        text = self.sheet_edit.text().strip()
        if not text:
            return None
        return text if not text.isdigit() else int(text)

    @staticmethod
    def _value_or_none(spin: QtWidgets.QDoubleSpinBox) -> Optional[float]:
        value = float(spin.value())
        # Use zero to represent default (spin shows "默认")
        return None if value == 0.0 else value

    # ------------------------------------------------------------------ Configuration
    def save_config(self) -> dict:
        """Save current panel configuration to dictionary."""
        return {
            "linear_enabled": self.linear_checkbox.isChecked(),
            "wls_enabled": self.wls_checkbox.isChecked(),
            "rhor_enabled": self.rhor_checkbox.isChecked(),
            "design": str(self.design_combo.currentData() or "mub"),
            "auto_dimension": self.auto_dimension_checkbox.isChecked(),
            "dimension": self.dimension_spin.value(),
            "sheet": self.sheet_edit.text().strip(),
            "linear_regularization": self._value_or_none(self.linear_reg_spin),
            "wls_regularization": self._value_or_none(self.wls_reg_spin),
            "wls_max_iterations": self.wls_iterations_spin.value(),
            "tolerance": float(self.tolerance_spin.value()),
            "cache_projectors": self.cache_projectors_checkbox.isChecked(),
            "analyze_bell": self.bell_checkbox.isChecked(),
        }

    def load_config(self, config: dict) -> None:
        """Load panel configuration from dictionary."""
        # Method checkboxes
        if "linear_enabled" in config:
            self.linear_checkbox.setChecked(bool(config["linear_enabled"]))
        if "wls_enabled" in config:
            self.wls_checkbox.setChecked(bool(config["wls_enabled"]))
        if "rhor_enabled" in config:
            self.rhor_checkbox.setChecked(bool(config["rhor_enabled"]))

        # Measurement design
        if "design" in config:
            design = str(config["design"])
            for i in range(self.design_combo.count()):
                if self.design_combo.itemData(i) == design:
                    self.design_combo.setCurrentIndex(i)
                    break

        # Dimension
        if "auto_dimension" in config:
            self.auto_dimension_checkbox.setChecked(bool(config["auto_dimension"]))
        if "dimension" in config:
            try:
                dim = int(config["dimension"])
                if 2 <= dim <= 128:
                    self.dimension_spin.setValue(dim)
            except (ValueError, TypeError):
                pass

        # Sheet
        if "sheet" in config:
            self.sheet_edit.setText(str(config["sheet"]))

        # Regularization
        if "linear_regularization" in config:
            linear_reg = config["linear_regularization"]
            if linear_reg is not None:
                try:
                    self.linear_reg_spin.setValue(float(linear_reg))
                except (ValueError, TypeError):
                    self.linear_reg_spin.setValue(0.0)  # Default
            else:
                self.linear_reg_spin.setValue(0.0)  # Default

        if "wls_regularization" in config:
            wls_reg = config["wls_regularization"]
            if wls_reg is not None:
                try:
                    self.wls_reg_spin.setValue(float(wls_reg))
                except (ValueError, TypeError):
                    self.wls_reg_spin.setValue(0.0)  # Default
            else:
                self.wls_reg_spin.setValue(0.0)  # Default

        # Advanced parameters
        if "wls_max_iterations" in config:
            try:
                iterations = int(config["wls_max_iterations"])
                if 100 <= iterations <= 10000:
                    self.wls_iterations_spin.setValue(iterations)
            except (ValueError, TypeError):
                pass

        if "tolerance" in config:
            try:
                tol = float(config["tolerance"])
                if 1e-12 <= tol <= 1e-3:
                    self.tolerance_spin.setValue(tol)
            except (ValueError, TypeError):
                pass

        # Options
        if "cache_projectors" in config:
            self.cache_projectors_checkbox.setChecked(bool(config["cache_projectors"]))
        if "analyze_bell" in config:
            self.bell_checkbox.setChecked(bool(config["analyze_bell"]))
