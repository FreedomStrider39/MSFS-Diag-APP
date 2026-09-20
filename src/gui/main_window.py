from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QLabel, QVBoxLayout, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ..services.hardware import HardwareInfo
from ..services.config_parser import ConfigParser
from ..services.crash_reader import CrashReader
from ..services.mod_scanner import ModScanner
from ..services.ai_service import AIService
from ..services.tuner import ConfigTuner
from .styles import DARK_STYLESHEET
from .tabs.dashboard_tab import DashboardTab
from .tabs.config_tab import ConfigTab
from .tabs.crash_tab import CrashTab
from .tabs.mods_tab import ModsTab
from .tabs.library_tab import LibraryTab
from .tabs.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSFS Diagnostics")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)

        self.hardware = HardwareInfo()
        self.config = ConfigParser()
        self.crash_reader = CrashReader()
        self.mod_scanner = ModScanner()
        self.ai_service = AIService()
        self.tuner = ConfigTuner()

        self.setStyleSheet(DARK_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel("MSFS Diagnostics")
        header.setProperty("class", "title")
        header.setAlignment(Qt.AlignCenter)
        font = header.font()
        font.setPointSize(18)
        font.setBold(True)
        header.setFont(font)
        layout.addWidget(header)

        subtitle = QLabel("Flight Simulator Crash Diagnostics & Config Tuner")
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self.dashboard_tab = DashboardTab(self)
        self.config_tab = ConfigTab(self)
        self.crash_tab = CrashTab(self)
        self.mods_tab = ModsTab(self)
        self.library_tab = LibraryTab(self)
        self.settings_tab = SettingsTab(self)

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.config_tab, "Config Tuner")
        self.tabs.addTab(self.crash_tab, "Crash Diagnostics")
        self.tabs.addTab(self.mods_tab, "Mod Inspector")
        self.tabs.addTab(self.library_tab, "Error Library")
        self.tabs.addTab(self.settings_tab, "Settings")

        layout.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self._update_status_timer = QTimer()
        self._update_status_timer.timeout.connect(self._update_status)
        self._update_status_timer.start(5000)

        self._update_status()

    def _update_status(self):
        try:
            info = self.hardware.get_all()
            self.status_bar.showMessage(
                f"{info.gpu.name} | {info.ram_total_gb} GB RAM"
            )
        except Exception:
            self.status_bar.showMessage("Ready")
