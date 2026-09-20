from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QListWidget, QListWidgetItem,
    QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal


class CrashScanWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, crash_reader):
        super().__init__()
        self.crash_reader = crash_reader

    def run(self):
        try:
            context = self.crash_reader.build_diagnostic_context()
            self.finished.emit(context)
        except Exception as e:
            self.error.emit(str(e))


class AIWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, ai_service, context):
        super().__init__()
        self.ai_service = ai_service
        self.context = context

    def run(self):
        try:
            result = self.ai_service.diagnose(self.context)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class CrashTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        btn_row = QHBoxLayout()

        scan_btn = QPushButton("Scan Event Viewer for MSFS Crashes")
        scan_btn.setProperty("class", "success")
        scan_btn.clicked.connect(self._scan_crashes)
        btn_row.addWidget(scan_btn)

        self.diagnose_btn = QPushButton("Diagnose with AI")
        self.diagnose_btn.setProperty("class", "warning")
        self.diagnose_btn.clicked.connect(self._run_diagnosis)
        btn_row.addWidget(self.diagnose_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        splitter = QSplitter(Qt.Vertical)

        event_group = QGroupBox("Crash Events Found")
        event_layout = QVBoxLayout()
        self.crash_list = QListWidget()
        self.crash_list.currentRowChanged.connect(self._on_crash_selected)
        event_layout.addWidget(self.crash_list)
        event_group.setLayout(event_layout)
        splitter.addWidget(event_group)

        detail_group = QGroupBox("Crash Details")
        detail_layout = QVBoxLayout()
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)

        layout.addWidget(splitter)

        ai_group = QGroupBox("AI Diagnosis")
        ai_layout = QVBoxLayout()
        self.ai_result = QTextEdit()
        self.ai_result.setReadOnly(True)
        self.ai_result.setPlaceholderText(
            "Click 'Diagnose with AI' after scanning crashes.\n\n"
            "Uses built-in rule engine by default (works offline).\n"
            "Optional: Add a free Groq API key in Settings for better AI analysis."
        )
        ai_layout.addWidget(self.ai_result)
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        self._crash_data = []
        self._diagnostic_context = ""

    def _scan_crashes(self):
        self.crash_list.clear()
        self.detail_text.clear()
        self.ai_result.clear()
        self.mw.status_bar.showMessage("Scanning Event Viewer...")
        self.worker = CrashScanWorker(self.mw.crash_reader)
        self.worker.finished.connect(self._on_scan_done)
        self.worker.error.connect(self._on_scan_error)
        self.worker.start()

    def _on_scan_done(self, context):
        self._diagnostic_context = context
        crashes = self.mw.crash_reader.get_recent_crashes(20)
        self._crash_data = crashes

        if not crashes:
            self.crash_list.addItem("No MSFS-related crashes found in Event Viewer.")
            self.detail_text.setText(
                "No crash events were found for Microsoft Flight Simulator.\n\n"
                "This could mean:\n"
                "1. No recent crashes have occurred\n"
                "2. The crash source name doesn't match known MSFS identifiers\n"
                "3. Event log permissions may be restricted"
            )
            self.mw.status_bar.showMessage("No crashes found", 5000)
            return

        for crash in crashes:
            item = QListWidgetItem(f"[{crash.timestamp}] {crash.source} (ID: {crash.event_id})")
            self.crash_list.addItem(item)

        self.mw.status_bar.showMessage(f"Found {len(crashes)} MSFS crash events", 5000)

    def _on_scan_error(self, error):
        self.mw.status_bar.showMessage(f"Scan error: {error}", 5000)
        QMessageBox.warning(self, "Scan Error", f"Failed to scan Event Viewer:\n{error}")

    def _on_crash_selected(self, index):
        if index < 0 or index >= len(self._crash_data):
            return
        crash = self._crash_data[index]
        details = self.mw.crash_reader.get_crash_details(crash)

        text = (
            f"=== Crash Event Details ===\n\n"
            f"Timestamp: {crash.timestamp}\n"
            f"Source: {crash.source}\n"
            f"Event ID: {crash.event_id}\n"
            f"Level: {crash.level}\n\n"
        )

        if details["faulting_module"]:
            text += f"Faulting Module: {details['faulting_module']}\n"
        if details["exception_code"]:
            text += f"Exception Code: {details['exception_code']}\n"
        if details["app_name"]:
            text += f"Application: {details['app_name']}\n"
        if details["fault_offset"]:
            text += f"Fault Offset: {details['fault_offset']}\n"

        text += f"\n--- Raw Message ---\n{crash.message}"
        self.detail_text.setText(text)

    def _run_diagnosis(self):
        if not self._diagnostic_context:
            QMessageBox.information(
                self, "No Data",
                "Please scan for crashes first using the 'Scan Event Viewer' button."
            )
            return

        self.diagnose_btn.setEnabled(False)
        self.diagnose_btn.setText("Analyzing...")
        engine = "Groq AI" if self.mw.ai_service.has_groq() else "Built-in Engine"
        self.mw.status_bar.showMessage(f"Running {engine}...")

        self.ai_worker = AIWorker(self.mw.ai_service, self._diagnostic_context)
        self.ai_worker.finished.connect(self._on_ai_done)
        self.ai_worker.error.connect(self._on_ai_error)
        self.ai_worker.start()

    def _on_ai_done(self, result):
        self.ai_result.setText(result)
        self.diagnose_btn.setEnabled(True)
        self.diagnose_btn.setText("Diagnose with AI")
        self.mw.status_bar.showMessage("Diagnosis complete", 5000)

    def _on_ai_error(self, error):
        self.ai_result.setText(f"Diagnosis Error:\n\n{error}")
        self.diagnose_btn.setEnabled(True)
        self.diagnose_btn.setText("Diagnose with AI")
        self.mw.status_bar.showMessage("Diagnosis failed", 5000)
