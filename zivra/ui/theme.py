STYLE = """
* { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #F5F5F5; }
QMainWindow, QWidget#shell { background: #08090B; }
QWidget { background: #111317; }
QLabel { background: transparent; }
QLabel#title { font-size: 30px; font-weight: 600; letter-spacing: 3px; }
QLabel#subtitle { color: #A1A1AA; }
QLabel#metric { font-size: 21px; padding: 18px; background: #191C21; border: 1px solid #30343B; border-radius: 8px; }
QPushButton { background: #191C21; border: 1px solid #30343B; border-radius: 6px; padding: 10px 14px; }
QPushButton:hover { background: #30343B; border-color: #737780; }
QPushButton:pressed { background: #484C53; }
QPushButton:disabled { color: #737780; }
QPushButton#primary { background: #F5F5F5; color: #08090B; font-weight: 600; }
QPushButton#primary:hover { background: #C8CAD0; }
QLineEdit, QTextBrowser, QTableWidget, QListWidget { background: #191C21; border: 1px solid #30343B; border-radius: 6px; padding: 8px; selection-background-color: #484C53; }
QLineEdit:focus { border-color: #A1A1AA; }
QListWidget { min-width: 180px; max-width: 210px; background: #111317; border: 0; }
QListWidget::item { padding: 12px 8px; border-radius: 5px; color: #A1A1AA; }
QListWidget::item:selected { background: #30343B; color: #F5F5F5; }
QCheckBox { padding: 6px 0; }
QStatusBar { color: #A1A1AA; background: #08090B; }
QHeaderView::section { background: #111317; padding: 8px; border: 0; }
QScrollBar:vertical { background: #111317; width: 10px; }
QScrollBar::handle:vertical { background: #484C53; min-height: 30px; }
"""
