from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QFrame
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


class ConfigTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
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

        rec_group = QGroupBox("Auto-Tuner Recommendations")
        rec_layout = QVBoxLayout()

        tier_row = QHBoxLayout()
        tier_row.addWidget(QLabel("Performance Tier:"))

        self.tier_combo = QComboBox()
        self.tier_combo.addItems(["Auto-Detect", "Low", "Medium", "High", "Ultra"])
        tier_row.addWidget(self.tier_combo)

        self.tier_info = QLabel("")
        tier_row.addWidget(self.tier_info)
        tier_row.addStretch()

        rec_layout.addLayout(tier_row)

        self.rec_table = QTableWidget()
        self.rec_table.setColumnCount(3)
        self.rec_table.setHorizontalHeaderLabels(["Setting", "Current", "Recommended"])
        self.rec_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rec_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rec_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rec_table.verticalHeader().setVisible(False)
        rec_layout.addWidget(self.rec_table)

        btn_row = QHBoxLayout()

        apply_btn = QPushButton("Apply Recommended Settings")
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

        rec_layout.addLayout(btn_row)

        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)

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
