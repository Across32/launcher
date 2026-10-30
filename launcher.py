#!/usr/bin/env python3
"""KDE Plasma/EndeavourOS launcher for the Across32 applications."""
from __future__ import annotations

from pathlib import Path
import json
import os
import shlex
import shutil
import sys
import webbrowser

from PySide6.QtCore import Qt, QSize, QProcess, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from app_manager import APPS, App, installed, open_application, repo_url, revision, version
from app_icons import delete_icon, save_icon, selected_icon
from autostart import enabled as autostart_enabled, set_enabled as set_autostart_enabled
from version_info import build_label, title_text
from update_checker import read_cache, update_available


STYLE = """
* { font-family: 'Noto Sans', 'DejaVu Sans', sans-serif; }
QMainWindow, QWidget#root, QScrollArea, QWidget#gridWidget {
    background: #202b39;
    color: #e4eaf2;
}
QFrame#header {
    background: #151f2d;
    border-bottom: 1px solid #3e536b;
}
QLabel#brand {
    color: #eff5fd;
    font-size: 25px;
    font-weight: 900;
    letter-spacing: 2px;
}
QLabel#buildVersion {
    color: #e4f4ff;
    background: #345472;
    border: 1px solid #6385a6;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 12px;
    font-weight: 800;
}
QLabel#micro {
    color: #89a9c7;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
}
QLabel#summary, QLabel#footer {
    color: #a0b3c8;
    font-size: 12px;
}
QFrame#card {
    background: #29384a;
    border: 1px solid #40566e;
    border-radius: 13px;
}
QLabel#appName { color: #eff5fc; font-size: 20px; font-weight: 800; }
QLabel#category { color: #b0c0d1; font-size: 12px; }
QLabel#description { color: #c7d5e3; font-size: 13px; }
QLabel#status { font-size: 11px; font-weight: 700; }
QLabel#updateAvailable {
    font-size: 11px; font-weight: 800; color: #ff747b;
}
QLabel#version { color: #95abc1; font-size: 11px; }
QLineEdit, QComboBox {
    background: #324458;
    color: #f4f8fe;
    border: 1px solid #536b83;
    border-radius: 6px;
    min-height: 35px;
    padding: 2px 9px;
    selection-background-color: #567b9f;
}
QPushButton {
    border-radius: 6px;
    font-size: 11px;
    font-weight: 800;
    min-height: 34px;
    padding: 0px 11px;
}
QPushButton#primary {
    color: #fff;
    background: #537da6;
    border: 1px solid #638db6;
}
QPushButton#primary:hover { background: #638fb8; }
QPushButton#secondary {
    color: #dbe8f4;
    background: #33485f;
    border: 1px solid #57718c;
}
QPushButton#secondary:hover { background: #425d7a; }
QPushButton#secondary:disabled, QPushButton#primary:disabled {
    color: #8699ac; background: #2b3a4b; border-color: #3a4d60;
}
QPushButton#history {
    color: #b6d1eb;
    background: #243648;
    border: 1px solid #496179;
    text-align: center;
}
QPushButton#history:hover { background: #37516b; color: white; }
QPushButton#link {
    background: transparent;
    border: 0;
    color: #a3bdd7;
    font-size: 10px;
    letter-spacing: 1px;
}
QPushButton#link:hover { color: #f1f7ff; }
QPushButton#refresh, QPushButton#tray {
    color: #d8e9f7;
    background: #2c4158;
    border: 1px solid #4c6680;
    font-size: 13px;
}
QPushButton#refresh:hover, QPushButton#tray:hover { background: #3c5874; }
QPushButton#appIcon {
    color: #f8fbfe;
    font-weight: 900;
    font-size: 24px;
    border-radius: 10px;
    border: 1px solid #7494b3;
    padding: 0;
}
QPushButton#backup {
    color: #eff8ff;
    background: #3b658c;
    border: 1px solid #6c95bd;
    font-size: 11px;
}
QPushButton#backup:hover { background: #4c7eaa; }
QPushButton#backup:disabled { background: #35475a; color: #7d96ae; }
QCheckBox#autostart {
    color: #eff7ff; font-size: 13px; font-weight: 800;
    spacing: 10px;
}
QLabel#autostartStatus { color: #95b6d4; font-size: 11px; }
QLabel#updatesStatus { color: #a8c8df; font-size: 12px; font-weight: 600; }
QFrame#startupSettings {
    background: #273a50;
    border: 1px solid #526f8a;
    border-radius: 8px;
}
QCheckBox#autostart::indicator {
    width: 17px; height: 17px;
}
QCheckBox#autostart::indicator:unchecked {
    background: #2b3c51; border: 1px solid #6a849e; border-radius: 4px;
}
QCheckBox#autostart::indicator:checked {
    background: #6094be; border: 2px solid #b8d9f2; border-radius: 4px;
}
QDialog#historyDialog, QDialog#historyDialog QScrollArea,
QDialog#historyDialog QWidget#historyContent {
    background: #1e2c3b;
    color: #e9f1f8;
}
QFrame#historyCard {
    background: #2a3d51;
    border: 1px solid #48617b;
    border-radius: 8px;
}
QLabel#historyTitle { color: #f0f6fc; font-size: 16px; font-weight: 800; }
QLabel#historyDate { color: #92bce3; font-size: 12px; font-weight: 700; }
QLabel#historyDetail { color: #c7d6e6; font-size: 12px; }
QMessageBox, QFileDialog { background: #243449; color: #e7eef6; }
"""



