"""Qt 适配工具，将 Matplotlib Figure 嵌入 Qt 组件。"""

from __future__ import annotations

import io
from importlib import import_module
from typing import Any, Optional, Tuple

from matplotlib.figure import Figure

__all__ = [
    "figure_to_png_bytes",
    "figure_to_qimage",
    "figure_to_pixmap",
    "ensure_qt_available",
]

_QT_TYPES: Optional[Tuple[Any, Any]] = None


def figure_to_png_bytes(
    figure: Figure,
    *,
    dpi: int = 110,
    transparent: bool = False,
) -> bytes:
    """
    将 Matplotlib Figure 渲染为 PNG 字节串。

    参数：
        figure: 需要导出的 Matplotlib Figure。
        dpi: 输出分辨率（默认 110）。
        transparent: 是否导出透明背景。
    """

    buffer = io.BytesIO()

    canvas = getattr(figure, "canvas", None)
    if canvas is not None:
        try:
            canvas.draw()
        except Exception:
            # 离屏渲染失败时继续走 savefig
            pass

    figure.savefig(
        buffer,
        format="png",
        dpi=dpi,
        bbox_inches="tight",
        transparent=transparent,
    )
    return buffer.getvalue()


def ensure_qt_available() -> Tuple[Any, Any]:
    """
    查找可用的 Qt 绑定（PySide6 / PyQt6 / PyQt5）。

    返回：
        (QImage, QPixmap) 类元组。

    抛出：
        RuntimeError: 当未安装任何受支持的 Qt 绑定时。
    """

    global _QT_TYPES
    if _QT_TYPES is not None:
        return _QT_TYPES

    candidates = (
        ("PySide6.QtGui", "PySide6"),
        ("PyQt6.QtGui", "PyQt6"),
        ("PyQt5.QtGui", "PyQt5"),
    )
    for module_name, label in candidates:
        try:
            module = import_module(module_name)
        except ModuleNotFoundError:
            continue

        qimage = getattr(module, "QImage", None)
        qpixmap = getattr(module, "QPixmap", None)
        if qimage is None or qpixmap is None:
            continue

        _QT_TYPES = (qimage, qpixmap)
        return _QT_TYPES

    raise RuntimeError(
        "未检测到 Qt 绑定。请安装 PySide6、PyQt6 或 PyQt5 后再试。"
    )


def figure_to_qimage(
    figure: Figure,
    *,
    dpi: int = 110,
    transparent: bool = False,
) -> Any:
    """
    将 Figure 转换为 QImage。

    抛出：
        RuntimeError: 当 Qt 未安装或转换失败时。
    """

    qimage_cls, _ = ensure_qt_available()
    png_bytes = figure_to_png_bytes(
        figure,
        dpi=dpi,
        transparent=transparent,
    )
    image = qimage_cls.fromData(png_bytes, "PNG")
    if getattr(image, "isNull", lambda: False)():
        raise RuntimeError("无法将 Matplotlib 图像转换为 QImage。")
    return image


def figure_to_pixmap(
    figure: Figure,
    *,
    dpi: int = 110,
    transparent: bool = False,
) -> Any:
    """
    将 Figure 转换为 QPixmap，适合直接绑定到 QLabel/QGraphicsView。
    """

    qimage_cls, qpixmap_cls = ensure_qt_available()
    png_bytes = figure_to_png_bytes(
        figure,
        dpi=dpi,
        transparent=transparent,
    )
    image = qimage_cls.fromData(png_bytes, "PNG")
    if getattr(image, "isNull", lambda: False)():
        raise RuntimeError("无法将 Matplotlib 图像转换为 QImage/QPixmap。")
    return qpixmap_cls.fromImage(image)

