#!/usr/bin/env python3
"""Back up Across32's PRIVATE GitHub repositories: verified mirror + Git bundle.

Every repository is replaced only after BOTH the mirror clone and bundle pass.
Existing successful copies are never destroyed before the replacement is valid.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

BACKUP_ROOT = Path("/Volumes/Data/Github backup")
OWNER = "Across32"
SAFE_REPO = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


def command(*args: str, timeout: int | None = None, capture: bool = False) -> str:
    print("+ " + " ".join(args), flush=True)
    proc = subprocess.run(
        args, check=True, timeout=timeout,
        stdout=subprocess.PIPE if capture else None,
        text=True if capture else False,
    )
    return proc.stdout if capture else ""


def private_repositories() -> list[str]:
    if not shutil.which("gh"):
        raise RuntimeError("Hiányzik a GitHub CLI. Telepítsd: sudo pacman -S github-cli")
    if not shutil.which("git"):
        raise RuntimeError("Hiányzik a Git. Telepítsd: sudo pacman -S git")
    try:
        command("gh", "auth", "status", "--hostname", "github.com", timeout=20)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise RuntimeError("GitHub-belépés szükséges: gh auth login")
    output = command(
        "gh", "repo", "list", OWNER, "--visibility", "private", "--limit", "1000",
        "--json", "nameWithOwner,isPrivate", timeout=35, capture=True,
    )
    data = json.loads(output)
    if not isinstance(data, list):
        raise RuntimeError("A GitHub nem küldött érvényes repólistát.")
    repos = []
    for item in data:
        if item.get("isPrivate") is not True:
            continue
        full = item.get("nameWithOwner", "")
        owner, separator, repo = full.partition("/")
        if not separator or owner != OWNER or not SAFE_REPO.fullmatch(repo):
            raise RuntimeError(f"Nem támogatott repónév: {full}")
        repos.append(repo)
    if len(repos) != len(set(repos)):
        raise RuntimeError("A lekért GitHub-listában ismétlődő repónév szerepel.")
    if not repos:
        raise RuntimeError(
            "Nem található elérhető privát Across32 repó. "
            "A mentés nem módosított semmit."
        )
    return sorted(repos, key=str.casefold)


def ensure_directory() -> None:
    if not BACKUP_ROOT.parent.is_dir():
        raise RuntimeError(
            "/Volumes/Data nincs csatolva. Csatold az adatlemezt; "
            "nem hozok létre véletlenül új mentési mappát a rendszerlemezen."
        )
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    if not os.access(BACKUP_ROOT, os.W_OK):
        raise RuntimeError(f"A mentési könyvtár nem írható: {BACKUP_ROOT}")


def names(repo: str) -> tuple[Path, Path]:
    if not SAFE_REPO.fullmatch(repo):
        raise ValueError("Érvénytelen repónév.")
    stem = f"{OWNER}__{repo}"
    return BACKUP_ROOT / (stem + ".git"), BACKUP_ROOT / (stem + ".bundle")


def backup_one(repo: str) -> dict:
    """One repo is updated transactionally as two fixed-name artifacts."""
    mirror, bundle = names(repo)
    # Workspace on the same filesystem: os.replace is atomic for each component.
    with tempfile.TemporaryDirectory(prefix=".across32-stage-", dir=BACKUP_ROOT) as temp:
        work = Path(temp)
        new_mirror = work / "new.git"
        new_bundle = work / "new.bundle"
        old_mirror = work / "old.git"
        old_bundle = work / "old.bundle"
        print(f"\n========== {OWNER}/{repo} ==========", flush=True)
        origin = f"https://github.com/{OWNER}/{repo}.git"
        # Scoped, non-persistent Git credential helper. Never write the token to files.
        command(
            "git", "-c", "credential.helper=!gh auth git-credential",
            "clone", "--mirror", origin, str(new_mirror),
        )
        command("git", "--git-dir", str(new_mirror), "fsck", "--no-reflogs")
        command("git", "--git-dir", str(new_mirror), "bundle", "create", str(new_bundle), "--all")
        command("git", "--git-dir", str(new_mirror), "bundle", "verify", str(new_bundle))
        if new_bundle.stat().st_size == 0:
            raise RuntimeError("A bundle üres; a korábbi mentés megmaradt.")
        sha = command("git", "--git-dir", str(new_mirror), "rev-parse", "HEAD",
                      capture=True).strip()
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
            raise RuntimeError("A Git HEAD azonosító hibás.")
        # Rename old files into the stage directory only after BOTH new pieces pass.
        moved_old_mirror = moved_old_bundle = False
        installed_new_mirror = installed_new_bundle = False
        try:
            if mirror.exists():
                os.replace(mirror, old_mirror)
                moved_old_mirror = True
            if bundle.exists():
                os.replace(bundle, old_bundle)
                moved_old_bundle = True
            os.replace(new_mirror, mirror)
            installed_new_mirror = True
            os.replace(new_bundle, bundle)
            installed_new_bundle = True
        except Exception:
            # A copy or replacement failed: restore previous pair.
            if installed_new_mirror:
                shutil.rmtree(mirror)
            if installed_new_bundle:
                bundle.unlink(missing_ok=True)
            if moved_old_mirror:
                os.replace(old_mirror, mirror)
            if moved_old_bundle:
                os.replace(old_bundle, bundle)
            raise
        print(f"SIKER: {repo}: {sha[:12]}", flush=True)
        return {
            "repo": f"{OWNER}/{repo}", "revision": sha,
            "mirror": mirror.name, "bundle": bundle.name,
            "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        }


def save_manifest(results: list[dict], failures: list[str]) -> None:
    target = BACKUP_ROOT / "backup-status.json"
    fd, temp = tempfile.mkstemp(prefix=".backup-status-", suffix=".json", dir=BACKUP_ROOT)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump({
                "owner": OWNER,
                "type": "private-only",
                "last_run_utc": datetime.now(timezone.utc).isoformat(),
                "success": results,
                "failed": failures,
            }, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.replace(temp, target)
    finally:
        Path(temp).unlink(missing_ok=True)


def main() -> int:
    print("Across32 GitHub Backup – csak a PRIVÁT repók", flush=True)
    print("Célmappa:", BACKUP_ROOT, flush=True)
    print("A korábbi sikeres mentéseket hiba esetén megtartom.", flush=True)
    try:
        repos = private_repositories()
        ensure_directory()
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"HIBA: {exc}", file=sys.stderr)
        return 1
    print(f"Talált privát repók: {len(repos)}", flush=True)
    good, failed = [], []
    for index, repo in enumerate(repos, 1):
        print(f"\n[{index}/{len(repos)}] {repo}", flush=True)
        try:
            good.append(backup_one(repo))
        except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired) as exc:
            failed.append(repo)
            print(f"HIBA: {repo}: {exc}", file=sys.stderr, flush=True)
            print("A meglévő sikeres mentés változatlan maradt.", flush=True)
    try:
        save_manifest(good, failed)
    except OSError as exc:
        print(f"FIGYELEM: A státuszfájl írása nem sikerült: {exc}", file=sys.stderr)
    print(f"\nÖSSZESÍTÉS: sikeres {len(good)} / {len(repos)}; sikertelen {len(failed)}", flush=True)
    print("A Git-tükrök és bundle fájlok mindig ugyanarra a fájlnévre kerülnek.", flush=True)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
