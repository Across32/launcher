"""Persist custom application-card images in the user's own data directory."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImageReader

from app_manager import App, data_home


def icons_dir() -> Path:
    return data_home() / "across32-launcher" / "icons"


def icon_path(app: App) -> Path:
    return icons_dir() / (app.key + ".png")


def save_icon(app: App, chosen_file: str) -> Path:
    source = Path(chosen_file).expanduser()
    if not source.is_file():
        raise ValueError("Nem található a kiválasztott képfájl.")
    if source.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Az ikonhoz legfeljebb 25 MB méretű kép választható.")
    reader = QImageReader(str(source))
    reader.setAutoTransform(True)
    if not reader.canRead():
        raise ValueError("A kiválasztott képformátum nem olvasható.")
    dimensions = reader.size()
    if dimensions.isValid() and (dimensions.width() > 12000 or dimensions.height() > 12000):
        raise ValueError("Az ikon képmérete túl nagy (maximum 12000 pixel oldalanként).")
    if dimensions.isValid():
        if dimensions.width() > 256 or dimensions.height() > 256:
            dimensions = dimensions.scaled(QSize(256, 256), Qt.AspectRatioMode.KeepAspectRatio)
            reader.setScaledSize(dimensions)
    image = reader.read()
    if image.isNull():
        raise ValueError("Nem sikerült feldolgozni a képet: " + reader.errorString())
    directory = icons_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = icon_path(app)
    fd, tmp = tempfile.mkstemp(prefix=".icon-", suffix=".png", dir=directory)
    os.close(fd)
    try:
        if not image.save(tmp, "PNG"):
            raise OSError("A PNG-ikon nem menthető.")
        os.replace(tmp, target)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return target


def delete_icon(app: App) -> None:
    icon_path(app).unlink(missing_ok=True)
