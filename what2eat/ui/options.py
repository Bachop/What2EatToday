"""First-run setup, option management and optional preference editing."""

from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QDoubleSpinBox, QHBoxLayout,
    QHeaderView, QMessageBox, QPlainTextEdit, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..models import FoodOption
from ..service import LunchService
from ..weights import equal_weights, redistribute_weight
from .common import button, label, run_action


class AddOptionsDialog(QDialog):
    def __init__(self, service: LunchService, parent: QWidget | None = None, *, first_run: bool = False) -> None:
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("欢迎 · 今天吃什么" if first_run else "添加午餐选项")
        self.resize(470, 430)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)
        layout.addWidget(label("先放进几道你想吃的午餐" if first_run else "添加想吃的午餐", "section"))
        layout.addWidget(label("每行填写一个选项，最多 40 个字符。以后随时可以添加或删除。", "muted", wrap=True))
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("optionNames")
        self.editor.setPlaceholderText("例如：\n番茄牛腩饭\n牛肉面\n轻食沙拉\n食堂")
        layout.addWidget(self.editor)
        self.submit = button("保存，开始选午餐" if first_run else "添加选项", self.save, "primary")
        layout.addWidget(self.submit)
        cancel = button("稍后再填" if first_run else "取消", self.reject)
        layout.addWidget(cancel)

    def save(self) -> None:
        if run_action(self, lambda: self.service.add_options(self.editor.toPlainText().splitlines())):
            self.accept()


class WeightDialog(QDialog):
    def __init__(self, service: LunchService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.options: list[FoodOption] = service.options()
        self.weights = [option.weight for option in self.options]
        self.setWindowTitle("偏好权重")
        self.resize(510, 540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(label("给更想吃的，多一点机会", "section"))
        layout.addWidget(label(
            "选中一项，再修改它的百分比；其余选项按原比例分配剩余权重。\n"
            "防重复规则优先于权重；所有选项的权重必须大于 0。", "muted", wrap=True,
        ))
        self.table = QTableWidget(len(self.options), 2)
        self.table.setHorizontalHeaderLabels(["午餐选项", "权重"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        layout.addWidget(self.table)
        row = QHBoxLayout()
        row.addWidget(label("所选选项："))
        self.spin = QDoubleSpinBox()
        self.spin.setObjectName("weightPercent")
        self.spin.setDecimals(6)
        self.spin.setRange(0.000001, 99.999999)
        self.spin.setSingleStep(1)
        self.spin.setSuffix(" %")
        self.spin.setKeyboardTracking(False)
        row.addWidget(self.spin, 1)
        layout.addLayout(row)
        layout.addWidget(label("权重合计：100%（即 1）", "muted"))
        actions = QHBoxLayout()
        actions.addWidget(button("恢复均等", self.equalize))
        actions.addStretch()
        actions.addWidget(button("取消", self.reject))
        actions.addWidget(button("保存权重", self.save, "primary"))
        layout.addLayout(actions)
        self.table.itemSelectionChanged.connect(self.sync_spin)
        self.spin.valueChanged.connect(self.change_weight)
        self.render()
        if self.options:
            self.table.selectRow(0)
        self.spin.setEnabled(len(self.options) > 1)

    def render(self) -> None:
        for row, (option, weight) in enumerate(zip(self.options, self.weights)):
            self.table.setItem(row, 0, QTableWidgetItem(option.name))
            self.table.setItem(row, 1, QTableWidgetItem(f"{weight * 100:.6f}%"))

    def sync_spin(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.spin.blockSignals(True)
            if len(self.options) == 1:
                self.spin.setMaximum(100)
            self.spin.setValue(self.weights[row] * 100)
            self.spin.blockSignals(False)

    def change_weight(self, percent: float) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        self.weights = redistribute_weight(self.weights, row, percent / 100)
        self.table.blockSignals(True)
        self.render()
        self.table.blockSignals(False)

    def equalize(self) -> None:
        self.weights = equal_weights(len(self.options))
        self.table.blockSignals(True)
        self.render()
        self.table.blockSignals(False)
        self.sync_spin()

    def save(self) -> None:
        values = {option.id: weight for option, weight in zip(self.options, self.weights)}
        if run_action(self, lambda: self.service.set_weights(values)):
            self.accept()


class OptionsDialog(QDialog):
    def __init__(self, service: LunchService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.options: list[FoodOption] = []
        self.setWindowTitle("管理午餐选项")
        self.resize(560, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(label("你的午餐清单", "section"))
        layout.addWidget(label("支持多选删除。删除选项后，日历中的历史记录会继续保留。", "muted", wrap=True))
        self.table = QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels(["午餐选项"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        actions.addWidget(button("添加选项", self.add))
        self.delete_button = button("删除所选", self.delete, "danger")
        actions.addWidget(self.delete_button)
        actions.addStretch()
        self.weight_button = button("偏好权重…", self.edit_weights)
        actions.addWidget(self.weight_button)
        layout.addLayout(actions)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        box.rejected.connect(self.accept)
        box.button(QDialogButtonBox.StandardButton.Close).setText("完成")
        layout.addWidget(box)
        self.table.itemSelectionChanged.connect(self.update_buttons)
        self.refresh()

    def refresh(self) -> None:
        self.options = self.service.options()
        self.table.setRowCount(len(self.options))
        for row, option in enumerate(self.options):
            self.table.setItem(row, 0, QTableWidgetItem(option.name))
        self.update_buttons()

    def update_buttons(self) -> None:
        self.delete_button.setEnabled(bool(self.table.selectionModel().selectedRows()))
        self.weight_button.setEnabled(bool(self.options))

    def add(self) -> None:
        AddOptionsDialog(self.service, self).exec()
        self.refresh()

    def delete(self) -> None:
        ids = [self.options[item.row()].id for item in self.table.selectionModel().selectedRows()]
        if not ids:
            return
        if QMessageBox.question(
            self, "删除选项", f"删除选中的 {len(ids)} 个选项？历史午餐记录会保留。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            if run_action(self, lambda: self.service.delete_options(ids)):
                self.refresh()

    def edit_weights(self) -> None:
        WeightDialog(self.service, self).exec()
