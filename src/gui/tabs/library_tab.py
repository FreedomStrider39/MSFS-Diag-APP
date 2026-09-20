from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QSplitter, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt


class LibraryTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.mw = main_window
        self._all_errors = []
        self._setup_ui()
        self._load_errors()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        search_group = QGroupBox("Search Error Database")
        search_layout = QVBoxLayout()

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search by error name, DLL, error code, symptom, or keyword... "
            "(e.g. 'nvlddmkm', '0xc0000005', 'crash on takeoff', 'clouds')"
        )
        self.search_input.returnPressed.connect(self._perform_search)
        search_row.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.setProperty("class", "success")
        search_btn.clicked.connect(self._perform_search)
        search_row.addWidget(search_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self._clear_search)
        search_row.addWidget(clear_btn)

        search_layout.addLayout(search_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Category:"))

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.currentTextChanged.connect(self._filter_changed)
        filter_row.addWidget(self.category_combo)

        filter_row.addWidget(QLabel("Severity:"))
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All", "Critical", "High", "Medium", "Low", "Info"])
        self.severity_combo.currentTextChanged.connect(self._filter_changed)
        filter_row.addWidget(self.severity_combo)

        self.result_count = QLabel("0 errors")
        self.result_count.setProperty("class", "subtitle")
        filter_row.addWidget(self.result_count)
        filter_row.addStretch()

        search_layout.addLayout(filter_row)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        splitter = QSplitter(Qt.Horizontal)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["ID", "Name", "Category", "Severity"])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.currentItemChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.results_table)

        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)

        self.detail_title = QLabel("Select an error to view details")
        self.detail_title.setProperty("class", "title")
        self.detail_title.setWordWrap(True)
        detail_layout.addWidget(self.detail_title)

        self.detail_content = QTextEdit()
        self.detail_content.setReadOnly(True)
        self.detail_content.setStyleSheet("font-size: 13px;")
        detail_layout.addWidget(self.detail_content)

        self.search_online_btn = QPushButton("Search Online for This Error")
        self.search_online_btn.setProperty("class", "secondary")
        self.search_online_btn.clicked.connect(self._search_online)
        self.search_online_btn.setEnabled(False)
        detail_layout.addWidget(self.search_online_btn)

        splitter.addWidget(detail_widget)
        splitter.setSizes([400, 500])

        layout.addWidget(splitter)

    def _load_errors(self):
        from ...services.error_library import get_all_errors, get_all_categories
        self._all_errors = get_all_errors()
        categories = get_all_categories()
        self.category_combo.addItems(categories)
        self._populate_table(self._all_errors)

    def _populate_table(self, errors):
        self.results_table.setRowCount(len(errors))
        for i, error in enumerate(errors):
            id_item = QTableWidgetItem(error.id)
            id_item.setData(Qt.UserRole, error.id)
            self.results_table.setItem(i, 0, id_item)

            name_item = QTableWidgetItem(error.name)
            self.results_table.setItem(i, 1, name_item)

            cat_item = QTableWidgetItem(error.category)
            self.results_table.setItem(i, 2, cat_item)

            sev_item = QTableWidgetItem(error.severity.upper())
            sev_colors = {
                "critical": "#e74c3c",
                "high": "#e67e22",
                "medium": "#f1c40f",
                "low": "#3498db",
                "info": "#95a5a6",
            }
            color = sev_colors.get(error.severity.lower(), "#ffffff")
            sev_item.setForeground(self._hex_to_color(color))
            self.results_table.setItem(i, 3, sev_item)

        self.result_count.setText(f"{len(errors)} errors")

    def _hex_to_color(self, hex_color):
        from PySide6.QtGui import QColor
        return QColor(hex_color)

    def _perform_search(self):
        from ...services.error_library import search_errors
        query = self.search_input.text().strip()
        if not query:
            self._apply_filters()
            return

        results = search_errors(query)

        category = self.category_combo.currentText()
        if category != "All Categories":
            results = [e for e in results if e.category == category]

        severity = self.severity_combo.currentText()
        if severity != "All":
            results = [e for e in results if e.severity.lower() == severity.lower()]

        self._populate_table(results)

    def _clear_search(self):
        self.search_input.clear()
        self.category_combo.setCurrentText("All Categories")
        self.severity_combo.setCurrentText("All")
        self._populate_table(self._all_errors)

    def _filter_changed(self):
        self._perform_search()

    def _apply_filters(self):
        errors = self._all_errors

        category = self.category_combo.currentText()
        if category != "All Categories":
            errors = [e for e in errors if e.category == category]

        severity = self.severity_combo.currentText()
        if severity != "All":
            errors = [e for e in errors if e.severity.lower() == severity.lower()]

        self._populate_table(errors)

    def _on_selection_changed(self, current, previous):
        from ...services.error_library import get_error_by_id
        if current is None:
            return
        row = current.row()
        id_item = self.results_table.item(row, 0)
        if not id_item:
            return
        error_id = id_item.data(Qt.UserRole)
        error = get_error_by_id(error_id)
        if error:
            self._show_error_detail(error)

    def _show_error_detail(self, error):
        self.detail_title.setText(f"{error.id}: {error.name}")

        parts = []
        parts.append(f"Category: {error.category}")
        parts.append(f"Severity: {error.severity.upper()}")
        if error.applies_to != "both":
            parts.append(f"Applies to: {error.applies_to}")
        parts.append("")
        parts.append("Description:")
        parts.append(error.description)
        parts.append("")

        if error.causes:
            parts.append("Causes:")
            for cause in error.causes:
                parts.append(f"  - {cause}")
            parts.append("")

        if error.fixes:
            parts.append("Fixes:")
            for i, fix in enumerate(error.fixes, 1):
                parts.append(f"  {i}. {fix}")
            parts.append("")

        if error.related_dlls:
            parts.append(f"Related DLLs: {', '.join(error.related_dlls)}")
        if error.related_codes:
            parts.append(f"Related Codes: {', '.join(error.related_codes)}")
        if error.search_terms:
            parts.append(f"Search Terms: {', '.join(error.search_terms)}")

        self.detail_content.setPlainText("\n".join(parts))
        self.search_online_btn.setEnabled(True)
        self._current_error = error

    def _search_online(self):
        if not hasattr(self, '_current_error') or not self._current_error:
            return

        error = self._current_error
        query_parts = ["MSFS"]
        if error.related_dlls:
            query_parts.append(error.related_dlls[0])
        if error.related_codes:
            query_parts.append(error.related_codes[0])
        query_parts.append("fix")
        query = " ".join(query_parts)

        results = self.mw.ai_service.web_search.search(query, max_results=3)

        if results.results:
            detail = f"Online results for: {query}\n\n"
            for r in results.results:
                detail += f"{r.title}\n{r.url}\n{r.snippet}\n\n"
            self.detail_content.setPlainText(
                self.detail_content.toPlainText() + "\n\n=== ONLINE RESULTS ===\n\n" + detail
            )
        else:
            self.detail_content.setPlainText(
                self.detail_content.toPlainText() + "\n\n=== ONLINE RESULTS ===\n\nNo results found."
            )
