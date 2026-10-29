#!/usr/bin/env python3
"""Actual release history, preferably from Hungarian changelogs.

Never invent dates or version numbers: Git SHA is a genuine revision identifier
when no numbered release exists.
"""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app_manager import App, source_dir, valid_checkout

MAX_ENTRIES = 45
TIMEOUT = 18
RELEASE_RE = re.compile(r"(?m)^#{2,3}\s+(v?\d+(?:\.\d+){0,3})\b([^\n]*)")
DATE_RE = re.compile(r"\b(20\d\d[-.]\d\d[-.]\d\d)\b")
VERSION_IN_MESSAGE_RE = re.compile(r"(?i)(?:^|\s|:)(v?\d+\.\d+(?:\.\d+){0,2}|v\d{2,4})(?=\s|:|\b)")
FILE_VERSION_RE = re.compile(r'(?m)^\s*(?:version|VERSION|UI_VERSION|__version__)\s*=\s*["\']([^"\']+)')
CHANGELOG_PATHS = ("CHANGELOG.md", "docs/CHANGELOG.md", "CHANGES.md")


@dataclass(frozen=True)
class Update:
    date: str
    version: str
    title: str
    description: str
    revision: str = ""


def git(repo: Path, *args: str, timeout: int = TIMEOUT) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, check=True,
    ).stdout


def api_json(app: App, resource: str) -> object:
    endpoint = f"repos/Across32/{app.key}/{resource}"
    if shutil.which("gh"):
        try:
            result = subprocess.run(
                ["gh", "api", endpoint], capture_output=True, text=True,
                timeout=TIMEOUT, check=True,
            )
            return json.loads(result.stdout)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
    # Only public repositories work here when the CLI is not authenticated.
    url = "https://api.github.com/" + endpoint
    req = Request(url, headers={"Accept": "application/vnd.github+json",
                                "User-Agent": "Across32-Launcher"})
    with urlopen(req, timeout=TIMEOUT) as response:
        return json.load(response)


def commit_entries(app: App) -> list[tuple[str, str, str]]:
    """(sha, YYYY-MM-DD, exact original message); uses local clone first."""
    folder = source_dir(app)
    if valid_checkout(folder, app):
        try:
            output = git(
                folder, "log", "--first-parent", "-n", "180",
                "--format=%H%x1f%cs%x1f%s%x1e",
                timeout=20,
            )
            values = []
            for item in output.split("\x1e"):
                parts = item.strip().split("\x1f", 2)
                if len(parts) == 3:
                    values.append(tuple(parts))
            if values:
                return values
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
    data = api_json(app, "commits?per_page=100")
    if not isinstance(data, list):
        return []
    entries = []
    for item in data:
        commit = item.get("commit", {})
        date = (commit.get("committer", {}).get("date")
                or commit.get("author", {}).get("date") or "")[:10]
        text = str(commit.get("message") or "").split("\n", 1)[0]
        entries.append((item.get("sha", ""), date, text))
    return entries


def changelog_text(app: App) -> str:
    folder = source_dir(app)
    for path in CHANGELOG_PATHS:
        local = folder / path
        if local.is_file():
            try:
                return local.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
    for path in CHANGELOG_PATHS:
        try:
            data = api_json(app, "contents/" + path)
            if isinstance(data, dict) and data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", "replace")
        except (HTTPError, URLError, OSError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired, ValueError, KeyError):
            continue
    return ""


def normalized_version(text: str) -> str:
    return text.strip().lower().removeprefix("v")


def commit_version(app: App, sha: str) -> str:
    """Read the version written in the actual commit's source tree."""
    folder = source_dir(app)
    if not valid_checkout(folder, app):
        return ""
    try:
        raw = git(folder, "show", f"{sha}:{app.version_file}", timeout=6)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return ""
    if app.key in ("Movie_database", "tankolas"):
        return raw.strip()[:32]
    match = FILE_VERSION_RE.search(raw)
    return match.group(1) if match else ""


