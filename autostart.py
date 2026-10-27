#!/usr/bin/env python3
"""KDE Plasma user autostart for Across32 Launcher.

Manual KDE application-menu launches open a window normally. The separate
~/.config/autostart desktop entry passes --start-in-tray, so KDE session
startup does not display the main window. No autostart is enabled by default.
"""
from __future__ import annotations

import argparse
import configparser
import os
from pathlib import Path
import tempfile


AUTOSTART_FILENAME = "across32-launcher.desktop"


def autostart_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return config_home.expanduser() / "autostart" / AUTOSTART_FILENAME


def entry_is_ours(path: Path) -> bool:
    if not path.is_file() or path.suffix.casefold() != ".desktop":
        return False
    try:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        parser.read(path, encoding="utf-8")
        entry = parser["Desktop Entry"]
        command = entry.get("Exec", "").casefold()
        name = entry.get("Name", "").casefold()
        desktop_id = path.stem.casefold()
        return (
            "across32-launcher" in command
            or "across32-launcher" in desktop_id
            or "launcher.py" in command
            or ("across32" in name and ("alkalmazáskezelő" in name or "launcher" in name))
        )
    except (OSError, KeyError, configparser.Error):
        return False


def matching_entries() -> list[Path]:
    """Find KDE-created autostarts even if KDE renamed the desktop file."""
    directory = autostart_path().parent
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.desktop") if entry_is_ours(path))


def entry_enabled(target: Path) -> bool:
    try:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.read(target, encoding="utf-8")
        entry = parser["Desktop Entry"]
        return (
            entry.get("Hidden", "false").casefold() != "true"
            and entry.get("X-GNOME-Autostart-enabled", "true").casefold() != "false"
        )
    except (OSError, KeyError, configparser.Error):
        return False


def enabled() -> bool:
    return any(entry_enabled(path) for path in matching_entries())


def escape_exec_path(path: Path) -> str:
    """Double-quoted freedesktop Exec token, with literal % encoded as %%."""
    value = str(path.resolve())
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    value = value.replace("$", "\\$").replace(chr(96), "\\" + chr(96))
    value = value.replace("%", "%%")
    return '"' + value + '"'


def desktop_file(run_script: Path) -> str:
    if not run_script.is_file():
        raise FileNotFoundError(f"Az indító nem található: {run_script}")
    parent = run_script.resolve().parent
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Version=1.0\n"
        "Name=Across32 – Alkalmazáskezelő (tálcán)\n"
        "Comment=Automatikus indítás KDE Plasma rendszertálcájára\n"
        f"Exec={escape_exec_path(run_script)} --start-in-tray\n"
        f"Path={parent}\n"
        f"Icon={parent / 'assets/across32-launcher.svg'}\n"
        "Terminal=false\n"
        "Categories=Utility;Development;\n"
        "X-GNOME-Autostart-enabled=true\n"
        "X-KDE-autostart-after=panel\n"
        "StartupNotify=false\n"
    )


def write_atomic(target: Path, contents: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(prefix=".across32-autostart-", suffix=".desktop",
                                    dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(contents)
        os.chmod(filename, 0o644)
        os.replace(filename, target)
    finally:
        Path(filename).unlink(missing_ok=True)


def set_enabled(enable: bool, run_script: Path) -> None:
    target = autostart_path()
    if target.exists() and not entry_is_ours(target):
        raise RuntimeError(
            "A meglévő automatikus indítási fájl nem az Across32 Launcherhez "
            "tartozik. Nem módosítom: " + str(target)
        )
    matches = matching_entries()
    if enable:
        contents = desktop_file(run_script)
        # Rewrite KDE's existing differently named autostart entry in place.
        # Never add a second active copy of the same launcher.
        destination = next((p for p in matches if entry_enabled(p)), None)
        if destination is None:
            destination = matches[0] if matches else target
        write_atomic(destination, contents)
        for duplicate in matches:
            if duplicate != destination:
                duplicate.unlink()
    else:
        for path in matches:
            path.unlink()


def repair_existing(run_script: Path) -> bool:
    """Migrate already enabled KDE autostarts, preserving disabled state."""
    matches = matching_entries()
    active = [p for p in matches if entry_enabled(p)]
    if not active:
        return False
    destination = active[0]
    write_atomic(destination, desktop_file(run_script))
    for duplicate in matches:
        if duplicate != destination:
            duplicate.unlink()
    return True


def main() -> int:
    args = argparse.ArgumentParser()
    args.add_argument("--repair", metavar="RUN_SH", type=Path, required=True)
    opts = args.parse_args()
    if repair_existing(opts.repair):
        print("KDE automatikus indítás: a Launcher ezentúl tálcára indul.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
