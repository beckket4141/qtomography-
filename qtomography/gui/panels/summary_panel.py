from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
from PySide6 import QtCore, QtGui, QtWidgets


class SummaryPanel(QtWidgets.QWidget):
    """Display summary.csv content in a table view."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._model = QtGui.QStandardItemModel(self)
        self._build_ui()

    def _build_ui(self) -> None:
        self._df: Optional[pd.DataFrame] = None
        # Design filter row
        self.design_combo = QtWidgets.QComboBox()
        self.design_combo.addItem("All", userData=None)
        self.design_combo.currentIndexChanged.connect(self._apply_filter)

        self.table = QtWidgets.QTableView()
        self.table.setModel(self._model)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        layout = QtWidgets.QVBoxLayout(self)
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Design:"))
        filter_layout.addWidget(self.design_combo)
        filter_layout.addStretch(1)
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)

    def clear(self) -> None:
        self._model.clear()

    def load_summary(self, path: Path) -> None:
        try:
            df = pd.read_csv(path)
        except Exception as exc:  # pylint: disable=broad-except
            QtWidgets.QMessageBox.critical(
                self,
                "加载 Summary 失败",
                f"无法读取 {path}:\n{exc}",
            )
            return

        self._df = df
        # Populate design filter if column exists
        self.design_combo.blockSignals(True)
        self.design_combo.clear()
        self.design_combo.addItem("All", userData=None)
        if "design" in df.columns:
            designs = sorted(str(x) for x in df["design"].dropna().unique())
            for d in designs:
                self.design_combo.addItem(d, userData=d)
        self.design_combo.blockSignals(False)
        self._apply_filter()

    # ------------------------------------------------------------------ helpers
    def _apply_filter(self) -> None:
        self._model.clear()
        df = self._df
        if df is None or df.empty:
            return
        # Apply design filter
        sel = self.design_combo.currentData()
        if sel is not None and "design" in df.columns:
            df_view = df[df["design"].astype(str) == str(sel)]
        else:
            df_view = df
        self._model.setHorizontalHeaderLabels(df_view.columns.tolist())
        for _, row in df_view.iterrows():
            items = [QtGui.QStandardItem(str(row[col]) if pd.notna(row[col]) else "") for col in df_view.columns]
            self._model.appendRow(items)
        self.table.resizeColumnsToContents()
