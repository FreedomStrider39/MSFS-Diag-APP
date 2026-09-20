from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QGridLayout, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal


class HardwareWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, hardware):
        super().__init__()
        self.hardware = hardware

    def run(self):
        try:
            summary = self.hardware.get_summary()
            self.finished.emit(summary)
        except Exception as e:
            self.error.emit(str(e))


class DashboardTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        admin_group = QGroupBox("System Status")
        admin_layout = QHBoxLayout()

        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            is_admin = False

        self.admin_label = QLabel()
        if is_admin:
            self.admin_label.setText("Running as Administrator")
            self.admin_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 5px;")
        else:
            self.admin_label.setText("Running as Standard User (some features may need admin)")
            self.admin_label.setStyleSheet("color: #f39c12; padding: 5px;")
        self.admin_label.setWordWrap(True)
        admin_layout.addWidget(self.admin_label)
        admin_layout.addStretch()
        admin_group.setLayout(admin_layout)
        layout.addWidget(admin_group)

        hw_group = QGroupBox("System Hardware")
        hw_layout = QVBoxLayout()

        self.hw_info_label = QLabel("Loading hardware info...")
        self.hw_info_label.setWordWrap(True)
        self.hw_info_label.setStyleSheet("font-family: 'Cascadia Code', monospace; padding: 10px;")
        hw_layout.addWidget(self.hw_info_label)

        refresh_btn = QPushButton("Refresh Hardware Info")
        refresh_btn.clicked.connect(self._refresh_hardware)
        hw_layout.addWidget(refresh_btn)

        hw_group.setLayout(hw_layout)
        layout.addWidget(hw_group)

        status_group = QGroupBox("Simulator Status")
        status_layout = QVBoxLayout()

        self.config_status = QLabel("Checking config...")
        self.config_status.setWordWrap(True)
        status_layout.addWidget(self.config_status)

        btn_row = QHBoxLayout()
        detect_btn = QPushButton("Detect MSFS Install")
        detect_btn.setProperty("class", "secondary")
        detect_btn.clicked.connect(self._detect_msfs)
        btn_row.addWidget(detect_btn)

        community_btn = QPushButton("Open Community Folder")
        community_btn.setProperty("class", "secondary")
        community_btn.clicked.connect(self._open_community)
        btn_row.addWidget(community_btn)

        status_layout.addLayout(btn_row)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        donate_group = QGroupBox("Support the Project")
        donate_layout = QVBoxLayout()

        donate_label = QLabel(
            "MSFS Diagnostics is free and open-source.\n"
            "If this tool helps you, consider supporting development!"
        )
        donate_label.setWordWrap(True)
        donate_layout.addWidget(donate_label)

        donate_row = QHBoxLayout()

        donate_btn = QPushButton("Donate via PayPal")
        donate_btn.setProperty("class", "warning")
        donate_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://paypal.me/your-paypal")))
        donate_row.addWidget(donate_btn)

        github_btn = QPushButton("Star on GitHub")
        github_btn.setProperty("class", "secondary")
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/FreedomStrider39/MSFS-Diag-APP")))
        donate_row.addWidget(github_btn)

        donate_row.addStretch()
        donate_layout.addLayout(donate_row)

        donate_group.setLayout(donate_layout)
        layout.addWidget(donate_group)

        layout.addStretch()
        self._refresh_hardware()

    def _refresh_hardware(self):
        self.hw_info_label.setText("Scanning hardware...")
        self.worker = HardwareWorker(self.mw.hardware)
        self.worker.finished.connect(self._on_hardware_ready)
        self.worker.error.connect(self._on_hardware_error)
        self.worker.start()

    def _on_hardware_ready(self, summary):
        self.hw_info_label.setText(summary)
        self._check_config()

    def _on_hardware_error(self, error):
        self.hw_info_label.setText(f"Error scanning hardware: {error}")

    def _check_config(self):
        path = self.mw.config.find_usercfg()
        if path and path.exists():
            settings = self.mw.config.parse()
            tier = self.mw.tuner.determine_tier()
            self.config_status.setText(
                f"UserCfg.opt found: {path}\n"
                f"Render Scale: {settings.render_scale} | "
                f"Texture: {settings.texture_res} | "
                f"Shadows: {settings.shadows}\n"
                f"Detected Performance Tier: {tier.upper()}"
            )
        else:
            self.config_status.setText(
                "UserCfg.opt not found. Click 'Detect MSFS Install' to locate your simulator."
            )

    def _detect_msfs(self):
        path = self.mw.config.find_msfs_path()
        if path:
            self.config_status.setText(f"MSFS found at: {path}")
            self._check_config()
            self.mw.status_bar.showMessage(f"MSFS detected at {path}", 5000)
        else:
            self.config_status.setText(
                "Could not auto-detect MSFS installation.\n"
                "Please ensure MSFS is installed via Microsoft Store or Steam."
            )

    def _open_community(self):
        import os
        community = self.mw.config.find_community_folder()
        if community:
            os.startfile(str(community))
        else:
            self.mw.status_bar.showMessage("Community folder not found", 5000)
