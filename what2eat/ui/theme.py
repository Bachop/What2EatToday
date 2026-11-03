"""A compact, consistent desktop theme with standard accessible Qt controls."""

STYLESHEET = """
QWidget { font-family: 'Microsoft YaHei UI', 'Microsoft YaHei', sans-serif;
          font-size: 14px; color: #253b35; }
QMainWindow, QDialog { background: #f7f6f0; }
QLabel { background: transparent; }
QLabel#eyebrow { color: #78877d; font-size: 12px; font-weight: 600; }
QLabel#title { font-size: 30px; font-weight: 700; }
QLabel#result { font-size: 38px; font-weight: 700; color: #214f40; }
QLabel#muted { color: #7a837c; }
QLabel#section { font-size: 18px; font-weight: 600; }
QLabel#status { color: #a36323; }
QFrame#hero { background: #ffffff; border: 1px solid #e3e7dd; border-radius: 20px; }
QPushButton { background: #ffffff; border: 1px solid #d8ded4; border-radius: 8px;
              padding: 10px 18px; min-height: 20px; }
QPushButton:hover { background: #edf2e9; border-color: #9fb49f; }
QPushButton:pressed { background: #dce8d7; }
QPushButton:disabled { background: #efeee9; color: #a7aaa3; border-color: #e2e3db; }
QPushButton#primary { background: #285d49; color: white; border: none; font-weight: 600;
                       padding: 14px 28px; }
QPushButton#primary:hover { background: #36765e; }
QPushButton#primary:disabled { background: #a2b4a7; color: #f6f7f4; }
QPushButton#danger { color: #a04435; }
QPlainTextEdit, QTableWidget, QListWidget { background: #ffffff; border: 1px solid #d8ded4;
                                        border-radius: 8px; padding: 6px; }
QTableWidget { selection-background-color: #e0eddf; selection-color: #214f40; }
QHeaderView::section { background: #eef1e9; border: none; padding: 9px; font-weight: 600; }
QDoubleSpinBox, QSpinBox, QComboBox { background: white; border: 1px solid #d8ded4;
                                   border-radius: 5px; padding: 7px; min-height: 22px; }
QToolTip { background: #253b35; color: #ffffff; padding: 6px; border: none; }
"""
