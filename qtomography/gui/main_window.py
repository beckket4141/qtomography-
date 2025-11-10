from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from qtomography.app.controller import ReconstructionConfig

from .panels.config_panel import ConfigPanel
from .panels.data_panel import DataPanel
from .panels.execute_panel import ExecutePanel
from .panels.figure_panel import FigurePanel
from .panels.progress_panel import ProgressPanel
from .panels.spectral_panel import SpectralDecompositionPanel
from .panels.summary_panel import SummaryPanel
from .services.controller_runner import ControllerRunner
from .services.spectral_runner import SpectralJobConfig, SpectralRunner
from .application.use_cases import GUIConfigUseCase


class MainWindow(QtWidgets.QMainWindow):
    """Main window for the QTomography MVP GUI."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QTomography GUI (MVP)")
        self.resize(1200, 720)

        self._runner = ControllerRunner(self)
        self._runner.started.connect(self._on_runner_started)
        self._runner.progress.connect(self._on_runner_progress)
        self._runner.finished.connect(self._on_runner_finished)
        self._runner.failed.connect(self._on_runner_failed)
        self._runner.cancelled.connect(self._on_runner_cancelled)

        self._spectral_runner = SpectralRunner(self)
        self._spectral_runner.started.connect(self._on_spectral_started)
        self._spectral_runner.progress.connect(self._on_spectral_progress)
        self._spectral_runner.finished.connect(self._on_spectral_finished)
        self._spectral_runner.error.connect(self._on_spectral_error)
        self._spectral_runner.log.connect(self._on_spectral_log)
        self._spectral_runner.cancelled.connect(self._on_spectral_cancelled)

        self._current_result_dir: Optional[Path] = None
        self._current_spectral_result_dir: Optional[Path] = None

        # Initialize configuration use case
        self._config_use_case = GUIConfigUseCase()

        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_central_widgets()
        self._connect_execute_panel()
        self._connect_spectral_panel()

        # Load saved configuration on startup
        self._load_config_to_ui()

    # ------------------------------------------------------------------ Setup
    def _create_actions(self) -> None:
        self.action_open = QtGui.QAction("打开数据", self)
        self.action_open.triggered.connect(self._open_data_file)

        self.action_run = QtGui.QAction("运行", self)
        self.action_run.triggered.connect(self._trigger_run)

        self.action_cancel = QtGui.QAction("取消", self)
        self.action_cancel.setEnabled(False)
        self.action_cancel.triggered.connect(self._runner.cancel)

        self.action_open_output = QtGui.QAction("打开输出目录", self)
        self.action_open_output.setEnabled(False)
        self.action_open_output.triggered.connect(self._open_output_dir)

    def _create_menu(self) -> None:
        menu_bar = self.menuBar()

        menu_file = menu_bar.addMenu("文件")
        menu_file.addAction(self.action_open)
        menu_file.addSeparator()
        menu_file.addAction(self.action_open_output)
        menu_file.addSeparator()
        exit_action = QtGui.QAction("退出", self)
        exit_action.triggered.connect(self.close)
        menu_file.addAction(exit_action)

        menu_config = menu_bar.addMenu("配置")
        menu_config.addAction("保存当前配置为默认", self._save_config_as_default)
        menu_config.addAction("加载默认配置", self._load_default_config)
        menu_config.addSeparator()
        menu_config.addAction("另存配置...", self._save_config_as)
        menu_config.addAction("从文件加载配置...", self._load_config_from_file)
        menu_config.addSeparator()
        menu_config.addAction("重置为默认配置", self._reset_to_default)

        menu_help = menu_bar.addMenu("帮助")
        about_action = QtGui.QAction("关于", self)
        about_action.triggered.connect(self._show_about_dialog)
        menu_help.addAction(about_action)

    def _create_toolbar(self) -> None:
        toolbar = self.addToolBar("主工具栏")
        toolbar.setObjectName("main_toolbar")  # Required for saveState()/restoreState()
        toolbar.setMovable(False)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_run)
        toolbar.addAction(self.action_cancel)
        toolbar.addSeparator()
        toolbar.addAction(self.action_open_output)

    def _create_central_widgets(self) -> None:
        """Create traditional splitter layout (数据/参数/执行 | Summary/图像/进度)."""
        self.data_panel = DataPanel()
        self.config_panel = ConfigPanel()
        self.execute_panel = ExecutePanel()
        self.spectral_panel = SpectralDecompositionPanel()

        self.progress_panel = ProgressPanel()
        self.summary_panel = SummaryPanel()
        self.figure_panel = FigurePanel()

        left_tabs = QtWidgets.QTabWidget()
        left_tabs.addTab(self.data_panel, "数据")
        left_tabs.addTab(self.config_panel, "参数")
        left_tabs.addTab(self.execute_panel, "执行")
        left_tabs.addTab(self.spectral_panel, "谱分解")

        right_tabs = QtWidgets.QTabWidget()
        right_tabs.addTab(self.progress_panel, "进度")
        right_tabs.addTab(self.summary_panel, "汇总")
        right_tabs.addTab(self.figure_panel, "图像")

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(left_tabs)
        splitter.addWidget(right_tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.addWidget(splitter)
        self.setCentralWidget(central)

    def _connect_execute_panel(self) -> None:
        self.execute_panel.run_requested.connect(self._trigger_run)
        self.execute_panel.cancel_requested.connect(self._runner.cancel)
        self.execute_panel.open_output_requested.connect(self._open_output_dir)

    def _connect_spectral_panel(self) -> None:
        self.spectral_panel.start_requested.connect(self._on_spectral_start_requested)
        self.spectral_panel.cancel_requested.connect(self._on_spectral_cancel_requested)

    # ------------------------------------------------------------------ Spectral panel handlers
    def _on_spectral_start_requested(self, payload: dict) -> None:
        """Handle spectral decomposition start request from panel."""
        try:
            config = SpectralJobConfig.from_dict(payload)
            self._spectral_runner.start(config)
        except ValueError as exc:
            QtWidgets.QMessageBox.critical(self, "参数错误", str(exc))
        except RuntimeError as exc:
            QtWidgets.QMessageBox.warning(self, "任务执行", str(exc))

    def _on_spectral_cancel_requested(self) -> None:
        """Handle spectral decomposition cancel request from panel."""
        self._spectral_runner.cancel()

    def _on_spectral_started(self) -> None:
        """Handle spectral runner started signal."""
        self.spectral_panel.set_running(True)
        self.spectral_panel.reset_progress()
        self.spectral_panel.append_log("开始批处理...")

    def _on_spectral_progress(self, percent: int, message: str) -> None:
        """Handle spectral runner progress signal."""
        self.spectral_panel.update_progress(percent, message)

    def _on_spectral_finished(self, result_dir: Path) -> None:
        """Handle spectral runner finished signal."""
        self.spectral_panel.set_running(False)
        self._current_spectral_result_dir = result_dir
        self.spectral_panel.append_log(f"批处理完成！结果保存在: {result_dir}")

        QtWidgets.QMessageBox.information(
            self,
            "谱分解完成",
            f"批处理完成！\n结果保存在:\n{result_dir}",
        )

        # Optionally open output directory
        reply = QtWidgets.QMessageBox.question(
            self,
            "打开输出目录",
            "是否打开输出目录？",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(result_dir)))

    def _on_spectral_error(self, path: str, error_message: str) -> None:
        """Handle spectral runner error signal."""
        self.spectral_panel.append_log(f"错误 [{path}]: {error_message}")

    def _on_spectral_log(self, message: str) -> None:
        """Handle spectral runner log signal."""
        self.spectral_panel.append_log(message)

    def _on_spectral_cancelled(self) -> None:
        """Handle spectral runner cancelled signal."""
        self.spectral_panel.set_running(False)
        self.spectral_panel.append_log("任务已取消")
        QtWidgets.QMessageBox.information(self, "已取消", "谱分解任务已取消。")

    # ------------------------------------------------------------------ Actions
    def _open_data_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择测量数据文件",
            "",
            "Data files (*.csv *.xlsx *.xls);;All files (*)",
        )
        if path:
            self.data_panel.set_file(Path(path))

    def _trigger_run(self) -> None:
        config = self._build_config()
        if config is None:
            return

        try:
            self._runner.start(config, config.output_dir)
        except ValueError as exc:
            QtWidgets.QMessageBox.critical(self, "参数错误", str(exc))
        except RuntimeError as exc:
            QtWidgets.QMessageBox.warning(self, "任务执行", str(exc))

    def _open_output_dir(self) -> None:
        if not self._current_result_dir:
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self._current_result_dir)))

    def _show_about_dialog(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "关于 QTomography GUI",
            "最小可用桌面界面，封装 CSV/Excel 数据加载、参数配置、运行进度与结果展示。",
        )

    # ------------------------------------------------------------------ Runner callbacks
    def _on_runner_started(self) -> None:
        self.action_run.setEnabled(False)
        self.action_cancel.setEnabled(True)
        self.action_open.setEnabled(False)
        self.execute_panel.set_running(True)
        self.progress_panel.reset()
        self.summary_panel.clear()
        self.figure_panel.clear()
        self.statusBar().showMessage("正在运行…")

    def _on_runner_progress(self, event) -> None:
        self.progress_panel.update_event(event)

    def _on_runner_finished(self, result) -> None:
        self._restore_idle_state()
        self.statusBar().showMessage("运行完成", 5000)

        self._current_result_dir = result.records_dir
        self.action_open_output.setEnabled(True)

        self.summary_panel.load_summary(result.summary_path)
        self.figure_panel.load_from_records(result.records_dir)

        QtWidgets.QMessageBox.information(self, "完成", "重构任务完成。")

    def _on_runner_failed(self, message: str) -> None:
        self._restore_idle_state()
        QtWidgets.QMessageBox.critical(self, "执行失败", message)

    def _on_runner_cancelled(self, message: str) -> None:
        self._restore_idle_state()
        QtWidgets.QMessageBox.information(self, "已取消", message)

    def _restore_idle_state(self) -> None:
        self.action_run.setEnabled(True)
        self.action_cancel.setEnabled(False)
        self.action_open.setEnabled(True)
        self.execute_panel.set_running(False)
        self.statusBar().clearMessage()

    # ------------------------------------------------------------------ Config helpers
    def _build_config(self) -> Optional[ReconstructionConfig]:
        # 确保每次都获取当前选择的文件（不依赖缓存）
        dataset = self.data_panel.current_file()
        if dataset is None:
            QtWidgets.QMessageBox.warning(self, "输入数据", "请先选择测量数据文件。")
            return None

        # 验证文件是否存在且可读
        if not dataset.exists():
            QtWidgets.QMessageBox.warning(
                self, "文件不存在", f"选择的文件不存在：\n{dataset}"
            )
            return None

        if not dataset.is_file():
            QtWidgets.QMessageBox.warning(
                self, "无效文件", f"选择的路径不是文件：\n{dataset}"
            )
            return None

        # 记录当前使用的文件路径（用于调试）
        import logging
        logger = logging.getLogger(__name__)
        logger.info("构建配置，使用文件: %s", dataset)

        try:
            config_kwargs = self.config_panel.build_config_kwargs(dataset)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "参数校验失败", str(exc))
            return None

        output_dir = self.execute_panel.output_directory()
        if output_dir is None:
            QtWidgets.QMessageBox.warning(self, "输出目录", "请先选择输出目录。")
            return None

        config_kwargs["output_dir"] = output_dir

        try:
            config = ReconstructionConfig(**config_kwargs)
            # 再次验证配置中的文件路径
            logger.info("配置构建完成，输入文件: %s, 输出目录: %s", config.input_path, config.output_dir)
            return config
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "参数错误", str(exc))
            return None

    # ------------------------------------------------------------------ Configuration Management
    def _load_config_to_ui(self) -> None:
        """Load configuration from repository and apply to UI (配置 → UI)."""
        config = self._config_use_case.get_current_config()

        # Load spectral panel config
        self.spectral_panel.load_config(config.spectral.to_dict())

        # Load data panel config
        self.data_panel.load_config(config.data.to_dict())

        # Load execute panel config
        self.execute_panel.load_config(config.execute.to_dict())

        # Load config panel config
        self.config_panel.load_config(config.config.to_dict())

        # Load window geometry
        if config.window.geometry:
            try:
                # Convert string to QByteArray (PySide6 compatibility)
                geometry_bytes = QtCore.QByteArray.fromBase64(
                    config.window.geometry.encode("utf-8")
                )
                self.restoreGeometry(geometry_bytes)
            except Exception:
                pass  # Ignore invalid geometry

        if config.window.state:
            try:
                state_bytes = QtCore.QByteArray.fromBase64(
                    config.window.state.encode("utf-8")
                )
                self.restoreState(state_bytes)
            except Exception:
                pass  # Ignore invalid state

    def _save_ui_to_config(self) -> None:
        """Save current UI state to configuration (UI → 配置)."""
        from qtomography.gui.domain.gui_config import (
            ConfigConfig,
            DataConfig,
            ExecuteConfig,
            SpectralConfig,
            WindowConfig,
        )

        # Collect UI state
        spectral_dict = self.spectral_panel.save_config()
        data_dict = self.data_panel.save_config()
        execute_dict = self.execute_panel.save_config()
        config_dict = self.config_panel.save_config()

        # Save window geometry
        geometry_bytes = self.saveGeometry()
        state_bytes = self.saveState()
        # Convert QByteArray to base64 string (PySide6 compatibility)
        # toBase64() returns QByteArray, use data() to get bytes, then decode
        geometry_base64 = geometry_bytes.toBase64()
        state_base64 = state_bytes.toBase64()
        geometry_str = geometry_base64.data().decode("utf-8", errors="ignore")
        state_str = state_base64.data().decode("utf-8", errors="ignore")

        # Create config updates
        config_updates = {
            "spectral": SpectralConfig.from_dict(spectral_dict).to_dict(),
            "data": DataConfig.from_dict(data_dict).to_dict(),
            "execute": ExecuteConfig.from_dict(execute_dict).to_dict(),
            "config": ConfigConfig.from_dict(config_dict).to_dict(),
            "window": {
                "geometry": geometry_str,
                "state": state_str,
            },
        }

        # Update configuration
        self._config_use_case.update_config(config_updates)

    def _save_config_as_default(self) -> None:
        """Save current UI state as default configuration."""
        self._save_ui_to_config()
        QtWidgets.QMessageBox.information(
            self, "配置已保存", "当前配置已保存为默认配置。"
        )

    def _load_default_config(self) -> None:
        """Load default configuration and apply to UI."""
        self._load_config_to_ui()
        QtWidgets.QMessageBox.information(
            self, "配置已加载", "默认配置已加载并应用到界面。"
        )

    def _save_config_as(self) -> None:
        """Save current configuration to a specific file."""
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存配置文件", "", "JSON files (*.json);;All files (*)"
        )
        if filepath:
            self._save_ui_to_config()
            if self._config_use_case.save_config_to_file(Path(filepath)):
                QtWidgets.QMessageBox.information(
                    self, "配置已保存", f"配置已保存到:\n{filepath}"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self, "保存失败", "无法保存配置文件，请检查文件路径和权限。"
                )

    def _load_config_from_file(self) -> None:
        """Load configuration from a specific file."""
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "加载配置文件", "", "JSON files (*.json);;All files (*)"
        )
        if filepath:
            if self._config_use_case.load_config_from_file(Path(filepath)):
                self._load_config_to_ui()
                QtWidgets.QMessageBox.information(
                    self, "配置已加载", f"配置已从文件加载:\n{filepath}"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self, "加载失败", "无法加载配置文件，请检查文件格式和路径。"
                )

    def _reset_to_default(self) -> None:
        """Reset configuration to default values."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "重置配置",
            "确定要重置为默认配置吗？当前配置将被覆盖。",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            if self._config_use_case.reset_to_default():
                self._load_config_to_ui()
                QtWidgets.QMessageBox.information(
                    self, "配置已重置", "配置已重置为默认值。"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self, "重置失败", "无法重置配置。"
                )
