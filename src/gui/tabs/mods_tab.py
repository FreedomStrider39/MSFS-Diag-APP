from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal


class ModScanWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, mod_scanner, community_path=None):
        super().__init__()
        self.mod_scanner = mod_scanner
        self.community_path = community_path

    def run(self):
        try:
            result = self.mod_scanner.scan(self.community_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ModsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        btn_row = QHBoxLayout()

        scan_btn = QPushButton("Scan Community Folder")
        scan_btn.setProperty("class", "success")
        scan_btn.clicked.connect(self._scan_mods)
        btn_row.addWidget(scan_btn)

        open_btn = QPushButton("Open Community Folder")
        open_btn.setProperty("class", "secondary")
        open_btn.clicked.connect(self._open_community)
        btn_row.addWidget(open_btn)

        btn_row.addStretch()

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        btn_row.addWidget(self.progress)

        layout.addLayout(btn_row)

        stats_row = QHBoxLayout()

        self.stats_mods = QLabel("Mods: 0")
        self.stats_mods.setProperty("class", "card-label")
        stats_row.addWidget(self.stats_mods)

        self.stats_size = QLabel("Size: 0 GB")
        self.stats_size.setProperty("class", "card-label")
        stats_row.addWidget(self.stats_size)

        self.stats_issues = QLabel("Issues: 0")
        self.stats_issues.setProperty("class", "card-label")
        stats_row.addWidget(self.stats_issues)

        self.stats_dupes = QLabel("Duplicates: 0")
        self.stats_dupes.setProperty("class", "card-label")
        stats_row.addWidget(self.stats_dupes)

        layout.addLayout(stats_row)

        self.mod_table = QTableWidget()
        self.mod_table.setColumnCount(5)
        self.mod_table.setHorizontalHeaderLabels(["Mod Name", "Size", "WASM", "CFG", "Issues"])
        self.mod_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.mod_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.mod_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.mod_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.mod_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.mod_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.mod_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.mod_table.verticalHeader().setVisible(False)
        self.mod_table.currentCellChanged.connect(self._on_mod_selected)
        layout.addWidget(self.mod_table)

        detail_group = QGroupBox("Mod Details")
        detail_layout = QVBoxLayout()

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        detail_layout.addWidget(self.detail_text)

        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)

        self._mods = []

    def _scan_mods(self):
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.mw.status_bar.showMessage("Scanning Community folder...")

        community = self.mw.config.find_community_folder()
        self.worker = ModScanWorker(self.mw.mod_scanner, community)
        self.worker.finished.connect(self._on_scan_done)
        self.worker.error.connect(self._on_scan_error)
        self.worker.start()

    def _on_scan_done(self, result):
        self.progress.setVisible(False)

        self.stats_mods.setText(f"Mods: {result.total_mods}")
        self.stats_size.setText(f"Size: {result.total_size_gb:.1f} GB")

        issue_count = sum(1 for m in result.mods if m.issues)
        self.stats_issues.setText(f"Issues: {issue_count}")
        self.stats_dupes.setText(f"Duplicates: {len(result.duplicate_names)}")

        self._mods = result.mods
        self.mod_table.setRowCount(len(result.mods))

        for i, mod in enumerate(result.mods):
            self.mod_table.setItem(i, 0, QTableWidgetItem(mod.name))
            self.mod_table.setItem(i, 1, QTableWidgetItem(f"{mod.size_mb:.1f} MB"))
            wasm_item = QTableWidgetItem("Yes" if mod.has_wasm else "No")
            if mod.has_wasm:
                wasm_item.setForeground(Qt.green)
            else:
                wasm_item.setForeground(Qt.gray)
            self.mod_table.setItem(i, 2, wasm_item)

            cfg_item = QTableWidgetItem("Yes" if mod.has_cfg else "No")
            if mod.has_cfg:
                cfg_item.setForeground(Qt.green)
            else:
                cfg_item.setForeground(Qt.gray)
            self.mod_table.setItem(i, 3, cfg_item)

            issue_text = "; ".join(mod.issues) if mod.issues else "None"
            issue_item = QTableWidgetItem(issue_text)
            if mod.issues:
                issue_item.setForeground(Qt.red)
            self.mod_table.setItem(i, 4, issue_item)

        self.mw.status_bar.showMessage(f"Scanned {result.total_mods} mods", 5000)

    def _on_scan_error(self, error):
        self.progress.setVisible(False)
        self.mw.status_bar.showMessage(f"Scan error: {error}", 5000)

    def _on_mod_selected(self, row, col, prev_row, prev_col):
        if row < 0 or row >= len(self._mods):
            return
        mod = self._mods[row]
        text = (
            f"Mod: {mod.name}\n"
            f"Path: {mod.path}\n"
            f"Size: {mod.size_mb:.1f} MB\n"
            f"Subfolders: {mod.subfolder_count}\n"
            f"Has WASM: {mod.has_wasm}\n"
            f"Has Config: {mod.has_cfg}\n"
            f"Has Textures: {mod.has_texture}\n"
            f"Has Models: {mod.has_model}\n"
        )
        if mod.issues:
            text += f"\nIssues:\n" + "\n".join(f"  - {issue}" for issue in mod.issues)
        self.detail_text.setText(text)

    def _open_community(self):
        import os
        community = self.mw.config.find_community_folder()
        if community:
            os.startfile(str(community))
        else:
            self.mw.status_bar.showMessage("Community folder not found", 5000)
