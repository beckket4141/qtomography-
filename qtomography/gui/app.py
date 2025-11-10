from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from PySide6 import QtWidgets

from .main_window import MainWindow


def ensure_stylesheet(app: QtWidgets.QApplication) -> None:
    """Apply a minimal stylesheet for consistent spacing (optional)."""

    app.setStyleSheet(
        """
        QWidget {
            font-size: 11pt;
        }
        QGroupBox {
            font-weight: bold;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
        }
        """
    )


def setup_logging() -> None:
    """Configure logging for GUI application.
    
    Logs are saved to the user's home directory under ~/.qtomography/logs/
    to ensure they can be written even when the application is packaged.
    """
    # 使用用户目录存储日志（与配置文件保持一致）
    # 这样打包后也能正常写入日志
    log_dir = Path.home() / ".qtomography" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "qtomography_gui.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 设置matplotlib日志级别（减少警告）
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def main(argv: Optional[list[str]] = None) -> int:
    """
    Launch the QTomography GUI application.

    Parameters
    ----------
    argv:
        Optional command-line arguments. Defaults to ``sys.argv``.
    """
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("启动QTomography GUI应用")

    if argv is None:
        argv = sys.argv

    try:
        app = QtWidgets.QApplication(argv)
        ensure_stylesheet(app)

        window = MainWindow()
        window.show()
        logger.info("GUI窗口已显示")
        return app.exec()
    except Exception as e:
        logger.error(f"GUI启动失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
