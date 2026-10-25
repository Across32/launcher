#!/usr/bin/env python3
"""Across32 Launcher – safe Git-based installer and local application discovery."""
from __future__ import annotations

import argparse
import configparser
from dataclasses import dataclass
from pathlib import Path
import os
import re
import shlex
import shutil
import subprocess
import sys


OWNER = "Across32"


@dataclass(frozen=True)
class App:
    key: str
    title: str
    description: str
    category: str
    letter: str
    color: str
    icon: str
    desktop_pattern: str
    version_file: str


APPS = (
    App("relief", "Relief Studio", "CNC domborművek, STL-modellek és 4 tengelyes megmunkálás.", "CNC / 3D", "R", "#327eaf", "applications-graphics", "relief-studio.desktop", "pyproject.toml"),
    App("Movie_database", "Filmadatbázis", "Filmek, sorozatok, szereplők, megjelenések és feliratok.", "Film / Média", "M", "#7d68ac", "applications-multimedia", "filmadatbazis.desktop", "VERSION"),
    App("Munkak_eladasok", "Munkák és eladások", "CNC- és gravírozott termékek, bevételek és elszámolás.", "Üzlet / Nyilvántartás", "E", "#c1873b", "office-chart-bar", "cnc-eladasok*.desktop", "main.py"),
    App("laser", "Laser Studio", "Lézergravírozás, képfeldolgozás és G-kód készítése.", "Lézer / CAM", "L", "#4b9a8b", "applications-graphics", "laser-studio.desktop", "laser_studio/core.py"),
    App("tankolas", "Tankolás", "Üzemanyag-fogyasztás, tankolások és szervizkiadások.", "Jármű / Költségek", "T", "#bb6866", "applications-utilities", "Tankolas.desktop", "VERSION"),
    App("gas", "Gázfogyasztás", "Gázóraállások, fogyasztás és költségek nyilvántartása.", "Otthon / Rezsi", "G", "#607fbd", "applications-utilities", "gas-tracker.desktop", "pyproject.toml"),
    App("player", "Across Player – Lejátszó", "Magyar nyelvű Full HD és 4K videólejátszó mpv-alapon, hangsáv- és feliratválasztással.", "Film / Lejátszó", "▶", "#527ca4", "applications-multimedia", "across-player.desktop", "player.py"),
)
BY_KEY = {app.key: app for app in APPS}


def data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))).expanduser()


def managed_dir() -> Path:
    return data_home() / "across32-launcher" / "sources"


def applications_dir() -> Path:
    return data_home() / "applications"


def repo_url(app: App) -> str:
    return f"https://github.com/{OWNER}/{app.key}.git"


def same_remote(remote: str, app: App) -> bool:
    """Only pull from our exact expected repository; never silently switch origin."""
    allowed = (
        repo_url(app),
        repo_url(app)[:-4],
        f"git@github.com:{OWNER}/{app.key}.git",
        f"git@github.com:{OWNER}/{app.key}",
        f"ssh://git@github.com/{OWNER}/{app.key}.git",
        f"ssh://git@github.com/{OWNER}/{app.key}",
    )
    return remote.strip() in allowed


def git_origin(folder: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(folder), "remote", "get-url", "origin"],
            text=True, capture_output=True, timeout=10, check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def valid_checkout(folder: Path, app: App) -> bool:
    return (folder / ".git").exists() and same_remote(git_origin(folder), app)


def desktop_entries(app: App) -> list[Path]:
    folder = applications_dir()
    entries = list(folder.glob(app.desktop_pattern)) if folder.is_dir() else []
    if app.key == "Munkak_eladasok":
        entries += list(folder.glob("cnc_eladasok*.desktop")) if folder.is_dir() else []
    return sorted(set(entries), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)


