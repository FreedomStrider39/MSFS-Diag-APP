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

        groq_row = QHBoxLayout()
        groq_row.addWidget(QLabel("Groq Key:"))
        self.groq_input = QLineEdit()
        self.groq_input.setPlaceholderText("Free Groq API key (optional - console.groq.com)")
        self.groq_input.setEchoMode(QLineEdit.Password)
        self.groq_input.setText(self.mw.ai_service.groq_key)
        groq_row.addWidget(self.groq_input)

        save_groq_btn = QPushButton("Save")
        save_groq_btn.clicked.connect(self._save_groq_key)
        groq_row.addWidget(save_groq_btn)
        ai_layout.addLayout(groq_row)

        gemini_row = QHBoxLayout()
        gemini_row.addWidget(QLabel("Gemini Key:"))
        self.gemini_input = QLineEdit()
        self.gemini_input.setPlaceholderText("Free Gemini API key (optional - aistudio.google.com)")
        self.gemini_input.setEchoMode(QLineEdit.Password)
        self.gemini_input.setText(self.mw.ai_service.gemini_key)
        gemini_row.addWidget(self.gemini_input)

        save_gemini_btn = QPushButton("Save")
        save_gemini_btn.clicked.connect(self._save_gemini_key)
        gemini_row.addWidget(save_gemini_btn)
        ai_layout.addLayout(gemini_row)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(200)
        help_text.setText(
            "AI Engine Priority: Groq > Gemini > Built-in Rules\n\n"
            "Built-in Rule Engine: Always works, no internet needed.\n"
            "302+ known MSFS errors with specific fixes.\n\n"
            "OPTIONAL - Groq Cloud AI (free, best quality):\n"
            "1. Go to console.groq.com\n"
            "2. Sign Up (free, no credit card, 30 seconds)\n"
            "3. API Keys -> Create API Key -> Copy\n"
            "4. Paste above and click Save\n"
            "Model: Llama 3 70B | Free tier: 14,400 tokens/min\n\n"
            "OPTIONAL - Gemini AI (free, fast):\n"
            "1. Go to aistudio.google.com\n"
            "2. Get API key (free, no credit card)\n"
            "3. Paste above and click Save\n"
            "Model: Gemini 2.5 Flash | Free tier: 5 RPM, 20 RPD"
        )
        ai_layout.addWidget(help_text)

        test_row = QHBoxLayout()
        test_btn = QPushButton("Test AI")
        test_btn.setProperty("class", "success")
        test_btn.clicked.connect(self._test_ai)
        test_row.addWidget(test_btn)
        test_row.addStretch()
        ai_layout.addLayout(test_row)

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
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/FreedomStrider39/MSFS-Diag-APP")))
        donate_row.addWidget(github_btn)
        donate_row.addStretch()
        donate_layout.addLayout(donate_row)
        donate_group.setLayout(donate_layout)
        layout.addWidget(donate_group)

        layout.addStretch()

        self._update_status()
        self._detect_paths()

    def _update_status(self):
        if self.mw.ai_service.has_groq() and self.mw.ai_service.has_gemini():
            self.status_label.setText(
                "AI: Groq + Gemini - BOTH CONNECTED\n"
                "Groq used first, Gemini as fallback."
            )
            self.status_label.setStyleSheet("padding: 8px; color: #27ae60; font-weight: bold;")
        elif self.mw.ai_service.has_groq():
            self.status_label.setText(
                "AI: Groq Cloud (Llama 3 70B) - CONNECTED\n"
                "Real AI-powered crash analysis enabled."
            )
            self.status_label.setStyleSheet("padding: 8px; color: #27ae60; font-weight: bold;")
        elif self.mw.ai_service.has_gemini():
            self.status_label.setText(
                "AI: Gemini (2.5 Flash) - CONNECTED\n"
                "Real AI-powered crash analysis enabled."
            )
            self.status_label.setStyleSheet("padding: 8px; color: #27ae60; font-weight: bold;")
        else:
            self.status_label.setText(
                "AI: Built-in Rule Engine (active)\n"
                "Works offline, no setup needed.\n"
                "Optional: Add a free Groq or Gemini API key above for better AI."
            )
            self.status_label.setStyleSheet("padding: 8px; color: #3498db;")

    def _save_groq_key(self):
        key = self.groq_input.text().strip()
        self.mw.ai_service.set_groq_key(key)
        self._update_status()
        if key:
            self.mw.status_bar.showMessage("Groq API key saved", 5000)
        else:
            self.mw.status_bar.showMessage("Groq key cleared", 5000)

    def _save_gemini_key(self):
        key = self.gemini_input.text().strip()
        self.mw.ai_service.set_gemini_key(key)
        self._update_status()
        if key:
            self.mw.status_bar.showMessage("Gemini API key saved", 5000)
        else:
            self.mw.status_bar.showMessage("Gemini key cleared", 5000)

    def _test_ai(self):
        self.mw.status_bar.showMessage("Testing AI...")
        result = self.mw.ai_service.diagnose(
            "Crash: nvlddmkm.dll at 0xc0000005. MSFS 2020. NVIDIA RTX 3060. What went wrong?"
        )
        preview = result[:500]
        provider = self.mw.ai_service._get_active_provider()
        QMessageBox.information(self, f"{provider} AI Test", f"AI responding via {provider}:\n\n{preview}")
        self.mw.status_bar.showMessage(f"AI test complete ({provider})", 5000)

    def _detect_paths(self):
        msfs = self.mw.config.find_msfs_path()
        community = self.mw.config.find_community_folder()
        self.path_display.setText(str(msfs) if msfs else "Not found")
        self.community_display.setText(str(community) if community else "Not found")

    def _redetect_paths(self):
        self.mw.config.find_msfs_path(clear_cache=True)
        msfs = self.mw.config.find_msfs_path()
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
