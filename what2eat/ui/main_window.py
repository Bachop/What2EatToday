"""Primary lunch screen; all mutations are delegated to the application service."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from ..dates import is_workday
from ..service import LunchService
from .calendar import CalendarDialog
from .common import button, label, run_action
from .options import AddOptionsDialog, OptionsDialog


class MainWindow(QMainWindow):
    def __init__(self, service: LunchService) -> None:
        super().__init__()
        self.service = service
        self.displayed_day = service.now().date()
        self.setWindowTitle("今天吃什么 · 午餐选择器")
        self.resize(900, 680)
        self.setMinimumSize(720, 580)
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(38, 30, 38, 28)
        layout.setSpacing(20)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("WHAT TO EAT TODAY", "eyebrow"))
        titles.addWidget(label("把午餐，交给一点惊喜。", "title"))
        header.addLayout(titles, 1)
        header.addWidget(button("午餐日历", self.open_calendar))
        layout.addLayout(header)
        self.date_label = label("", "muted")
        layout.addWidget(self.date_label)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(34, 28, 34, 30)
        hero_layout.setSpacing(18)
        self.caption = label("今天的午餐", "eyebrow")
        hero_layout.addWidget(self.caption, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.result = label("准备好开饭了吗？", "result", wrap=True)
        self.result.setTextFormat(Qt.TextFormat.PlainText)
        self.result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result.setMinimumHeight(100)
        hero_layout.addWidget(self.result, 1)
        self.hint = label("点击下方按钮，选出今天想吃的一餐。", "muted", wrap=True)
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.hint)
        action_row = QHBoxLayout()
        action_row.addStretch()
        self.choose_button = button("帮我选午餐", self.choose, "primary")
        self.choose_button.setMinimumWidth(220)
        action_row.addWidget(self.choose_button)
        action_row.addStretch()
        hero_layout.addLayout(action_row)
        self.status = label("", "status", wrap=True)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.status)
        layout.addWidget(hero, 1)

        options_heading = QHBoxLayout()
        self.options_label = label("午餐清单", "section")
        options_heading.addWidget(self.options_label)
        options_heading.addStretch()
        options_heading.addWidget(button("管理选项", self.manage_options))
        layout.addLayout(options_heading)
        self.preview = label("", "muted", wrap=True)
        self.preview.setTextFormat(Qt.TextFormat.PlainText)
        self.preview.setMinimumHeight(48)
        layout.addWidget(self.preview)
        layout.addWidget(label("按偏好随机选择 · 工作日自动避免过度重复 · 每天保留最终结果", "eyebrow", wrap=True))
        self.refresh()
        self.timer = QTimer(self)
        self.timer.setInterval(30_000)
        self.timer.timeout.connect(self.check_day)
        self.timer.start()

    def start_setup(self) -> None:
        if not self.service.options():
            AddOptionsDialog(self.service, self, first_run=True).exec()
            self.refresh()

    def refresh(self) -> None:
        today = self.service.now().date()
        self.displayed_day = today
        weekday = "一二三四五六日"[today.weekday()]
        self.date_label.setText(
            f"{today.year} 年 {today.month} 月 {today.day} 日 · 星期{weekday} · "
            + ("工作日" if is_workday(today) else "周末，自由选择")
        )
        options = self.service.options()
        self.options_label.setText(f"午餐清单 · {len(options)} 项")
        preview = "  /  ".join(option.name for option in options[:8])
        self.preview.setText(preview + (f"  /  还有 {len(options) - 8} 项…" if len(options) > 8 else "")
                             if options else "还没有选项。点击「管理选项」，添加你想吃的午餐。")
        record = self.service.today_record()
        if record is None:
            self.result.setText("准备好开饭了吗？" if options else "先加几道想吃的吧")
            self.caption.setText("今天的午餐")
            self.hint.setText("点击下方按钮，选出今天想吃的一餐。")
            self.choose_button.setText("帮我选午餐" if options else "添加午餐选项")
            self.choose_button.setEnabled(True)
            self.status.setText("")
        else:
            self.result.setText(record.option_name)
            self.caption.setText("今天就吃")
            self.hint.setText("已自动保存到午餐日历。祝你吃得开心。")
            self.choose_button.setText("再选一次" if record.remaining_rerolls else "今天的重选机会已用完")
            self.choose_button.setEnabled(bool(options) and record.remaining_rerolls > 0)
            self.status.setText(f"今天还可以重选 {record.remaining_rerolls} 次。" if record.rerolls else "")

    def check_day(self) -> None:
        if self.displayed_day != self.service.now().date():
            run_action(self, self.refresh)

    def choose(self) -> None:
        run_action(self, self._choose)

    def _choose(self) -> None:
        if self.displayed_day != self.service.now().date():
            self.refresh()
            return
        if not self.service.options():
            self.start_setup()
            return
        record = self.service.today_record()
        if record is not None and record.rerolls >= 1:
            response = QMessageBox.question(
                self, "再选一次午餐",
                f"今天剩余 {record.remaining_rerolls} 次重选机会，本次将使用 1 次。\n"
                "符合规则的其他选项不足时，可能得到相同结果。继续吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                return
            if self.displayed_day != self.service.now().date():
                self.refresh()
                return
        self.service.choose(reroll=record is not None)
        self.refresh()

    def manage_options(self) -> None:
        def action() -> None:
            OptionsDialog(self.service, self).exec()
            self.refresh()
        run_action(self, action)

    def open_calendar(self) -> None:
        run_action(self, lambda: CalendarDialog(self.service, self).exec())