def brief_hungarian(message: str) -> str:
    """Conservative, Hungarian classification, no invented change details."""
    s = message.casefold()
    if re.search(r"(?:^|\s)(?:fix|repair|correct|bugfix|hotfix)(?:\s|:|$)", s):
        return "Hibajavítás, a program működésének pontosítása."
    if re.search(r"(?:^|\s)(?:test|tests|regression|audit|smoke)(?:\s|:|$)", s):
        return "Automatikus tesztek és működésellenőrzések bővítése."
    if re.search(r"(?:^|\s)(?:document|docs|readme)(?:\s|:|$)", s):
        return "Dokumentáció és használati útmutató frissítése."
    if "invoice" in s:
        return "Számlák kezelésével kapcsolatos fejlesztés."
    if "wood" in s or "warehouse" in s or "stock" in s:
        return "Faanyagok és raktárkészlet kezelésének fejlesztése."
    if "icon" in s:
        return "Ikonok és megjelenítési beállítások fejlesztése."
    if "release" in s or re.match(r"v?\d+(?:\.\d+)*:", s):
        return "Új kiadás, összegyűjtött fejlesztésekkel és javításokkal."
    if re.search(r"(?:^|\s)(?:add|implement|introduce|enable)(?:\s|:|$)", s):
        return "Új funkció beépítése a programba."
    if re.search(r"(?:^|\s)(?:update|improve|enhance|refactor)(?:\s|:|$)", s):
        return "Meglévő programfunkciók továbbfejlesztése."
    return "Fejlesztői módosítás a program GitHub-forráskódjában."


def find_date(version: str, commits: list[tuple[str, str, str]]) -> str:
    wanted = normalized_version(version)
    pattern = re.compile(r"(?i)(?<![\w.])v?" + re.escape(wanted) + r"(?![\w.])")
    for _sha, date, title in commits:
        if pattern.search(title):
            return date
    return ""


def changelog_updates(markdown: str, commits: list[tuple[str, str, str]]) -> list[Update]:
    matches = list(RELEASE_RE.finditer(markdown))
    results = []
    for i, match in enumerate(matches[:MAX_ENTRIES]):
        version = match.group(1).lstrip("vV")
        heading = match.group(2)
        chunk = markdown[match.end(): matches[i + 1].start() if i + 1 < len(matches) else len(markdown)]
        date_match = DATE_RE.search(heading)
        date = (date_match.group(1).replace(".", "-") if date_match else find_date(version, commits))
        bullets = []
        for raw in chunk.splitlines():
            cleaned = raw.strip()
            if cleaned.startswith(("- ", "* ")):
                cleaned = cleaned[2:].strip()
                cleaned = re.sub(r"\*\*|\x60", "", cleaned)
                if cleaned:
                    bullets.append(cleaned)
        summary = "\n".join("• " + item for item in bullets[:7])
        if not summary:
            summary = "A részletek a projekt változásnaplójában találhatók."
        results.append(Update(date or "Nincs megadva", f"v{version}",
                              f"Verzió: v{version}", summary[:2800]))
    return results


def git_updates(app: App, commits: list[tuple[str, str, str]]) -> list[Update]:
    results = []
    for sha, date, title in commits[:MAX_ENTRIES]:
        release = VERSION_IN_MESSAGE_RE.search(title)
        explicit = release.group(1) if release else ""
        checked = commit_version(app, sha)
        version = checked or explicit
        label = f"v{normalized_version(version)}" if version else f"Git {sha[:8]}"
        detail = brief_hungarian(title)
        # The original message is clearly identified, rather than falsely translated.
        detail += f"\nEredeti Git-bejegyzés: {title}"
        results.append(Update(date or "Nincs megadva", label,
                              brief_hungarian(title), detail, sha[:8]))
    return results


def load_history(app: App) -> tuple[list[Update], str]:
    """Fetch a real timeline; only trust dates or release versions from sources."""
    errors = []
    commits = []
    try:
        commits = commit_entries(app)
    except (HTTPError, URLError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        errors.append(str(exc))
    markdown = ""
    try:
        markdown = changelog_text(app)
    except (HTTPError, URLError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        errors.append(str(exc))
    if markdown:
        entries = changelog_updates(markdown, commits)
        if entries:
            return entries, "Magyar nyelvű CHANGELOG.md. A hiányzó dátumokat a Git-előzményekből keressük."
    if commits:
        return git_updates(app, commits), (
            "A projekt nem tartalmaz feldolgozható kiadási naplót. "
            "A lista valós Git-változásokat mutat magyar összefoglalóval, "
            "eredeti fejlesztői címmel, dátummal és valódi verzióval vagy Git-azonosítóval."
        )
    details = "; ".join(errors[:2])
    raise RuntimeError(
        "Nem sikerült betölteni a frissítési előzményeket. "
        "Ellenőrizd az internetkapcsolatot és privát repóknál a 'gh auth login' bejelentkezést."
        + (f"\nRészletek: {details}" if details else "")
    )


def main() -> int:
    import argparse
    from dataclasses import asdict
    import sys
    from app_manager import BY_KEY
    parser = argparse.ArgumentParser(description="Magyar GitHub frissítési előzmények")
    parser.add_argument("repo", choices=tuple(BY_KEY))
    args = parser.parse_args()
    try:
        entries, note = load_history(BY_KEY[args.repo])
        print(json.dumps({"items": [asdict(item) for item in entries], "note": note},
                         ensure_ascii=False))
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
