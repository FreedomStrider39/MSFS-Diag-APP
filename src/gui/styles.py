DARK_STYLESHEET = """
QMainWindow {
    background-color: #0a0f1a;
}

QWidget {
    background-color: #0a0f1a;
    color: #f0f4f8;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0e1424;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #1a2332;
    color: #94a3b8;
    padding: 10px 22px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 120px;
    font-weight: 500;
    border: 1px solid #1e293b;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #0e1424;
    color: #f97316;
    font-weight: bold;
    border-color: #f97316;
}

QTabBar::tab:hover {
    background-color: #1e293b;
    color: #f0f4f8;
}

QPushButton {
    background-color: #f97316;
    color: #ffffff;
    border: none;
    padding: 9px 22px;
    border-radius: 6px;
    font-weight: bold;
    min-height: 20px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #fb923c;
}

QPushButton:pressed {
    background-color: #ea580c;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748b;
}

QPushButton.secondary {
    background-color: transparent;
    border: 1.5px solid #f97316;
    color: #f97316;
}

QPushButton.secondary:hover {
    background-color: #f97316;
    color: #ffffff;
}

QPushButton.success {
    background-color: #22c55e;
}

QPushButton.success:hover {
    background-color: #4ade80;
}

QPushButton.warning {
    background-color: #f59e0b;
    color: #000000;
}

QPushButton.warning:hover {
    background-color: #fbbf24;
}

QLabel {
    color: #f0f4f8;
}

QLabel.title {
    font-size: 20px;
    font-weight: bold;
    color: #f97316;
}

QLabel.subtitle {
    font-size: 14px;
    color: #94a3b8;
}

QLabel.card-label {
    background-color: #0e1424;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #1e293b;
}

QLineEdit {
    background-color: #1a2332;
    border: 1.5px solid #1e293b;
    padding: 9px 14px;
    border-radius: 6px;
    color: #f0f4f8;
    selection-background-color: #f97316;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1.5px solid #f97316;
}

QTextEdit, QPlainTextEdit {
    background-color: #0a0f1a;
    border: 1.5px solid #1e293b;
    padding: 10px;
    border-radius: 6px;
    color: #e2e8f0;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}

QComboBox {
    background-color: #1a2332;
    border: 1.5px solid #1e293b;
    padding: 9px 14px;
    border-radius: 6px;
    color: #f0f4f8;
    min-height: 20px;
    font-size: 13px;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #94a3b8;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1a2332;
    border: 1px solid #1e293b;
    color: #f0f4f8;
    selection-background-color: #f97316;
    border-radius: 4px;
}

QProgressBar {
    background-color: #1a2332;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: #f0f4f8;
    min-height: 22px;
    font-weight: bold;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f97316, stop:1 #fb923c);
    border-radius: 6px;
}

QScrollBar:vertical {
    background-color: #0a0f1a;
    width: 10px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #f97316;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #0a0f1a;
    height: 10px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #334155;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #f97316;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QGroupBox {
    border: 1.5px solid #1e293b;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 18px;
    font-weight: bold;
    color: #f97316;
    font-size: 13px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    background-color: #0e1424;
    border-radius: 4px;
}

QCheckBox {
    spacing: 8px;
    color: #f0f4f8;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #334155;
    background-color: #0a0f1a;
}

QCheckBox::indicator:checked {
    background-color: #22c55e;
    border-color: #22c55e;
}

QListWidget {
    background-color: #0a0f1a;
    border: 1.5px solid #1e293b;
    border-radius: 6px;
    color: #e2e8f0;
    padding: 5px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
    margin: 1px;
}

QListWidget::item:selected {
    background-color: #1a2332;
    color: #f97316;
    border-left: 3px solid #f97316;
}

QListWidget::item:hover {
    background-color: #1e293b;
}

QSplitter::handle {
    background-color: #1e293b;
    border-radius: 2px;
}

QStatusBar {
    background-color: #0e1424;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
    font-size: 12px;
}

QToolTip {
    background-color: #1a2332;
    color: #f0f4f8;
    border: 1px solid #f97316;
    padding: 8px;
    border-radius: 6px;
    font-size: 12px;
}

QHeaderView::section {
    background-color: #0e1424;
    color: #f97316;
    padding: 6px;
    border: 1px solid #1e293b;
    font-weight: bold;
}

QMenu {
    background-color: #1a2332;
    color: #f0f4f8;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #f97316;
    color: #ffffff;
}

QMenuBar {
    background-color: #0e1424;
    color: #f0f4f8;
    border-bottom: 1px solid #1e293b;
}

QMenuBar::item:selected {
    background-color: #1a2332;
    color: #f97316;
}

QSpinBox, QDoubleSpinBox {
    background-color: #1a2332;
    border: 1.5px solid #1e293b;
    padding: 6px 10px;
    border-radius: 6px;
    color: #f0f4f8;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1.5px solid #f97316;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background-color: #1e293b;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #f97316;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background-color: #fb923c;
}

QSlider::sub-page:horizontal {
    background-color: #f97316;
    border-radius: 3px;
}
"""