class AppCard(QFrame):
    def __init__(self, spec: App, active: bool, busy: bool, parent: "Launcher",
                 needs_update: bool = False, latest_version: str = ""):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumWidth(310)
        self.setMinimumHeight(323)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 16)
        outer.setSpacing(11)

        top = QHBoxLayout()
        tag = QLabel(spec.category.upper())
        tag.setObjectName("micro")
        top.addWidget(tag, 1)
        link = QPushButton("GITHUB ↗")
        link.setObjectName("link")
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(repo_url(spec)[:-4])))
        top.addWidget(link)
        outer.addLayout(top)

        title_row = QHBoxLayout()
        icon = QPushButton(spec.letter)
        icon.setObjectName("appIcon")
        icon.setFixedSize(55, 55)
        icon.setCursor(Qt.CursorShape.PointingHandCursor)
        icon.setToolTip("Kattints az ikon cseréjéhez. Jobb kattintás: alaphelyzet.")
        icon.setStyleSheet(f"QPushButton#appIcon {{ background: {spec.color}; }}")
        chosen_icon = selected_icon(spec)
        if not chosen_icon.isNull():
            icon.setText("")
            icon.setIcon(chosen_icon)
            icon.setIconSize(QSize(43, 43))
        icon.clicked.connect(lambda: parent.choose_icon(spec))
        icon.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        icon.customContextMenuRequested.connect(lambda _pos: parent.reset_icon(spec))
        title_row.addWidget(icon)
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        name = QLabel(spec.title)
        name.setObjectName("appName")
        sub = QLabel(spec.category)
        sub.setObjectName("category")
        text_col.addWidget(name)
        text_col.addWidget(sub)
        title_row.addLayout(text_col, 1)
        outer.addLayout(title_row)

        description = QLabel(spec.description)
        description.setObjectName("description")
        description.setWordWrap(True)
        description.setMinimumHeight(40)
        outer.addWidget(description)

        badge = QLabel("●  FOLYAMATBAN" if busy else
                       ("●  TELEPÍTVE" if active else "○  NINCS TELEPÍTVE"))
        badge.setObjectName("status")
        badge.setStyleSheet("color: #ffd18c;" if busy else
                            ("color: #80d5b3;" if active else "color: #a6b5c5;"))
        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        status_row.addWidget(badge)
        if active and needs_update:
            warning = QLabel("●  FRISSÍTÉS ELÉRHETŐ")
            warning.setObjectName("updateAvailable")
            warning.setToolTip(
                "Új kiadás a GitHubon: "
                + (latest_version or "új Git-revízió")
                + ". A jelzés a legújabb változat telepítéséig megmarad."
            )
            status_row.addWidget(warning)
        status_row.addStretch()
        outer.addLayout(status_row)

        local_version = version(spec)
        short_sha = revision(spec)
        detail = f"Verzió: {local_version}"
        if short_sha:
            detail += f"   •   Git: {short_sha}"
        label = QLabel(detail)
        label.setObjectName("version")
        outer.addWidget(label)
        outer.addStretch(1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        if active:
            launch = QPushButton("MEGNYITÁS")
            launch.setObjectName("primary")
            launch.setEnabled(not busy)
            launch.clicked.connect(lambda: parent.open_app(spec))
            actions.addWidget(launch, 2)
            update = QPushButton("FRISSÍTÉS")
            update.setObjectName("secondary")
            update.setEnabled(not busy)
            update.clicked.connect(lambda: parent.operation(spec, "update"))
            actions.addWidget(update, 1)
        else:
            install_button = QPushButton("TELEPÍTÉS")
            install_button.setObjectName("primary")
            install_button.setEnabled(not busy)
            install_button.clicked.connect(lambda: parent.operation(spec, "install"))
            actions.addWidget(install_button)
        outer.addLayout(actions)
        history = QPushButton("◷  FRISSÍTÉSI ELŐZMÉNYEK")
        history.setObjectName("history")
        history.setToolTip("Valódi GitHub-kiadások és változások magyar nyelven")
        history.clicked.connect(lambda: parent.show_history(spec))
        outer.addWidget(history)



class HistoryDialog(QDialog):
    """Responsive, scrollable, real-source history; no UI blocking on GitHub."""
    def __init__(self, spec: App, parent: "Launcher"):
        super().__init__(parent)
        self.spec = spec
        self.setObjectName("historyDialog")
        self.setWindowTitle(f"{spec.title} – Frissítési előzmények")
        self.resize(790, 690)
        self.setMinimumSize(540, 410)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.layout_root = QVBoxLayout(self)
        self.layout_root.setContentsMargins(20, 18, 20, 18)
        title = QLabel(f"{spec.title} – Frissítési előzmények")
        title.setObjectName("historyTitle")
        self.layout_root.addWidget(title)
        self.note = QLabel("Valódi GitHub-adatok betöltése…")
        self.note.setObjectName("historyDetail")
        self.note.setWordWrap(True)
        self.layout_root.addWidget(self.note)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.content.setObjectName("historyContent")
        self.entries_layout = QVBoxLayout(self.content)
        self.entries_layout.setContentsMargins(0, 7, 8, 12)
        self.entries_layout.setSpacing(12)
        self.scroll.setWidget(self.content)
        self.layout_root.addWidget(self.scroll)
        close_button = QPushButton("BEZÁRÁS")
        close_button.setObjectName("secondary")
        close_button.clicked.connect(self.close)
        self.layout_root.addWidget(close_button)

        self.worker = QProcess(self)
        self.worker.setProgram(sys.executable)
        self.worker.setArguments([
            str(Path(__file__).resolve().parent / "release_history.py"), spec.key
        ])
        self.worker.finished.connect(self.completed)
        self.worker.errorOccurred.connect(self.process_error)
        self.worker.start()

    def process_error(self, _error):
        if self.worker.state() == QProcess.ProcessState.NotRunning:
            self.note.setText("Nem sikerült elindítani a frissítési előzmények lekérését.")

    def completed(self, code, _status):
        if code:
            error = bytes(self.worker.readAllStandardError()).decode("utf-8", "replace").strip()
            self.note.setText("Hiba az előzmények lekérésekor: " + (error or "Ismeretlen hiba"))
            return
        try:
            output = json.loads(bytes(self.worker.readAllStandardOutput()).decode("utf-8"))
            items = output["items"]
        except (ValueError, KeyError, TypeError) as exc:
            self.note.setText(f"Az előzmények értelmezése sikertelen: {exc}")
            return
        self.note.setText(output.get("note", ""))
        if not items:
            self.entries_layout.addWidget(QLabel("Nincs elérhető változásbejegyzés."))
            return
        for item in items:
            card = QFrame()
            card.setObjectName("historyCard")
            block = QVBoxLayout(card)
            block.setContentsMargins(15, 13, 15, 14)
            block.setSpacing(7)
            first = QHBoxLayout()
            version = QLabel(item["version"])
            version.setObjectName("historyTitle")
            first.addWidget(version)
            first.addStretch()
            date = QLabel(item["date"])
            date.setObjectName("historyDate")
            first.addWidget(date)
            block.addLayout(first)
            heading = QLabel(item["title"])
            heading.setObjectName("historyDetail")
            heading.setWordWrap(True)
            block.addWidget(heading)
            details = QLabel(item["description"])
            details.setObjectName("historyDetail")
            details.setTextFormat(Qt.TextFormat.PlainText)
            details.setWordWrap(True)
            details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            block.addWidget(details)
            self.entries_layout.addWidget(card)
        self.entries_layout.addStretch(1)

    def closeEvent(self, event):
        if self.worker.state() != QProcess.ProcessState.NotRunning:
            self.worker.kill()
            self.worker.waitForFinished(3000)
        super().closeEvent(event)


class Launcher(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(title_text())
        self.setMinimumSize(940, 640)
        self.resize(1280, 795)
        self.running: dict[str, QProcess] = {}
        self.backup_process = None
        self.histories = []
        self.tray = None
        self.update_records = read_cache()
        self.update_process = None
        self._update_output = b""
        self._scan_results = {}
        self._scan_issue = ""
        self._manual_update_summary = False
        self._scan_watchdog = QTimer(self)
        self._scan_watchdog.setSingleShot(True)
        self._scan_watchdog.timeout.connect(self.update_scan_timeout)
        self.setup_tray()

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(27, 18, 27, 20)
        header_layout.setSpacing(14)

        head = QHBoxLayout()
        brand = QLabel("ACROSS32")
        brand.setObjectName("brand")
        head.addWidget(brand)
        self.build_badge = QLabel(build_label())
        self.build_badge.setObjectName("buildVersion")
        self.build_badge.setToolTip(
            "Az éppen futó Launcher verziója és a GitHubról telepített forrás Git-azonosítója."
        )
        head.addWidget(self.build_badge)
        subtitle = QLabel("CRAFT APP SUITE  /  ENDEAVOUROS")
        subtitle.setObjectName("micro")
        head.addWidget(subtitle)
        head.addStretch()
        self.backup_button = QPushButton("⬇  GITHUB BACKUP")
        self.backup_button.setObjectName("backup")
        self.backup_button.setToolTip("Privát Across32 GitHub repók biztonsági mentése Git-tükör és bundle fájl formájában")
        self.backup_button.clicked.connect(self.start_backup)
        head.addWidget(self.backup_button)
        tray_button = QPushButton("TÁLCÁRA")
        tray_button.setObjectName("tray")
        tray_button.setToolTip("Az ablak minimalizálása; elérhető rendszertálcán is, ha támogatott")
        tray_button.clicked.connect(self.minimize_to_tray)
        head.addWidget(tray_button)
        refresh = QPushButton("↻")
        refresh.setObjectName("refresh")
        refresh.setFixedSize(40, 36)
        refresh.setToolTip("Telepített alkalmazások újraellenőrzése")
        refresh.clicked.connect(self.manual_refresh)
        head.addWidget(refresh)
        header_layout.addLayout(head)

        tools = QHBoxLayout()
        self.summary = QLabel()
        self.summary.setObjectName("summary")
        tools.addWidget(self.summary)
        tools.addStretch()
        self.filter = QComboBox()
        self.filter.addItems(["Összes alkalmazás", "Telepítve", "Nincs telepítve"])
        self.filter.currentIndexChanged.connect(self.refresh)
        self.filter.setFixedWidth(190)
        tools.addWidget(self.filter)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Alkalmazások keresése")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(245)
        self.search.textChanged.connect(self.refresh)
        tools.addWidget(self.search)

        header_layout.addLayout(tools)
        # Own full-width settings row: the previous checkbox was squeezed
        # between search and filter controls on narrower KDE displays.
        startup_box = QFrame()
        startup_box.setObjectName("startupSettings")
        startup_row = QHBoxLayout(startup_box)
        startup_row.setContentsMargins(15, 7, 15, 7)
        self.autostart_checkbox = QCheckBox("INDÍTÁS A RENDSZERREL · TÁLCÁRA")
        self.autostart_checkbox.setObjectName("autostart")
        self.autostart_checkbox.setToolTip(
            "KDE Plasma bejelentkezésekor kizárólag a rendszertálcán jelenjen meg."
        )
        self.autostart_checkbox.setChecked(autostart_enabled())
        self.autostart_checkbox.toggled.connect(self.change_autostart)
        startup_row.addWidget(self.autostart_checkbox)
        startup_row.addStretch()
        self.autostart_status = QLabel()
        self.autostart_status.setObjectName("autostartStatus")
        startup_row.addWidget(self.autostart_status)
        header_layout.addWidget(startup_box)
        self.update_autostart_status()
        self.updates_status = QLabel(
            "GitHub verzióellenőrzés: korábbi adatok betöltve · ellenőrzés indul…"
        )
        self.updates_status.setObjectName("updatesStatus")
        self.updates_status.setToolTip(
            "A fenti ↻ gombbal manuálisan ellenőrizheted a 8 repót. "
            "Az ellenőrzés végén részletes eredmény jelenik meg."
        )
        self.updates_status.setWordWrap(True)
        header_layout.addWidget(self.updates_status)
        layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_widget = QWidget()
        self.grid_widget.setObjectName("gridWidget")
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(24, 22, 24, 24)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(17)
        self.scroll.setWidget(self.grid_widget)
        layout.addWidget(self.scroll, 1)

        self.footer = QLabel(
            "  A telepítés és frissítés GitHub-forrásból történik. "
            "A hitelesítéshez és a rendszerjogosultságokhoz Konsole ablak nyílik meg.  "
        )
        self.footer.setObjectName("footer")
        self.footer.setContentsMargins(24, 10, 16, 12)
        layout.addWidget(self.footer)
        self.timer = QTimer(self)
        self.timer.setInterval(3500)
        self.timer.timeout.connect(self.refresh_if_running)
        self.timer.start()
        self.refresh()
        # Network lookups are performed by a separate subprocess, not in
        # QMainWindow.refresh() or on the Qt UI thread.
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(30 * 60 * 1000)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start()
        if os.environ.get("ACROSS32_DISABLE_UPDATE_CHECK") != "1":
            QTimer.singleShot(300, self.check_for_updates)


    def setup_tray(self):
        # Register even when Plasma's panel is still starting. Qt automatically
        # displays an already-visible tray icon when a system tray appears.
        tray = QSystemTrayIcon(self)
        icon_file = Path(__file__).resolve().parent / "assets/across32-launcher.svg"
        icon = QIcon(str(icon_file))
        if icon.isNull():
            icon = QIcon.fromTheme("applications-system")
        tray.setIcon(icon)
        tray.setToolTip(title_text())
        menu = QMenu(self)
        show_action = menu.addAction("Megnyitás")
        show_action.triggered.connect(self.restore_from_tray)
        minimize_action = menu.addAction("Minimalizálás")
        minimize_action.triggered.connect(self.showMinimized)
        menu.addSeparator()
        quit_action = menu.addAction("Teljes bezárás")
        quit_action.triggered.connect(self.close)
        tray.setContextMenu(menu)
        tray.activated.connect(
            lambda reason: self.restore_from_tray()
            if reason == QSystemTrayIcon.ActivationReason.Trigger else None
        )
        tray.show()
        self.tray = tray

    def minimize_to_tray(self):
        if self.tray is not None and QSystemTrayIcon.isSystemTrayAvailable():
            self.hide()
        else:
            # KDE's ordinary taskbar is still available even without a tray.
            self.showMinimized()

    def start_in_tray(self):
        """Keep the desktop clear even while the Plasma tray is starting."""
        self._startup_tray_pending = True
        self._startup_tray_checks = 0
        self.hide()
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._startup_tray_pending = False
            return
        self._startup_tray_timer = QTimer(self)
        self._startup_tray_timer.setInterval(1000)
        self._startup_tray_timer.timeout.connect(self.check_startup_tray)
        self._startup_tray_timer.start()

    def check_startup_tray(self):
        if not getattr(self, "_startup_tray_pending", False):
            self._startup_tray_timer.stop()
            return
        self._startup_tray_checks += 1
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._startup_tray_pending = False
            self._startup_tray_timer.stop()
        elif self._startup_tray_checks >= 60:
            # Only fall back to a MINIMIZED taskbar window if the Plasma
            # system tray is genuinely unavailable after a full minute.
            self._startup_tray_pending = False
            self._startup_tray_timer.stop()
            self.showMinimized()

    def restore_from_tray(self):
        self._startup_tray_pending = False
        if hasattr(self, "_startup_tray_timer"):
            self._startup_tray_timer.stop()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def update_autostart_status(self):
        enabled = autostart_enabled()
        self.autostart_status.setText(
            "Aktív · csak rendszertálca" if enabled else "Kikapcsolva"
        )

    def change_autostart(self, desired: bool):
        try:
            set_autostart_enabled(
                desired, Path(__file__).resolve().parent / "run.sh"
            )
        except (OSError, RuntimeError, ValueError) as exc:
            self.autostart_checkbox.blockSignals(True)
            self.autostart_checkbox.setChecked(autostart_enabled())
            self.autostart_checkbox.blockSignals(False)
            QMessageBox.warning(self, "Automatikus indítás", str(exc))
        self.update_autostart_status()

    def manual_refresh(self):
        """Refresh local versions AND request an explicit eight-repo report."""
        self.refresh()
        self.check_for_updates(manual=True)

    def check_for_updates(self, manual: bool = False):
        if os.environ.get("ACROSS32_DISABLE_UPDATE_CHECK") == "1":
            if manual:
                self.updates_status.setText("GitHub ellenőrzés a tesztkörnyezetben kikapcsolva.")
            return
        if manual:
            self._manual_update_summary = True
        if self.update_process is not None:
            self.updates_status.setText(
                f"GitHub: ellenőrzés folyamatban… "
                f"({len(self._scan_results)}/{len(APPS)} repó)"
            )
            return
        self._scan_results = {}
        self._scan_issue = ""
        self._update_output = b""
        self.updates_status.setText(
            f"GitHub: verziók ellenőrzése folyamatban… (0/{len(APPS)} repó)"
        )
        worker = QProcess(self)
        worker.setProgram(sys.executable)
        worker.setArguments([
            "-u", str(Path(__file__).resolve().parent / "update_checker.py"), "--scan"
        ])
        worker.readyReadStandardOutput.connect(self.read_update_results)
        worker.finished.connect(self.update_scan_finished)
        worker.errorOccurred.connect(self.update_scan_error)
        self.update_process = worker
        worker.start()
        # External GitHub calls must not hold an invisible process forever.
        self._scan_watchdog.start(120_000)

    def consume_update_result(self, record) -> bool:
        """Accept one backend event, including failure; preserve old updates."""
        if not isinstance(record, dict):
            return False
        key = record.get("key")
        if key not in {app.key for app in APPS}:
            return False
        if (record.get("ok") is True
                and isinstance(record.get("remote_version"), str)
                and isinstance(record.get("remote_sha"), str)):
            self.update_records[key] = {
                "remote_version": record["remote_version"],
                "remote_sha": record["remote_sha"],
            }
            self._scan_results[key] = {"ok": True}
            return True
        if record.get("ok") is False:
            self._scan_results[key] = {
                "ok": False,
                "error": str(record.get("error") or "Ismeretlen GitHub-hiba")[:320],
            }
        return False

    def checked_update_count(self) -> int:
        return sum(
            bool(installed(spec) and update_available(
                spec, version(spec), self.update_records.get(spec.key, {})
            )) for spec in APPS
        )

    def show_scan_progress(self):
        finished = len(self._scan_results)
        errors = sum(item.get("ok") is False for item in self._scan_results.values())
        self.updates_status.setText(
            f"GitHub: {finished}/{len(APPS)} repó ellenőrizve "
            f"· {self.checked_update_count()} frissítés elérhető"
            + (f" · {errors} hiba" if errors else "")
        )
        if errors:
            self.updates_status.setToolTip(
                "Az ↻ gombbal részletes hibaüzenetet kérhetsz. "
                "A legutóbb sikeresen lekért verzióadatok megmaradtak."
            )

    def read_update_results(self):
        worker = self.update_process
        if worker is None:
            return
        self._update_output += bytes(worker.readAllStandardOutput())
        modified = False
        while b"\n" in self._update_output:
            line, self._update_output = self._update_output.split(b"\n", 1)
            try:
                record = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                continue
            modified |= self.consume_update_result(record)
        if modified:
            self.refresh()
        self.show_scan_progress()

    def update_scan_timeout(self):
        worker = self.update_process
        if worker and worker.state() != QProcess.ProcessState.NotRunning:
            self._scan_issue = "GitHub ellenőrzés: 120 másodperces időtúllépés."
            worker.kill()

    def scan_report(self) -> str:
        """Show the exact local and remote versions and concrete errors."""
        report = [
            f"GitHub verzióellenőrzés – {len(self._scan_results)}/{len(APPS)} repó",
            "",
        ]
        for spec in APPS:
            local = version(spec)
            result = self._scan_results.get(spec.key, {})
            cached = self.update_records.get(spec.key, {})
            if result.get("ok"):
                remote = cached.get("remote_version") or (
                    "Git " + cached.get("remote_sha", "")[:8]
                )
                pending = bool(installed(spec) and
                               update_available(spec, local, cached))
                status = "FRISSÍTÉS ELÉRHETŐ" if pending else "nincs újabb verzió"
                report.append(f"{spec.title}: {local} → {remote} ({status})")
            else:
                reason = result.get("error") or (
                    self._scan_issue or "Nem érkezett válasz a GitHubtól."
                )
                report.append(f"{spec.title}: {local} – HIBA: {reason}")
        if self._scan_issue:
            report.extend(["", self._scan_issue])
        return "\n".join(report)

    def update_scan_finished(self, code, _status):
        worker = self.update_process
        if worker is None:
            return
        self._scan_watchdog.stop()
        self.read_update_results()
        self._scan_issue = self._scan_issue or (
            bytes(worker.readAllStandardError()).decode("utf-8", "replace").strip()[:400]
            if code != 0 else ""
        )
        if code and not self._scan_issue:
            self._scan_issue = f"Az ellenőrző folyamat hibakóddal állt le: {code}."
        report = self.scan_report()
        self.show_scan_progress()
        errors = sum(item.get("ok") is False for item in self._scan_results.values())
        if errors or len(self._scan_results) != len(APPS) or self._scan_issue:
            self.updates_status.setText(
                f"GitHub: {len(self._scan_results)}/{len(APPS)} repó ellenőrizve "
                f"· {errors} lekérési hiba · ↻ részletek"
            )
            self.updates_status.setToolTip(report)
        else:
            self.show_scan_progress()
        self.update_process = None
        self._update_output = b""
        worker.deleteLater()
        if self._manual_update_summary:
            self._manual_update_summary = False
            if errors or self._scan_issue or len(self._scan_results) != len(APPS):
                QMessageBox.warning(self, "GitHub frissítésellenőrzés – hiba", report)
            else:
                QMessageBox.information(self, "GitHub frissítésellenőrzés", report)

    def update_scan_error(self, _error):
        worker = self.update_process
        if not worker:
            return
        self._scan_issue = (
            "Az ellenőrző nem indítható: " + worker.errorString()
        )
        if worker.state() == QProcess.ProcessState.NotRunning:
            # FailedToStart doesn't always emit QProcess.finished.
            self.update_scan_finished(-1, QProcess.ExitStatus.CrashExit)

    def closeEvent(self, event):
        # Closing X is a REAL exit, never an implicit minimize-to-tray.
        self._scan_watchdog.stop()
        if self.update_process:
            self.update_process.kill()
            self.update_process.waitForFinished(1200)
            self.update_process = None
        for dlg in list(self.histories):
            dlg.close()
        if self.tray:
            self.tray.hide()
        if self.backup_process and self.backup_process.state() != QProcess.ProcessState.NotRunning:
            # The Konsole backup terminal is an independent user process.
            self.backup_process.setParent(None)
        for process in self.running.values():
            if process.state() != QProcess.ProcessState.NotRunning:
                process.setParent(None)
        event.accept()
        QApplication.quit()

    def choose_icon(self, spec: App):
        path, _filter = QFileDialog.getOpenFileName(
            self, f"{spec.title} – új ikon kiválasztása", str(Path.home()),
            "Képfájlok (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff);;Minden fájl (*)",
        )
        if not path:
            return
        try:
            save_icon(spec, path)
            self.refresh()
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Ikon nem menthető", str(exc))

    def reset_icon(self, spec: App):
        try:
            delete_icon(spec)
            self.refresh()
        except OSError as exc:
            QMessageBox.warning(self, "Ikon visszaállítása", str(exc))

    def show_history(self, spec: App):
        dialog = HistoryDialog(spec, self)
        self.histories.append(dialog)
        dialog.destroyed.connect(lambda _obj=None, dlg=dialog: self.remove_history(dlg))
        dialog.show()

    def remove_history(self, dialog):
        if dialog in self.histories:
            self.histories.remove(dialog)

    def start_backup(self):
        if self.backup_process is not None:
            return
        if not shutil.which("konsole"):
            QMessageBox.warning(self, "Hiányzó Konsole", "A mentéshez Konsole szükséges.")
            return
        backup_file = Path(__file__).resolve().parent / "github_backup.py"
        command = shlex.join([sys.executable, str(backup_file)])
        shell = (
            f"{command}; status=$?; "
            "printf '\\n--- GitHub Backup vége (kilépési kód: %s) ---\\n' \"$status\"; "
            "printf 'Enter: ablak bezárása...'; read -r _; exit \"$status\""
        )
        process = QProcess(self)
        process.setProgram("konsole")
        process.setArguments(["--title", "Across32 – GitHub Backup",
                              "-e", "bash", "-c", shell])
        process.finished.connect(self.backup_finished)
        process.errorOccurred.connect(self.backup_error)
        self.backup_process = process
        self.backup_button.setEnabled(False)
        self.backup_button.setText("MENTÉS FOLYAMATBAN…")
        process.start()

    def backup_error(self, _error):
        if self.backup_process is not None and self.backup_process.state() == QProcess.ProcessState.NotRunning:
            message = self.backup_process.errorString()
            self.backup_process = None
            self.backup_button.setEnabled(True)
            self.backup_button.setText("⬇  GITHUB BACKUP")
            QMessageBox.warning(self, "Backup indítási hiba", message)

    def backup_finished(self, code, _status):
        self.backup_process = None
        self.backup_button.setEnabled(True)
        self.backup_button.setText("⬇  GITHUB BACKUP")
        if code:
            QMessageBox.warning(self, "GitHub Backup",
                                "A mentés nem minden repónál sikerült. "
                                "A korábbi sikeres mentések megmaradtak. "
                                "A részleteket a Konsole ablak mutatta.")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # No resize-loop: layout only changes when switching columns.
        if hasattr(self, "grid"):
            col_count = 2 if self.width() < 1090 else 3
            if getattr(self, "_columns", None) != col_count:
                self.refresh()

    def refresh_if_running(self) -> None:
        if self.running:
            self.refresh()

    def refresh(self, *_args) -> None:
        if not hasattr(self, "grid"):
            return
        self._columns = 2 if self.width() < 1090 else 3
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        query = self.search.text().casefold().strip()
        state = {spec.key: installed(spec) for spec in APPS}
        total = sum(state.values())
        self.summary.setText(f"{total} telepítve  /  {len(APPS)} alkalmazás")
        shown = []
        for spec in APPS:
            active = state[spec.key]
            if query and query not in f"{spec.title} {spec.key} {spec.description} {spec.category}".casefold():
                continue
            if self.filter.currentIndex() == 1 and not active:
                continue
            if self.filter.currentIndex() == 2 and active:
                continue
            shown.append(spec)

        for i, spec in enumerate(shown):
            latest = self.update_records.get(spec.key, {})
            show_update = bool(state[spec.key] and
                               update_available(spec, version(spec), latest))
            card = AppCard(
                spec, state[spec.key], spec.key in self.running, self,
                needs_update=show_update,
                latest_version=latest.get("remote_version") or
                               ("Git " + latest.get("remote_sha", "")[:8]),
            )
            self.grid.addWidget(card, i // self._columns, i % self._columns)
        for column in range(3):
            self.grid.setColumnStretch(column, 1 if column < self._columns else 0)
        self.grid.setRowStretch((len(shown) + self._columns - 1) // self._columns, 1)
        if not shown:
            empty = QLabel("Nincs a feltételeknek megfelelő alkalmazás.")
            empty.setStyleSheet("color:#666;font-size:15px;")
            self.grid.addWidget(empty, 0, 0)

    def open_app(self, spec: App) -> None:
        try:
            open_application(spec)
        except (RuntimeError, OSError, ValueError) as exc:
            QMessageBox.critical(self, "Indítás sikertelen", f"{spec.title}\n\n{exc}")

    def operation(self, spec: App, action: str) -> None:
        if spec.key in self.running:
            return
        if not shutil.which("konsole"):
            QMessageBox.critical(self, "Hiányzó Konsole",
                                 "A telepítéshez és a sudo/GitHub bejelentkezéshez "
                                 "Konsole szükséges. Telepítés: sudo pacman -S konsole")
            return
        backend = Path(__file__).resolve().parent / "app_manager.py"
        command = shlex.join([sys.executable, str(backend), action, spec.key])
        shell = (
            f"{command}; status=$?; "
            "printf '\\n\\n--- Művelet befejezve (kilépési kód: %s) ---\\n' \"$status\"; "
            "printf 'Nyomj Entert az ablak bezárásához...'; "
            "read -r _; exit \"$status\""
        )
        process = QProcess(self)
        process.setProgram("konsole")
        process.setArguments(["--title", f"Across32 - {spec.title} - {action}",
                              "-e", "bash", "-c", shell])
        process.finished.connect(
            lambda code, _status, key=spec.key, label=spec.title:
            self.operation_finished(key, label, code)
        )
        process.errorOccurred.connect(
            lambda _error, key=spec.key: self.operation_error(key)
        )
        self.running[spec.key] = process
        process.start()
        self.refresh()

    def operation_error(self, key: str) -> None:
        process = self.running.pop(key, None)
        if process:
            QMessageBox.warning(self, "Konsole hiba",
                                f"A terminál nem indult el: {process.errorString()}")
        self.refresh()

    def operation_finished(self, key: str, label: str, code: int) -> None:
        self.running.pop(key, None)
        self.refresh()
        if code == 0:
            self.check_for_updates()
        if code != 0:
            QMessageBox.warning(self, "Sikertelen művelet",
                                f"{label}: a telepítés vagy frissítés nem sikerült. "
                                "A részletes hiba a Konsole ablakban látható.")

def main() -> int:
    if "--version" in sys.argv[1:]:
        print(title_text())
        print(f"Futtatási mappa: {Path(__file__).resolve().parent}")
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName("Across32 Launcher")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(STYLE)
    window = Launcher()
    if "--start-in-tray" in sys.argv[1:]:
        window.start_in_tray()
    else:
        window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
