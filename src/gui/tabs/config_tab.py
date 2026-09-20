from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal


class TuneWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, tuner, tier):
        super().__init__()
        self.tuner = tuner
        self.tier = tier

    def run(self):
        try:
            backup = self.tuner.parser.create_backup()
            if not backup:
                self.finished.emit(False, "Failed to create backup. Check MSFS installation path.")
                return
            changes = self.tuner.get_msfs_changes(self.tier)
            success = self.tuner.apply_msfs_changes(changes)
            if success:
                self.finished.emit(True, f"Settings applied! Backup saved to:\n{backup}")
            else:
                self.finished.emit(False, "Failed to write config. Check file permissions.")
        except Exception as e:
            self.finished.emit(False, str(e))


class AIAnalysisWorker(QThread):
    finished = Signal(object)

    def __init__(self, ai_service, system_info, current_settings, crash_events, mods):
        super().__init__()
        self.ai_service = ai_service
        self.system_info = system_info
        self.current_settings = current_settings
        self.crash_events = crash_events
        self.mods = mods

    def run(self):
        try:
            report = self.ai_service.recommend_tuning(
                self.system_info, self.current_settings,
                self.crash_events, self.mods
            )
            self.finished.emit(report)
        except Exception as e:
            self.finished.emit(None)


class ConfigTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._current_report = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_group = QGroupBox("Current Settings")
        info_layout = QVBoxLayout()

        self.current_settings = QLabel("Click 'Scan Settings' to load current config.")
        self.current_settings.setWordWrap(True)
        self.current_settings.setStyleSheet("font-family: 'Cascadia Code', monospace; padding: 8px;")
        info_layout.addWidget(self.current_settings)

        scan_btn = QPushButton("Scan Settings")
        scan_btn.clicked.connect(self._scan_settings)
        info_layout.addWidget(scan_btn)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        ai_group = QGroupBox("AI-Powered Tuning")
        ai_layout = QVBoxLayout()

        ai_desc = QLabel(
            "Analyze your hardware, current settings, and crash history to get\n"
            "personalized optimization recommendations."
        )
        ai_desc.setProperty("class", "subtitle")
        ai_desc.setWordWrap(True)
        ai_layout.addWidget(ai_desc)

        ai_btn_row = QHBoxLayout()

        self.ai_analyze_btn = QPushButton("Run AI Analysis")
        self.ai_analyze_btn.setProperty("class", "success")
        self.ai_analyze_btn.clicked.connect(self._run_ai_analysis)
        ai_btn_row.addWidget(self.ai_analyze_btn)

        self.ai_status = QLabel("")
        self.ai_status.setProperty("class", "subtitle")
        ai_btn_row.addWidget(self.ai_status)
        ai_btn_row.addStretch()

        ai_layout.addLayout(ai_btn_row)

        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setPlaceholderText("Click 'Run AI Analysis' to get personalized recommendations...")
        self.ai_output.setStyleSheet("font-family: 'Cascadia Code', monospace; min-height: 180px;")
        ai_layout.addWidget(self.ai_output)

        ai_btn_row2 = QHBoxLayout()

        self.apply_ai_btn = QPushButton("Apply AI Recommendations")
        self.apply_ai_btn.setProperty("class", "success")
        self.apply_ai_btn.setEnabled(False)
        self.apply_ai_btn.clicked.connect(self._apply_ai_recommendations)
        ai_btn_row2.addWidget(self.apply_ai_btn)

        self.apply_ai_btn.setShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_A)

        ai_btn_row2.addStretch()
        ai_layout.addLayout(ai_btn_row2)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        preset_group = QGroupBox("Quick Presets")
        preset_layout = QVBoxLayout()

        tier_row = QHBoxLayout()
        tier_row.addWidget(QLabel("Performance Tier:"))

        self.tier_combo = QComboBox()
        self.tier_combo.addItems(["Auto-Detect", "Low", "Medium", "High", "Ultra"])
        tier_row.addWidget(self.tier_combo)

        self.tier_info = QLabel("")
        tier_row.addWidget(self.tier_info)
        tier_row.addStretch()

        preset_layout.addLayout(tier_row)

        self.rec_table = QTableWidget()
        self.rec_table.setColumnCount(3)
        self.rec_table.setHorizontalHeaderLabels(["Setting", "Current", "Recommended"])
        self.rec_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rec_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rec_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rec_table.verticalHeader().setVisible(False)
        preset_layout.addWidget(self.rec_table)

        btn_row = QHBoxLayout()

        apply_btn = QPushButton("Apply Preset Settings")
        apply_btn.setProperty("class", "success")
        apply_btn.clicked.connect(self._apply_settings)
        btn_row.addWidget(apply_btn)

        backup_btn = QPushButton("Create Backup Only")
        backup_btn.setProperty("class", "secondary")
        backup_btn.clicked.connect(self._create_backup)
        btn_row.addWidget(backup_btn)

        restore_btn = QPushButton("Restore Backup")
        restore_btn.setProperty("class", "warning")
        restore_btn.clicked.connect(self._restore_backup)
        btn_row.addWidget(restore_btn)

        preset_layout.addLayout(btn_row)

        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        self._scan_settings()

    def _scan_settings(self):
        path = self.mw.config.find_usercfg()
        if not path or not path.exists():
            self.current_settings.setText("UserCfg.opt not found. Detect MSFS from the Dashboard tab first.")
            return

        settings = self.mw.config.parse()
        self.current_settings.setText(
            f"File: {path}\n\n"
            f"Render Scale: {settings.render_scale} | "
            f"Terrain LOD: {settings.terrain_lod} | "
            f"Object LOD: {settings.object_lod}\n"
            f"Clouds: {settings.volumetric_clouds} | "
            f"Texture: {settings.texture_res} | "
            f"Aniso: {settings.anisotropic}x\n"
            f"Shadows: {settings.shadows} | "
            f"Reflection: {settings.reflection} | "
            f"Grass: {settings.grass}\n"
            f"AO: {settings.ambient_occlusion} | "
            f"Motion Blur: {settings.motion_blur} | "
            f"DoF: {settings.depth_of_field} | "
            f"Bloom: {settings.bloom}"
        )

        tier = self.mw.tuner.determine_tier()
        self.tier_info.setText(f"Detected tier: {tier.upper()}")

        self._load_recommendations(tier)

    def _load_recommendations(self, tier):
        recs = self.mw.tuner.get_recommendations(tier)
        self.rec_table.setRowCount(len(recs))
        for i, rec in enumerate(recs):
            self.rec_table.setItem(i, 0, QTableWidgetItem(rec.setting))
            self.rec_table.setItem(i, 1, QTableWidgetItem(rec.current))
            item = QTableWidgetItem(rec.recommended)
            item.setForeground(Qt.green)
            self.rec_table.setItem(i, 2, item)

    def _get_selected_tier(self) -> str:
        text = self.tier_combo.currentText()
        mapping = {"Auto-Detect": None, "Low": "low", "Medium": "medium", "High": "high", "Ultra": "ultra"}
        tier = mapping.get(text)
        if tier is None:
            tier = self.mw.tuner.determine_tier()
        return tier

    def _run_ai_analysis(self):
        self.ai_analyze_btn.setEnabled(False)
        self.ai_analyze_btn.setText("Analyzing...")
        self.ai_status.setText("AI is analyzing your system...")
        self.ai_output.setPlainText("Analyzing hardware, settings, and crash history...")

        system_info = self.mw.hardware.get_all()
        current_settings = self.mw.config.parse()

        crash_events = []
        try:
            crash_events = self.mw.crash_reader.get_recent_crashes(10)
        except Exception:
            pass

        mods = []
        try:
            community = self.mw.config.find_community_folder()
            if community:
                scan_result = self.mw.mod_scanner.scan(community)
                mods = [m.name for m in scan_result.mods[:15]]
        except Exception:
            pass

        self._ai_worker = AIAnalysisWorker(
            self.mw.ai_service, system_info, current_settings,
            crash_events, mods
        )
        self._ai_worker.finished.connect(self._on_ai_analysis_done)
        self._ai_worker.start()

    def _on_ai_analysis_done(self, report):
        self.ai_analyze_btn.setEnabled(True)
        self.ai_analyze_btn.setText("Run AI Analysis")

        if report is None:
            self.ai_status.setText("AI analysis failed")
            self.ai_output.setPlainText("Error: AI analysis failed. Check your Groq API key or try again.")
            return

        self._current_report = report

        source_label = f"[{report.source}]"
        self.ai_status.setText(f"Analysis complete {source_label}")

        self.ai_output.setPlainText(report.to_text())

        if report.recommendations:
            self.apply_ai_btn.setEnabled(True)
            high_count = len([r for r in report.recommendations if r.impact == "high"])
            self.apply_ai_btn.setText(f"Apply {len(report.recommendations)} Recommendations ({high_count} high impact)")
        else:
            self.apply_ai_btn.setEnabled(False)
            self.apply_ai_btn.setText("No Changes Needed")

    def _apply_ai_recommendations(self):
        if not self._current_report or not self._current_report.recommendations:
            return

        report = self._current_report
        rec_text = "\n".join([
            f"{r.setting}: {r.current_value} -> {r.recommended_value}"
            for r in report.recommendations[:10]
        ])

        reply = QMessageBox.question(
            self, "Apply AI Recommendations",
            f"Apply {len(report.recommendations)} AI-recommended settings?\n\n"
            f"{rec_text}\n\n"
            "A timestamped backup will be created automatically.\n"
            f"Engine: {report.source}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        tier = self._current_report.overall_tier or self._get_selected_tier()
        self.worker = TuneWorker(self.mw.tuner, tier)
        self.worker.finished.connect(self._on_tune_done)
        self.worker.start()
        self.mw.status_bar.showMessage("Applying AI recommendations...")

    def _apply_settings(self):
        tier = self._get_selected_tier()
        reply = QMessageBox.question(
            self, "Apply Settings",
            f"Apply {tier.upper()} preset to UserCfg.opt?\n\n"
            "A timestamped backup will be created automatically.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.worker = TuneWorker(self.mw.tuner, tier)
        self.worker.finished.connect(self._on_tune_done)
        self.worker.start()
        self.mw.status_bar.showMessage("Applying settings...")

    def _on_tune_done(self, success, message):
        if success:
            QMessageBox.information(self, "Success", message)
            self.mw.status_bar.showMessage("Settings applied successfully", 5000)
            self._scan_settings()
        else:
            QMessageBox.warning(self, "Error", message)
            self.mw.status_bar.showMessage("Failed to apply settings", 5000)

    def _create_backup(self):
        backup = self.mw.config.create_backup()
        if backup:
            QMessageBox.information(self, "Backup Created", f"Backup saved to:\n{backup}")
            self.mw.status_bar.showMessage(f"Backup: {backup}", 5000)
        else:
            QMessageBox.warning(self, "Error", "Failed to create backup. Check MSFS installation path.")

    def _restore_backup(self):
        backups = self.mw.config.list_backups()
        if not backups:
            QMessageBox.information(self, "No Backups", "No backups found to restore.")
            return

        from PySide6.QtWidgets import QInputDialog
        names = [b.name for b in backups]
        name, ok = QInputDialog.getItem(self, "Restore Backup", "Select a backup to restore:", names, 0, False)
        if ok and name:
            backup_path = next((b for b in backups if b.name == name), None)
            if backup_path:
                reply = QMessageBox.question(
                    self, "Confirm Restore",
                    f"Restore backup '{name}'?\n\nThis will overwrite your current UserCfg.opt.",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    success = self.mw.config.restore_backup(backup_path)
                    if success:
                        QMessageBox.information(self, "Restored", "Backup restored successfully!")
                        self._scan_settings()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to restore backup.")
