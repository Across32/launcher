#!/usr/bin/env python3
"""KDE Plasma/EndeavourOS launcher for the six Across32 applications."""
from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import sys
import webbrowser

from PySide6.QtCore import Qt, QProcess, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app_manager import APPS, App, installed, open_application, repo_url, revision, source_dir, version


STYLE = """
QMainWindow, QWidget#root, QScrollArea, QWidget#gridWidget {
    background: #f5f5f3;
    color: #17181c;
}
QFrame#header {
    background: #ffffff;
    border-bottom: 1px solid #dadbdd;
}
QLabel#brand {
    color: #101114;
    font-size: 23px;
    font-weight: 900;
    letter-spacing: 1px;
}
QLabel#micro {
    color: #84868b;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
}
QLabel#summary {
    color: #70747a;
    font-size: 13px;
}
QFrame#card {
    background: #ffffff;
    border: 1px solid #d9dbdd;
    border-radius: 8px;
}
QLabel#appName {
    font-size: 21px;
    color: #101115;
    font-weight: 800;
}
QLabel#category {
    font-size: 12px;
    color: #70757b;
}
QLabel#description {
    font-size: 13px;
    color: #4d5259;
}
QLabel#status {
    font-size: 11px;
    font-weight: 700;
}
QLabel#version {
    color: #94969b;
    font-size: 11px;
}
QLineEdit, QComboBox {
    background: #fff;
    border: 1px solid #d2d3d5;
    border-radius: 4px;
    color: #252629;
    min-height: 33px;
    padding: 2px 9px;
}
QPushButton {
    border-radius: 4px;
    font-size: 12px;
    font-weight: 800;
    min-height: 33px;
    padding: 0px 12px;
}
QPushButton#primary {
    color: white;
    background: #15161a;
    border: 1px solid #15161a;
}
QPushButton#primary:hover { background: #383c45; }
QPushButton#secondary {
    color: #25272c;
    background: #f9f9fa;
    border: 1px solid #cfd0d3;
}
QPushButton#secondary:hover { background: #eaecef; }
QPushButton#secondary:disabled { color: #a3a6ac; background: #f2f3f4; }
QPushButton#link {
    background: transparent;
    border: 0;
    color: #62666b;
    font-size: 11px;
    letter-spacing: 1px;
}
QPushButton#link:hover { color: #246db8; }
QPushButton#refresh {
    color: #25282e;
    background: #fff;
    border: 1px solid #cfd0d3;
    font-size: 16px;
}
"""


class AppCard(QFrame):
    def __init__(self, spec: App, active: bool, busy: bool, parent: "Launcher"):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumWidth(310)
        self.setMinimumHeight(268)
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
        icon = QLabel(spec.letter)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(51, 51)
        icon.setStyleSheet(
            f"background:{spec.color};color:white;border-radius:11px;"
            "font-weight:900;font-size:27px;"
        )
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
        badge.setStyleSheet("color: #bc813b;" if busy else
                            ("color: #278068;" if active else "color: #777b81;"))
        outer.addWidget(badge)

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


class Launcher(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Across32 – Alkalmazáskezelő")
        self.setMinimumSize(940, 640)
        self.resize(1280, 795)
        self.running: dict[str, QProcess] = {}

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
        subtitle = QLabel("CRAFT APP SUITE  /  ENDEAVOUROS")
        subtitle.setObjectName("micro")
        head.addWidget(subtitle)
        head.addStretch()
        refresh = QPushButton("↻")
        refresh.setObjectName("refresh")
        refresh.setFixedSize(40, 36)
        refresh.setToolTip("Telepített alkalmazások újraellenőrzése")
        refresh.clicked.connect(self.refresh)
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
        self.footer.setObjectName("summary")
        self.footer.setContentsMargins(24, 10, 16, 12)
        layout.addWidget(self.footer)
        self.timer = QTimer(self)
        self.timer.setInterval(3500)
        self.timer.timeout.connect(self.refresh_if_running)
        self.timer.start()
        self.refresh()

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
            card = AppCard(spec, state[spec.key], spec.key in self.running, self)
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
        if code != 0:
            QMessageBox.warning(self, "Sikertelen művelet",
                                f"{label}: a telepítés vagy frissítés nem sikerült. "
                                "A részletes hiba a Konsole ablakban látható.")

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Across32 Launcher")
    app.setStyleSheet(STYLE)
    window = Launcher()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
