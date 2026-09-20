from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QTextEdit, QFormLayout, QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
import os


class SettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        ai_group = QGroupBox("AI Engine")
        ai_layout = QVBoxLayout()

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 8px;")
        ai_layout.addWidget(self.status_label)

        key_row = QHBoxLayout()
        self.groq_input = QLineEdit()
        self.groq_input.setPlaceholderText("Paste your free Groq API key here (optional)")
        self.groq_input.setEchoMode(QLineEdit.Password)
        self.groq_input.setText(self.mw.ai_service.groq_key)
        key_row.addWidget(self.groq_input)

        save_btn = QPushButton("Save Key")
        save_btn.clicked.connect(self._save_key)
        key_row.addWidget(save_btn)
        ai_layout.addLayout(key_row)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(160)
        help_text.setText(
            "AI Engine: Built-in Rule Engine (always works, no internet needed)\n\n"
            "OPTIONAL UPGRADE - Groq Cloud AI (free, better answers):\n"
            "1. Go to console.groq.com\n"
            "2. Click 'Sign Up' (free, no credit card, 30 seconds)\n"
            "3. Go to API Keys -> Create API Key\n"
            "4. Copy the key and paste it above\n\n"
            "Free tier: 14,400 tokens/min, Llama 3 70B model"
        )
        ai_layout.addWidget(help_text)

        test_btn = QPushButton("Test AI")
        test_btn.setProperty("class", "success")
        test_btn.clicked.connect(self._test_ai)
        ai_layout.addWidget(test_btn)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        path_group = QGroupBox("MSFS Paths")
        path_layout = QFormLayout()

        self.path_display = QLabel("Detecting...")
        self.path_display.setWordWrap(True)
        path_layout.addRow("MSFS Path:", self.path_display)

        self.community_display = QLabel("Detecting...")
        self.community_display.setWordWrap(True)
        path_layout.addRow("Community:", self.community_display)

        btn_row = QHBoxLayout()
        detect_btn = QPushButton("Re-detect Paths")
        detect_btn.clicked.connect(self._redetect_paths)
        btn_row.addWidget(detect_btn)

        browse_btn = QPushButton("Browse Manually")
        browse_btn.setProperty("class", "secondary")
        browse_btn.clicked.connect(self._browse_path)
        btn_row.addWidget(browse_btn)
        btn_row.addStretch()
        path_layout.addRow("", btn_row)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        donate_group = QGroupBox("Support Development")
        donate_layout = QVBoxLayout()
        donate_label = QLabel(
            "All features are free. If this tool saves you time,\n"
            "consider buying the developer a coffee!"
        )
        donate_label.setWordWrap(True)
        donate_layout.addWidget(donate_label)
        donate_row = QHBoxLayout()
        paypal_btn = QPushButton("Donate via PayPal")
        paypal_btn.setProperty("class", "warning")
        paypal_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://paypal.me/your-paypal")))
        donate_row.addWidget(paypal_btn)
        github_btn = QPushButton("Star on GitHub")
        github_btn.setProperty("class", "secondary")
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/your-repo")))
        donate_row.addWidget(github_btn)
        donate_row.addStretch()
        donate_layout.addLayout(donate_row)
        donate_group.setLayout(donate_layout)
        layout.addWidget(donate_group)

        layout.addStretch()

        self._update_status()
        self._detect_paths()

    def _update_status(self):
        if self.mw.ai_service.has_groq():
            self.status_label.setText(
                "AI: Groq Cloud (Llama 3 70B) - CONNECTED\n"
                "Real AI-powered crash analysis enabled."
            )
            self.status_label.setStyleSheet("padding: 8px; color: #27ae60; font-weight: bold;")
        else:
            self.status_label.setText(
                "AI: Built-in Rule Engine (active)\n"
                "Works offline, no setup needed.\n"
                "Optional: Add a free Groq API key above for better AI analysis."
            )
            self.status_label.setStyleSheet("padding: 8px; color: #3498db;")

    def _save_key(self):
        key = self.groq_input.text().strip()
        self.mw.ai_service.set_groq_key(key)
        self._update_status()
        if key:
            self.mw.status_bar.showMessage("Groq API key saved", 5000)
        else:
            self.mw.status_bar.showMessage("Using built-in AI engine", 5000)

    def _test_ai(self):
        self.mw.status_bar.showMessage("Testing AI...")
        result = self.mw.ai_service.diagnose(
            "Crash: nvlddmkm.dll at 0xc0000005. MSFS 2020. NVIDIA RTX 3060. What went wrong?"
        )
        preview = result[:400]
        if self.mw.ai_service.has_groq():
            QMessageBox.information(self, "Groq AI Test", f"Cloud AI responding:\n\n{preview}")
        else:
            QMessageBox.information(self, "Built-in AI Test", f"Rule engine responding:\n\n{preview}")
        self.mw.status_bar.showMessage("AI test complete", 5000)

    def _detect_paths(self):
        msfs = self.mw.config.find_msfs_path()
        community = self.mw.config.find_community_folder()
        self.path_display.setText(str(msfs) if msfs else "Not found")
        self.community_display.setText(str(community) if community else "Not found")

    def _redetect_paths(self):
        self.mw.config._msfs_path = None
        self.mw.config._config_path = None
        msfs = self.mw.config.find_msfs_path(clear_cache=True)
        community = self.mw.config.find_community_folder()
        self.path_display.setText(str(msfs) if msfs else "Not found")
        self.community_display.setText(str(community) if community else "Not found")
        if msfs:
            self.mw.status_bar.showMessage(f"MSFS found at {msfs}", 5000)
        else:
            self.mw.status_bar.showMessage("MSFS not found. Try browsing manually.", 5000)

    def _browse_path(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select MSFS Installation Folder",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        if folder:
            from pathlib import Path
            p = Path(folder)
            success = self.mw.config.set_custom_path(p)
            if success:
                self.path_display.setText(str(p))
                community = self.mw.config.find_community_folder()
                self.community_display.setText(str(community) if community else "Not found")
                self.mw.status_bar.showMessage(f"Path set to {p}", 5000)
            else:
                QMessageBox.warning(
                    self, "Invalid Folder",
                    f"Could not find UserCfg.opt in:\n{folder}\n\n"
                    "Please select the folder that contains your MSFS config files."
                )
