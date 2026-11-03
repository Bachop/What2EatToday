"""Application bootstrap, local data paths, logging and process lifecycle."""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QStandardPaths, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from .repository import LunchRepository
from .service import LunchService
from .ui.main_window import MainWindow
from .ui.theme import STYLESHEET


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="今天吃什么 · 午餐选择器")
    parser.add_argument("--data-dir", type=Path, help="指定数据目录（默认使用系统应用数据目录）")
    args = parser.parse_args(argv)
    app = QApplication([sys.argv[0]])
    app.setApplicationName("What2EatToday")
    app.setOrganizationName("SilverTools")
    QLocale.setDefault(QLocale(QLocale.Language.Chinese, QLocale.Country.China))
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet(STYLESHEET)
    data_dir = args.data_dir or Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=data_dir / "application.log", encoding="utf-8", level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
        repository = LunchRepository(data_dir / "lunch.db")
    except (OSError, sqlite3.Error) as error:
        QMessageBox.critical(
            None, "无法打开午餐数据",
            f"数据目录：{data_dir}\n\n{error}\n\n请检查目录权限，或备份数据后恢复有效的数据库文件。",
        )
        return 1
    try:
        window = MainWindow(LunchService(repository))
        window.show()
        QTimer.singleShot(0, window.start_setup)
        return app.exec()
    finally:
        repository.close()
