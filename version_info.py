"""Version shown by the running Across32 Launcher, not by a cached desktop entry."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess


APP_ROOT = Path(__file__).resolve().parent
VERSION_FILE = APP_ROOT / "VERSION"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-.][A-Za-z0-9.]+)?$")


def launcher_version() -> str:
    try:
        raw = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "ismeretlen"
    return "v" + raw if VERSION_RE.fullmatch(raw) else "ismeretlen"


def git_revision() -> str:
    """Read the real checkout SHA, if there is a local Git working tree."""
    if not (APP_ROOT / ".git").exists():
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", str(APP_ROOT), "rev-parse", "--short=8", "HEAD"],
            capture_output=True, text=True, timeout=3, check=True,
        )
        return result.stdout.strip() if re.fullmatch(r"[0-9a-f]{7,16}", result.stdout.strip()) else ""
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""


def build_label() -> str:
    version = launcher_version()
    rev = git_revision()
    return f"{version} · Git {rev}" if rev else version


def title_text() -> str:
    return f"Across32 – Alkalmazáskezelő | {build_label()}"
