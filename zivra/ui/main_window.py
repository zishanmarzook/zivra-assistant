from datetime import datetime
from html import escape
from pathlib import Path

from PySide6.QtCore import QThreadPool, QTimer, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow, QMenu, QMessageBox,
    QPushButton, QStackedWidget, QSystemTrayIcon, QTableWidget, QTableWidgetItem,
    QTextBrowser, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView)

from zivra import __version__
from zivra.core.assistant import Assistant
from zivra.system.performance import Performance
from zivra.system.windows import IS_WINDOWS, Startup
from zivra.ui.theme import STYLE
from zivra.ui.workers import Job

PAGES = ("Dashboard", "AI Chat", "Voice Assistant", "Applications", "Automation",
         "Integrations", "System Monitor", "File Manager", "Plugins", "Settings")


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.assistant = Assistant(settings)
        self.performance = Performance()
        self.startup = Startup()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(3)
        self.jobs = set()
        self.foreground_busy = False
        self.monitor_busy = False
        self.quitting = False
        self.tray = None
        self.history_epoch = 0
        self.setWindowTitle(f"ZIVRA • Personal system {__version__}")
        self.resize(1180, 820)
        self.setMinimumSize(880, 650)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(QIcon(str(Path(__file__).parents[1] / "resources/zivra.svg")))
        shell = QWidget(objectName="shell")
        self.setCentralWidget(shell)
        layout = QHBoxLayout(shell)
        layout.setContentsMargins(16, 16, 16, 16)
        self.navigation = QListWidget()
        self.navigation.addItems(PAGES)
        layout.addWidget(self.navigation)
        self.pages = QStackedWidget()
        layout.addWidget(self.pages, 1)
        self.layouts = {}
        for name in PAGES:
            page = QWidget()
            column = QVBoxLayout(page)
            column.setContentsMargins(28, 20, 28, 20)
            column.setSpacing(16)
            title = QLabel("Z / I / V / R / A" if name == "Dashboard" else name, objectName="title")
            column.addWidget(title)
            self.layouts[name] = column
            self.pages.addWidget(page)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.build_dashboard()
        self.build_chat()
        self.build_voice()
        self.build_applications()
        self.build_automation()
        self.build_integrations()
        self.build_monitor()
        self.build_files()
        self.build_plugins()
        self.build_settings()
        self.install_tray()
        self.statusBar().showMessage("LOCAL COMMAND ENGINE • No cloud model • Microphone off")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(2000)
        self.tick()
        for command, response in self.settings.history():
            self.add_message("YOU", command)
            self.add_message("ZIVRA", response)

    @staticmethod
    def text(column, message):
        label = QLabel(message, objectName="subtitle")
        label.setWordWrap(True)
        column.addWidget(label)
        return label

    @staticmethod
    def button(column, text, callback, primary=False):
        button = QPushButton(text)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(callback)
        column.addWidget(button)
        return button

    def build_dashboard(self):
        column = self.layouts["Dashboard"]
        self.clock = self.text(column, "")
        self.text(column, "PERSONAL SYSTEM / LOCAL FIRST\nYour command console, rebuilt from ZIVRA V2.")
        grid = QGridLayout()
        self.metric_labels = {}
        for index, name in enumerate(("CPU", "Memory", "Network", "Battery")):
            label = QLabel(f"{name}\nSampling…", objectName="metric")
            self.metric_labels[name] = label
            grid.addWidget(label, index // 2, index % 2)
        column.addLayout(grid)
        self.task_label = self.text(column, "Running tasks: none")
        self.text(column, "INTEGRATIONS / No external account connections\nVOICE / Microphone off until Listen once is pressed")
        row = QHBoxLayout()
        for title, command in (("System report", "system status"), ("Open files", "open files"), ("Open Spotify", "open spotify")):
            self.button(row, title, lambda checked=False, c=command: self.submit(c))
        column.addLayout(row)
        self.text(column, "RECENT COMMANDS / Current session")
        self.recent = QListWidget()
        self.recent.setMaximumWidth(16777215)
        self.recent.setMinimumWidth(0)
        column.addWidget(self.recent, 1)

    def build_chat(self):
        column = self.layouts["AI Chat"]
        self.text(column, "Local rule-based commands. Conversational AI, streaming and model providers are planned. No API key is required.")
        self.chat = QTextBrowser()
        self.chat.setOpenExternalLinks(False)
        column.addWidget(self.chat, 1)
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Try ‘system status’ or ‘open spotify’")
        self.entry.setMaxLength(512)
        self.entry.returnPressed.connect(lambda: self.submit())
        row = QHBoxLayout()
        row.addWidget(self.entry, 1)
        self.send = self.button(row, "Send", lambda: self.submit(), primary=True)
        column.addLayout(row)
        controls = QHBoxLayout()
        self.button(controls, "Copy conversation", lambda: QApplication.clipboard().setText(self.chat.toPlainText()))
        self.button(controls, "Clear conversation", self.clear_chat)
        column.addLayout(controls)

    def build_voice(self):
        column = self.layouts["Voice Assistant"]
        self.text(column, "EXPERIMENTAL / Retained V2 Windows offline speech recognition.\nUses the default Windows microphone and an installed English recognizer. No wake-word monitoring. Voice output and microphone selection are planned for Phase 2.")
        self.voice_state = self.text(column, "Microphone off")
        self.listen_button = self.button(column, "Listen once (up to 8 seconds)", self.listen)
        self.listen_button.setEnabled(IS_WINDOWS)
        if not IS_WINDOWS:
            self.text(column, "Speech recognition requires Windows; this Linux environment cannot validate microphone behavior.")
        column.addStretch()

    def build_applications(self):
        column = self.layouts["Applications"]
        self.text(column, "Known apps are detected when launched. Add or override an alias with a trusted .exe. Paths are local to this PC. No shell strings, arguments or batch scripts.")
        self.aliases = QTableWidget(0, 2)
        self.aliases.setHorizontalHeaderLabels(("Alias", "Executable"))
        self.aliases.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.aliases.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.aliases.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        column.addWidget(self.aliases, 1)
        self.alias_name = QLineEdit()
        self.alias_name.setPlaceholderText("Alias, for example: ghostlink")
        column.addWidget(self.alias_name)
        self.alias_path = QLineEdit()
        self.alias_path.setPlaceholderText("Absolute path to a trusted .exe")
        column.addWidget(self.alias_path)
        row = QHBoxLayout()
        self.button(row, "Browse", self.browse_alias)
        self.button(row, "Save alias", self.save_alias)
        self.button(row, "Remove selected", self.remove_alias)
        column.addLayout(row)
        self.refresh_aliases()

    def build_automation(self):
        column = self.layouts["Automation"]
        self.text(column, "MANUAL WORKFLOW / System report\nPermission: system.read • One read-only step • Stops on failure\nWorkflow editing, scheduling and file organization are planned.")
        self.button(column, "Run system report", self.workflow)
        self.workflow_log = QTextBrowser()
        column.addWidget(self.workflow_log, 1)

    def build_integrations(self):
        column = self.layouts["Integrations"]
        for name, status, command in (
            ("Spotify", "Shortcut and Windows media keys only. No OAuth or playback data connection.", "open spotify"),
            ("iPhone / Phone Link", "Opens Windows Phone Link. Pair there; ZIVRA has no phone data access.", "open phone link"),
            ("Instagram", "Browser shortcut only. No messages connected. Official messaging needs account eligibility and Meta permissions.", "open instagram"),
            ("GhostLink", "Backend absent from supplied ZIP. Configure its executable alias in Applications. No paired devices or transfers.", "open ghostlink"),
        ):
            self.text(column, f"{name.upper()} / NOT CONNECTED\n{status}")
            self.button(column, f"Launch {name}", lambda checked=False, c=command: self.submit(c))
        column.addStretch()

    def build_monitor(self):
        column = self.layouts["System Monitor"]
        self.monitor_text = self.text(column, "Sampling…")
        self.text(column, "Metrics update every two seconds in a background worker. CPU is sampled over a short interval. Network is the sum of bytes sent and received across interfaces. Process memory can be shared between processes.")
        self.button(column, "Show largest memory users", lambda: self.submit("what's using my ram"))
        column.addStretch()

    def build_files(self):
        column = self.layouts["File Manager"]
        self.text(column, "Phase 1 folder shortcuts. No file mutation or sharing. File browsing and preview/undo organization are planned.")
        self.button(column, "Open File Explorer", lambda: self.submit("open files"))
        self.button(column, "Open Downloads", lambda: self.submit("open downloads"))
        column.addStretch()

    def build_plugins(self):
        column = self.layouts["Plugins"]
        self.text(column, "Bundled allowlist only. Plugins run as trusted application code, not sandboxed third-party code. Disabling a plugin disables its commands. Dashboard monitoring is part of the core.")
        self.plugin_checks = {}
        for identifier, factory in self.assistant.plugins.factories.items():
            manifest = factory().manifest
            check = QCheckBox(f"{manifest.name} / {manifest.version} / {', '.join(manifest.permissions)}")
            check.setChecked(identifier in self.assistant.plugins.plugins)
            check.toggled.connect(lambda enabled, key=identifier: self.toggle_plugin(key, enabled))
            column.addWidget(check)
            self.plugin_checks[identifier] = check
        self.plugin_status = self.text(column, "")
        self.refresh_plugins()
        column.addStretch()

    def build_settings(self):
        column = self.layouts["Settings"]
        self.text(column, f"ZIVRA {__version__} / Settings schema 1\nStored locally at {self.settings.directory}\nNo passwords or access tokens are stored here.")
        self.history_check = QCheckBox("Store command history on this PC (off by default)")
        self.history_check.setChecked(self.settings.get("remember_history"))
        self.history_check.toggled.connect(self.toggle_history)
        column.addWidget(self.history_check)
        self.tray_check = QCheckBox("Minimize to system tray when closing (when a tray is available)")
        self.tray_check.setChecked(self.settings.get("minimize_to_tray"))
        self.tray_check.toggled.connect(lambda value: self.save_setting("minimize_to_tray", value))
        column.addWidget(self.tray_check)
        self.startup_check = QCheckBox("Start ZIVRA when I sign into Windows")
        try:
            self.startup_check.setChecked(self.startup.enabled())
        except OSError as error:
            self.text(column, f"Startup state unavailable: {error}")
        self.startup_check.setEnabled(IS_WINDOWS)
        self.startup_check.toggled.connect(self.toggle_startup)
        column.addWidget(self.startup_check)
        self.button(column, "Export preferences…", self.export_settings)
        self.button(column, "Delete stored command history", self.clear_chat)
        self.button(column, "Reset preferences…", self.reset_settings)
        self.text(column, "Export includes executable paths, but excludes history. Disabling history deletes stored entries. Reset does not change Windows startup registration; use its separate toggle.")
        column.addStretch()

    def install_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("ZIVRA / Local assistant")
        menu = QMenu(self)
        restore = QAction("Restore ZIVRA", self)
        restore.triggered.connect(self.restore)
        menu.addAction(restore)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.request_quit)
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.restore() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()

    def restore(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def start_job(self, function, callback):
        job = Job(function)
        self.jobs.add(job)

        def finished(value, error):
            self.jobs.discard(job)
            callback(value, error)
            if self.quitting and not self.jobs:
                QTimer.singleShot(0, self.request_quit)

        job.signals.finished.connect(finished)
        self.pool.start(job)

    def foreground(self, function, callback):
        if self.foreground_busy or self.quitting:
            self.statusBar().showMessage("Wait for the current command or voice request to finish")
            return False
        self.foreground_busy = True
        self.send.setEnabled(False)
        self.listen_button.setEnabled(False)
        self.task_label.setText("Running tasks: one command / voice request")

        def done(value, error):
            self.foreground_busy = False
            self.send.setEnabled(True)
            self.listen_button.setEnabled(IS_WINDOWS)
            self.task_label.setText("Running tasks: none")
            callback(value, error)

        self.start_job(function, done)
        return True

    def add_message(self, speaker, message):
        color = "#191C21" if speaker == "ZIVRA" else "#30343B"
        self.chat.append(f'<table width="100%" bgcolor="{color}" cellpadding="12"><tr><td><b>{speaker}</b><br>{escape(message).replace(chr(10), "<br>")}</td></tr></table><br>')
        scrollbar = self.chat.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def submit(self, command=None):
        query = command if isinstance(command, str) else self.entry.text().strip()
        if not query or self.foreground_busy or self.quitting:
            return
        self.entry.clear()
        self.navigation.setCurrentRow(1)
        self.add_message("YOU", query)
        self.recent.insertItem(0, query)
        if self.recent.count() > 20:
            self.recent.takeItem(20)
        epoch = self.history_epoch

        def answered(value, error):
            if epoch == self.history_epoch:
                self.add_message("ZIVRA", error or value)

        self.foreground(lambda: self.assistant.respond(query), answered)

    def listen(self):
        from zivra.voice import listen_once
        self.voice_state.setText("Listening for one command…")

        def recognized(value, error):
            self.voice_state.setText("Microphone off" + (f" • {error}" if error else ""))
            if value:
                self.submit(value)

        if not self.foreground(listen_once, recognized):
            self.voice_state.setText("Microphone off • Wait for the current task")

    def workflow(self):
        self.foreground(self.assistant.system_workflow, lambda value, error: self.workflow_log.setPlainText(error or value))

    def tick(self):
        self.clock.setText(datetime.now().astimezone().strftime("%A, %d %B %Y  /  %H:%M:%S %Z"))
        if not self.monitor_busy and not self.quitting:
            self.monitor_busy = True
            self.start_job(self.performance.sample, self.update_metrics)

    def update_metrics(self, metrics, error):
        self.monitor_busy = False
        if error:
            self.monitor_text.setText("Metrics unavailable: " + error)
            return
        values = {"CPU": f"{metrics['cpu']:.0f}%", "Memory": f"{metrics['memory']:.0f}%",
                  "Network": "Sampling…" if metrics['network_kbps'] is None else f"{metrics['network_kbps']:.1f} KB/s",
                  "Battery": "Not reported" if metrics['battery'] is None else f"{metrics['battery']:.0f}%"}
        for name, value in values.items():
            self.metric_labels[name].setText(f"{name}\n{value}")
        self.monitor_text.setText("\n\n".join(f"{name}: {value}" for name, value in values.items()) +
            f"\n\nAvailable RAM: {metrics['available_gb']:.1f} GB\nDisk free: {metrics['disk_free_gb']:.1f} GB\nZIVRA process RSS: {metrics['rss_mb']:.1f} MB")

    def confirm(self, text):
        return QMessageBox.question(self, "Confirm ZIVRA change", text, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes

    def show_error(self, error):
        QMessageBox.warning(self, "ZIVRA", str(error))

    def save_setting(self, key, value):
        try:
            self.settings.set(key, value)
        except Exception as error:
            self.show_error(error)

    def toggle_history(self, value):
        self.save_setting("remember_history", value)

    def clear_chat(self):
        self.history_epoch += 1
        self.settings.clear_history()
        self.chat.clear()
        self.recent.clear()
        # Prevent an in-flight command from repopulating persistent history.
        if self.foreground_busy:
            self.history_check.setChecked(False)

    def browse_alias(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a trusted application", "", "Windows application (*.exe)")
        if path:
            self.alias_path.setText(path)

    def save_alias(self):
        if not self.confirm("Trust this executable for future launch commands? Only select applications you trust."):
            return
        try:
            aliases = self.settings.get("application_aliases")
            aliases[self.alias_name.text().strip().lower()] = self.alias_path.text().strip()
            self.settings.set("application_aliases", aliases)
            self.refresh_aliases()
        except Exception as error:
            self.show_error(error)

    def remove_alias(self):
        row = self.aliases.currentRow()
        if row >= 0:
            aliases = self.settings.get("application_aliases")
            aliases.pop(self.aliases.item(row, 0).text(), None)
            self.settings.set("application_aliases", aliases)
            self.refresh_aliases()

    def refresh_aliases(self):
        aliases = self.settings.get("application_aliases")
        self.aliases.setRowCount(len(aliases))
        for row, (name, path) in enumerate(sorted(aliases.items())):
            self.aliases.setItem(row, 0, QTableWidgetItem(name))
            self.aliases.setItem(row, 1, QTableWidgetItem(path))

    def refresh_plugins(self):
        self.plugin_status.setText("\n".join(f"{key}: {value}" for key, value in self.assistant.plugins.status().items()))

    def toggle_plugin(self, identifier, value):
        if self.foreground_busy:
            self.show_error("Wait for the current command to finish before changing plugins")
        else:
            try:
                self.assistant.plugins.set_enabled(identifier, value)
            except Exception as error:
                self.show_error(error)
        check = self.plugin_checks[identifier]
        check.blockSignals(True)
        check.setChecked(identifier in self.assistant.plugins.plugins)
        check.blockSignals(False)
        self.refresh_plugins()

    def toggle_startup(self, value):
        try:
            approved = self.confirm("Change ZIVRA's Windows sign-in startup entry for your user? No administrator access is required.")
            if approved:
                self.startup.set_enabled(value, approved=True)
        except Exception as error:
            self.show_error(error)
        finally:
            self.startup_check.blockSignals(True)
            try:
                self.startup_check.setChecked(self.startup.enabled())
            except OSError as error:
                self.show_error(f"Could not read startup state: {error}")
            finally:
                self.startup_check.blockSignals(False)

    def export_settings(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export preferences", "zivra-settings.json", "JSON (*.json)")
        if path:
            try:
                self.settings.export(path)
            except Exception as error:
                self.show_error(error)

    def reset_settings(self):
        if self.foreground_busy:
            self.show_error("Wait for the current command to finish before resetting")
            return
        if not self.confirm("Delete ZIVRA preferences and history? Windows startup registration will be unchanged."):
            return
        self.settings.reset()
        self.clear_chat()
        self.history_check.setChecked(False)
        self.tray_check.setChecked(True)
        self.refresh_aliases()
        for identifier, check in self.plugin_checks.items():
            self.assistant.plugins.set_enabled(identifier, True)
            check.blockSignals(True)
            check.setChecked(identifier in self.assistant.plugins.plugins)
            check.blockSignals(False)
        self.refresh_plugins()

    def request_quit(self):
        self.quitting = True
        self.timer.stop()
        if self.jobs:
            self.statusBar().showMessage("Finishing active work before quitting (voice can take up to 19 seconds)…")
            return
        self.assistant.shutdown()
        if self.tray:
            self.tray.hide()
        self.close()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if not self.quitting and self.tray and self.settings.get("minimize_to_tray"):
            self.hide()
            event.ignore()
        elif self.jobs:
            event.ignore()
            self.request_quit()
        else:
            self.timer.stop()
            self.assistant.shutdown()
            event.accept()
