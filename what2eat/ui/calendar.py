"""One-month calendar with persistent per-option colors and daily details."""

import calendar
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGridLayout, QHBoxLayout, QPushButton, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget,
)

from ..models import LunchRecord
from ..service import LunchService
from .common import button, label, run_action


class CalendarDialog(QDialog):
    def __init__(self, service: LunchService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.records: dict[date, LunchRecord] = {}
        today = service.now().date()
        self.year, self.month = today.year, today.month
        self.setWindowTitle("午餐日历")
        self.resize(850, 660)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        heading = QHBoxLayout()
        heading.addWidget(label("每一餐，都有迹可循", "section"))
        heading.addStretch()
        heading.addWidget(button("回到本月", self.go_today))
        layout.addLayout(heading)
        navigation = QHBoxLayout()
        self.prev_button = button("‹ 上个月", lambda: self.shift_month(-1))
        navigation.addWidget(self.prev_button)
        navigation.addStretch()
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 9998)
        self.year_spin.setSuffix(" 年")
        self.month_combo = QComboBox()
        self.month_combo.addItems([f"{month} 月" for month in range(1, 13)])
        navigation.addWidget(self.year_spin)
        navigation.addWidget(self.month_combo)
        navigation.addStretch()
        self.next_button = button("下个月 ›", lambda: self.shift_month(1))
        navigation.addWidget(self.next_button)
        layout.addLayout(navigation)
        self.grid = QGridLayout()
        self.grid.setSpacing(5)
        for column, name in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
            heading_label = label(f"周{name}", "muted")
            heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(heading_label, 0, column)
            self.grid.setColumnStretch(column, 1)
        self.cells: list[QPushButton] = []
        for position in range(42):
            cell = QPushButton()
            cell.setMinimumSize(86, 62)
            cell.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            cell.clicked.connect(lambda checked=False, index=position: self.show_details(index))
            self.cells.append(cell)
            self.grid.addWidget(cell, position // 7 + 1, position % 7)
            self.grid.setRowStretch(position // 7 + 1, 1)
        layout.addLayout(self.grid, 1)
        self.details = label("点击日期可查看完整午餐名称。灰色日期表示没有选择记录。", "muted", wrap=True)
        self.details.setMinimumHeight(44)
        self.details.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.details)
        layout.addWidget(label("颜色对应午餐选项；删除选项后，历史名称和颜色仍会保留。", "muted", wrap=True))
        self.year_spin.valueChanged.connect(self.controls_changed)
        self.month_combo.currentIndexChanged.connect(self.controls_changed)
        self.refresh()

    def controls_changed(self) -> None:
        self.year = self.year_spin.value()
        self.month = self.month_combo.currentIndex() + 1
        run_action(self, self.refresh)

    def shift_month(self, offset: int) -> None:
        serial = self.year * 12 + self.month - 1 + offset
        year, zero_month = divmod(serial, 12)
        if 1900 <= year <= 9998:
            self.year, self.month = year, zero_month + 1
            run_action(self, self.refresh)

    def go_today(self) -> None:
        today = self.service.now().date()
        self.year, self.month = today.year, today.month
        run_action(self, self.refresh)

    def refresh(self) -> None:
        self.records = {record.day: record for record in self.service.month_records(self.year, self.month)}
        self.year_spin.blockSignals(True)
        self.month_combo.blockSignals(True)
        self.year_spin.setValue(self.year)
        self.month_combo.setCurrentIndex(self.month - 1)
        self.year_spin.blockSignals(False)
        self.month_combo.blockSignals(False)
        self.prev_button.setEnabled((self.year, self.month) > (1900, 1))
        self.next_button.setEnabled((self.year, self.month) < (9998, 12))
        weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(self.year, self.month)
        days = [day for week in weeks for day in week]
        days.extend([0] * (42 - len(days)))
        today = self.service.now().date()
        for cell, number in zip(self.cells, days):
            cell.setProperty("day", number)
            cell.setVisible(number != 0)
            cell.setEnabled(number != 0)
            if not number:
                continue
            day = date(self.year, self.month, number)
            record = self.records.get(day)
            border = "2px solid #285d49" if day == today else "1px solid #e0e4da"
            if record:
                color = QColor(record.color)
                background = color.lighter(178).name()
                cell.setText(f"{number}\n{record.option_name[:7]}{'…' if len(record.option_name) > 7 else ''}")
                cell.setToolTip(f"{day.isoformat()}  {record.option_name}")
                cell.setStyleSheet(
                    f"QPushButton {{ background: {background}; color: #253b35; border: {border}; "
                    f"border-left: 5px solid {record.color}; padding: 4px; min-height: 48px; border-radius: 7px; }}"
                    "QPushButton:hover { background: #e2ecde; }"
                )
            else:
                cell.setText(str(number))
                cell.setToolTip(f"{day.isoformat()}  没有选择记录")
                cell.setStyleSheet(
                    f"QPushButton {{ background: #efefea; color: #92978f; border: {border}; "
                    "padding: 4px; min-height: 48px; border-radius: 7px; }"
                    "QPushButton:hover { background: #e5e8e0; }"
                )
        self.details.setText(f"{self.year} 年 {self.month} 月 · 记录了 {len(self.records)} 天午餐。点击日期查看详情。")

    def show_details(self, index: int) -> None:
        number = self.cells[index].property("day")
        if not number:
            return
        day = date(self.year, self.month, number)
        record = self.records.get(day)
        if record is None:
            self.details.setText(f"{day.isoformat()} · 没有使用本程序选择午餐。")
        else:
            self.details.setText(f"{day.isoformat()} · {record.option_name}\n当天重选 {record.rerolls} 次，日历保留最终结果。")
