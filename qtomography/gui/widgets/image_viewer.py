from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class ImageViewer(QtWidgets.QGraphicsView):
    """Reusable image viewer with smooth zoom/drag/fullscreen support."""

    def __init__(
        self,
        parent: Optional[QtWidgets.QWidget] = None,
        *,
        min_zoom: float = 0.25,
        max_zoom: float = 4.0,
    ) -> None:
        super().__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._pixmap_item: Optional[QtWidgets.QGraphicsPixmapItem] = None
        self._zoom = 1.0
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom

    # ------------------------------------------------------------------ API
    def set_pixmap(self, pixmap: Optional[QtGui.QPixmap]) -> None:
        """Display pixmap inside viewer."""
        self.scene().clear()
        if pixmap is None or pixmap.isNull():
            self._pixmap_item = None
            self._zoom = 1.0
            return

        self._pixmap_item = self.scene().addPixmap(pixmap)
        self.scene().setSceneRect(self._pixmap_item.boundingRect())
        self.reset_view()

    def current_pixmap(self) -> Optional[QtGui.QPixmap]:
        if self._pixmap_item is None:
            return None
        return self._pixmap_item.pixmap()

    def zoom_in(self) -> None:
        self._apply_zoom(1.15)

    def zoom_out(self) -> None:
        self._apply_zoom(1 / 1.15)

    def reset_view(self) -> None:
        self._zoom = 1.0
        self.resetTransform()
        if self._pixmap_item is not None:
            self.fitInView(self._pixmap_item, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    # ------------------------------------------------------------------ Events
    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        if self._pixmap_item is None:
            return
        angle_delta = event.angleDelta().y()
        if angle_delta == 0:
            return
        factor = 1.15 if angle_delta > 0 else 1 / 1.15
        self._apply_zoom(factor)
        event.accept()

    # ------------------------------------------------------------------ Helpers
    def _apply_zoom(self, scale_factor: float) -> None:
        new_zoom = self._zoom * scale_factor
        new_zoom = max(self._min_zoom, min(self._max_zoom, new_zoom))
        scale_factor = new_zoom / self._zoom
        if abs(scale_factor - 1.0) < 1e-3:
            return
        self.scale(scale_factor, scale_factor)
        self._zoom = new_zoom
