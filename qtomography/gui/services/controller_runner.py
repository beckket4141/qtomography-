from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from threading import Event
from typing import Optional

from PySide6 import QtCore

from qtomography.app.controller import ProgressEvent, ReconstructionConfig, ReconstructionController
from qtomography.app.exceptions import ReconstructionCancelled, ReconstructionError


class ControllerRunner(QtCore.QObject):
    """Execute ReconstructionController in a worker thread and emit Qt signals."""

    started = QtCore.Signal()
    progress = QtCore.Signal(ProgressEvent)
    finished = QtCore.Signal(object)  # SummaryResult
    failed = QtCore.Signal(str)
    cancelled = QtCore.Signal(str)

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self._controller = ReconstructionController()
        self._logger = logging.getLogger(__name__)
        self._future = None
        self._cancel_event: Optional[Event] = None

    def start(
        self,
        config: ReconstructionConfig,
        output_dir: Path,
        *,
        repo_factory=None,
    ) -> None:
        if self._future and not self._future.done():
            raise RuntimeError("已有任务正在执行，请先取消或等待完成。")

        cfg = replace(config, output_dir=output_dir)
        self._cancel_event = Event()
        self.started.emit()

        self._future = self._controller.run_batch_async(
            cfg,
            repo_factory=repo_factory,
            progress_callback=self._emit_progress,
            cancel_event=self._cancel_event,
        )
        self._future.add_done_callback(self._handle_done)

    def cancel(self) -> None:
        if self._cancel_event:
            self._cancel_event.set()

    # ------------------------------------------------------------------ callbacks
    def _emit_progress(self, event: ProgressEvent) -> None:
        self.progress.emit(event)

    def _handle_done(self, future) -> None:
        try:
            result = future.result()
        except ReconstructionCancelled as exc:
            message = str(exc)
            self._logger.info("任务被取消: %s", message)
            self.cancelled.emit(message)
        except ReconstructionError as exc:
            self._logger.exception("重构任务失败。")
            self.failed.emit(str(exc))
        except Exception as exc:  # pylint: disable=broad-except
            self._logger.exception("未知错误导致任务失败。")
            self.failed.emit(str(exc))
        else:
            self.finished.emit(result)
        finally:
            self._future = None
            self._cancel_event = None