def desktop_command(path: Path) -> tuple[list[str], Path | None]:
    """Parse trusted local desktop Exec WITHOUT involving a shell."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    entry = parser["Desktop Entry"]
    args = shlex.split(entry.get("Exec", ""))
    # Freedesktop field codes are argument placeholders, not shell syntax.
    args = [arg for arg in args if not re.fullmatch(r"%[fFuUdDnNickvm]", arg)]
    working = entry.get("Path", "").strip()
    return args, Path(working).expanduser() if working else None


def command_exists(argv: list[str]) -> bool:
    if not argv:
        return False
    command = argv[0]
    path = Path(command).expanduser()
    if path.is_absolute():
        return path.is_file() and os.access(path, os.X_OK)
    return bool(shutil.which(command) or (Path.home() / ".local/bin" / command).is_file())


def working_desktop(app: App) -> tuple[Path, list[str], Path | None] | None:
    for path in desktop_entries(app):
        try:
            args, cwd = desktop_command(path)
            if command_exists(args):
                return path, args, cwd
        except (OSError, ValueError, KeyError, configparser.Error):
            continue
    return None


def root_from_desktop(app: App) -> Path | None:
    entry = working_desktop(app)
    if not entry:
        return None
    _, argv, _ = entry
    # Find the original Git worktree from Exec /path/run.sh or /path/.venv/bin/python.
    for arg in argv:
        p = Path(arg).expanduser()
        if not p.is_absolute():
            continue
        for parent in (p.parent, *list(p.parents)[:5]):
            if valid_checkout(parent, app):
                return parent
    if app.key == "player":
        # Across Player's KDE desktop entry points to ~/.local/bin/across-player.
        # That wrapper contains the actual repo's player.py path, even if cloned
        # outside the project's usual ~/.local/share/across-player directory.
        for arg in argv:
            wrapper = Path(arg).expanduser()
            if wrapper.name != "across-player" or not wrapper.is_file():
                continue
            try:
                for line in wrapper.read_text(encoding="utf-8").splitlines():
                    words = shlex.split(line)
                    if len(words) >= 3 and words[:2] == ["exec", "/usr/bin/python"]:
                        source = Path(words[2]).expanduser()
                        if source.name == "player.py" and valid_checkout(source.parent, app):
                            return source.parent
            except (OSError, ValueError):
                continue
    return None


def source_dir(app: App) -> Path:
    external = root_from_desktop(app)
    if external:
        return external
    if app.key == "player":
        # The player's own documented clone destination. Do not create a second
        # installation when an existing checkout is already present.
        player_root = Path.home() / ".local/share/across-player"
        if player_root.exists():
            return player_root
    known = managed_dir() / app.key
    if known.exists():
        return known
    if app.key == "player":
        return Path.home() / ".local/share/across-player"
    if app.key == "Munkak_eladasok" and not working_desktop(app):
        # This repo's installer intentionally refuses a new, non-existing target.
        # A fresh clone at its historical default is itself a valid target.
        legacy_default = data_home() / "cnc-eladasok"
        if not legacy_default.exists():
            return legacy_default
        if valid_checkout(legacy_default, app):
            return legacy_default
    return known


def is_ready(app: App, folder: Path) -> bool:
    if app.key == "Movie_database":
        return ((data_home() / "filmadatbazis-app" / ".venv/bin/python").is_file()
                and (data_home() / "filmadatbazis-app" / "main.py").is_file())
    if app.key == "player":
        wrapper = Path.home() / ".local/bin/across-player"
        return ((folder / "player.py").is_file()
                and wrapper.is_file() and os.access(wrapper, os.X_OK))
    executable = ".venv/bin/gas-tracker" if app.key == "gas" else ".venv/bin/python"
    return (folder / executable).is_file()


def installed(app: App) -> bool:
    return bool(working_desktop(app)) or is_ready(app, source_dir(app))


def version(app: App) -> str:
    # The player project currently has no explicit VERSION/pyproject version.
    # Display its real local Git revision, not an invented release number.
    if app.key == "player":
        commit = revision(app)
        return f"Git {commit}" if commit else "—"
    folder = source_dir(app)
    candidate = folder / app.version_file
    if app.key == "Movie_database" and not candidate.exists():
        candidate = data_home() / "filmadatbazis-app" / "VERSION"
    try:
        raw = candidate.read_text(encoding="utf-8")
    except OSError:
        return "—"
    if app.key in ("Movie_database", "tankolas"):
        return raw.strip()[:24]
    if app.key in ("relief", "gas"):
        match = re.search(r"(?m)^version\s*=\s*['\"]([^'\"]+)['\"]", raw)
    elif app.key == "laser":
        match = re.search(r"(?m)^VERSION\s*=\s*['\"]([^'\"]+)['\"]", raw)
    else:
        match = re.search(r"(?m)^UI_VERSION\s*=\s*['\"]([^'\"]+)['\"]", raw)
    return match.group(1) if match else "—"


def revision(app: App) -> str:
    folder = source_dir(app)
    if not valid_checkout(folder, app):
        return ""
    try:
        return subprocess.run(
            ["git", "-C", str(folder), "rev-parse", "--short", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def open_application(app: App) -> None:
    desktop = working_desktop(app)
    if desktop:
        _, argv, cwd = desktop
    else:
        folder = source_dir(app)
        if not is_ready(app, folder):
            raise RuntimeError("A program nincs telepítve, vagy az indítója hiányzik.")
        script = "start.sh" if app.key == "relief" else "run.sh"
        if app.key == "tankolas":
            argv = [str(folder / ".venv/bin/python"), str(folder / "main.py")]
        elif app.key == "Movie_database":
            argv = [str(data_home() / "filmadatbazis-app/.venv/bin/python"),
                    str(data_home() / "filmadatbazis-app/main.py")]
        elif app.key == "player":
            argv = [str(Path.home() / ".local/bin/across-player")]
        else:
            argv = ["bash", str(folder / script)]
        cwd = folder
    cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "across32-launcher"
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / f"{app.key}.log").open("ab") as log:
        subprocess.Popen(argv, cwd=str(cwd) if cwd and cwd.is_dir() else None,
                         stdout=log, stderr=subprocess.STDOUT, start_new_session=True)


def run_command(*args: str, cwd: Path | None = None) -> None:
    print("+", shlex.join(args), flush=True)
    subprocess.run(args, cwd=str(cwd) if cwd else None, check=True)


def ensure_source(app: App, action: str) -> Path:
    folder = source_dir(app)
    if folder.exists():
        if not valid_checkout(folder, app):
            raise RuntimeError(
                f"A célkönyvtár létezik, de nem a megfelelő Git-klón:\n{folder}\n"
                "Nem módosítom és nem törlöm. Ellenőrizd kézzel."
            )
        # Never discard local changes and never use git reset --hard.
        changed = subprocess.run(
            ["git", "-C", str(folder), "status", "--porcelain", "--untracked-files=no"],
            check=True, capture_output=True, text=True,
        ).stdout
        if changed.strip():
            raise RuntimeError(
                f"Helyi módosítások vannak a forrásban: {folder}\n"
                "A frissítés leállt; semmi sem lett felülírva."
            )
        print(f"GitHub ellenőrzése: {app.title}", flush=True)
        run_command("git", "-C", str(folder), "pull", "--ff-only", "origin", "main")
    else:
        if action == "update" and not installed(app):
            raise RuntimeError("A program még nincs telepítve. Először a Telepítés gombot használd.")
        folder.parent.mkdir(parents=True, exist_ok=True)
        print(f"GitHub klónozás: {repo_url(app)}", flush=True)
        run_command("git", "clone", "--branch", "main", "--single-branch", repo_url(app), str(folder))
    return folder


def install_or_update(app: App, action: str) -> None:
    if not shutil.which("git"):
        raise RuntimeError("Hiányzik a Git. Telepítsd: sudo pacman -S git")
    if app.key in ("Munkak_eladasok", "tankolas", "gas") and not Path("/Volumes/Data").is_dir():
        raise RuntimeError(
            "A program az adatokat a /Volumes/Data mappában tárolja. "
            "A mappa hiányzik; csatold az adatmeghajtót, mielőtt telepítenéd."
        )
    folder = ensure_source(app, action)
    if app.key == "player":
        # The upstream installer requires system /usr/bin/python and pacman
        # packages, not a virtual environment. Verify every prerequisite,
        # including XWayland for embedded mpv video under KDE Wayland.
        if not shutil.which("pacman"):
            raise RuntimeError("Az Across Player EndeavourOS / Arch Linux rendszert igényel.")
        required = ("mpv", "pyside6", "qt6-base", "xorg-xwayland")
        missing = []
        for package in required:
            found = subprocess.run(
                ["pacman", "-Qq", package], capture_output=True,
                check=False, timeout=20,
            )
            if found.returncode != 0:
                missing.append(package)
        python = Path("/usr/bin/python")
        python_ok = python.is_file() and subprocess.run(
            [str(python), "-c", "import PySide6"],
            capture_output=True, check=False, timeout=20,
        ).returncode == 0
        if not python_ok and "pyside6" not in missing:
            raise RuntimeError(
                "A rendszerszintű Python nem tudja importálni a PySide6-ot. "
                "Ellenőrizd a pacman Python/PySide6 telepítését."
            )
        if missing:
            print("Across Player hiányzó rendszercsomagok: "
                  + ", ".join(missing), flush=True)
            run_command("sudo", "pacman", "-S", "--needed", *missing)
    script = "install_kde_menu.sh" if app.key == "Movie_database" else "install.sh"
    installer = folder / script
    if not installer.is_file():
        raise RuntimeError(f"Hiányzik a telepítő: {installer}")
    print("\nFüggőségek és KDE-indító beállítása...", flush=True)
    run_command("bash", str(installer), cwd=folder)
    if not installed(app):
        raise RuntimeError("A telepítő lefutott, de az alkalmazás nem található. Ellenőrizd a naplót.")
    print(f"\nSIKER: {app.title} – telepítve / frissítve.", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Across32 GitHub alkalmazáskezelő")
    parser.add_argument("action", choices=("install", "update", "status"))
    parser.add_argument("repo", choices=tuple(BY_KEY))
    args = parser.parse_args(argv)
    app = BY_KEY[args.repo]
    try:
        if args.action == "status":
            print(f"{app.title}: {'telepítve' if installed(app) else 'nincs telepítve'}")
            return 0
        install_or_update(app, args.action)
        return 0
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"\nHIBA: {exc}", file=sys.stderr, flush=True)
        print("Privát GitHub-repóhoz szükség lehet: gh auth login; gh auth setup-git",
              file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
