"""Small reusable widget and error-handling helpers."""

import logging
import sqlite3
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QWidget

from ..models import LunchError


def label(text: str, object_name: str = "", *, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(object_name)
    widget.setWordWrap(wrap)
    return widget


def button(text: str, callback: Callable, object_name: str = "") -> QPushButton:
    widget = QPushButton(text)
    widget.setObjectName(object_name)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.clicked.connect(callback)
    return widget


def run_action(parent: QWidget, action: Callable[[], object]) -> bool:
    try:
        action()
        return True
    except LunchError as error:
        QMessageBox.information(parent, "请检查输入", str(error))
    except (sqlite3.Error, OSError):
        logging.exception("Could not access lunch data")
        QMessageBox.warning(
            parent, "数据暂时无法保存",
            "请检查数据目录的访问权限和可用空间，并关闭正在占用数据文件的其他程序。\n"
            "本次操作没有完成，请稍后重试。",
        )
    return False
