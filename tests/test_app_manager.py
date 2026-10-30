"""Offline behavior checks; never clone or install a real application."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import app_manager as m


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {"XDG_DATA_HOME": str(self.home)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_eight_repo_keys(self):
        self.assertEqual(
            [app.key for app in m.APPS],
            ["relief", "Movie_database", "Munkak_eladasok", "laser", "tankolas", "gas", "player", "csomagkezelo"],
        )

    def test_git_origin_allowlist(self):
        app = m.BY_KEY["tankolas"]
        self.assertTrue(m.same_remote("https://github.com/Across32/tankolas.git", app))
        self.assertTrue(m.same_remote("git@github.com:Across32/tankolas.git", app))
        self.assertFalse(m.same_remote("https://github.com/Other/tankolas.git", app))
        self.assertFalse(m.same_remote("https://github.com/Across32/tankolas-malware.git", app))

    def test_clean_new_munkak_location(self):
        self.assertEqual(
            m.source_dir(m.BY_KEY["Munkak_eladasok"]),
            self.home / "cnc-eladasok",
        )

    def test_occupied_checkout_is_not_overwritten(self):
        app = m.BY_KEY["relief"]
        occupied = m.managed_dir() / app.key
        occupied.mkdir(parents=True)
        keep = occupied / "important.txt"
        keep.write_text("preserve", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            m.ensure_source(app, "install")
        self.assertEqual(keep.read_text(encoding="utf-8"), "preserve")

    def test_desktop_parse_and_detect(self):
        app = m.BY_KEY["laser"]
        destination = m.applications_dir()
        destination.mkdir(parents=True)
        desktop = destination / "laser-studio.desktop"
        desktop.write_text(
            "[Desktop Entry]\nType=Application\n"
            f"Exec={sys.executable} /tmp/example.py %F\n"
            "Path=/tmp\n",
            encoding="utf-8",
        )
        argv, cwd = m.desktop_command(desktop)
        self.assertEqual(argv, [sys.executable, "/tmp/example.py"])
        self.assertEqual(cwd, Path("/tmp"))
        self.assertTrue(m.installed(app))

    def test_version_regex(self):
        app = m.BY_KEY["relief"]
        root = m.managed_dir() / app.key
        root.mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            '[project]\nversion = "0.8.45"\n', encoding="utf-8"
        )
        self.assertEqual(m.version(app), "0.8.45")

    def test_munkak_version_from_actual_kde_installed_copy(self):
        app = m.BY_KEY["Munkak_eladasok"]
        # Installer copies main.py from its Git clone into a separate installed
        # directory. Never show the old Git checkout version for the running app.
        checkout = m.managed_dir() / app.key
        checkout.mkdir(parents=True)
        (checkout / "main.py").write_text('UI_VERSION = "2026.10.20-90"\n')
        installed_root = self.home / "installed Munkak"
        installed_root.mkdir()
        (installed_root / "main.py").write_text('UI_VERSION = "2026.10.24-95"\n')
        launcher = installed_root / "run.sh"
        launcher.write_text("#!/bin/sh\n")
        launcher.chmod(0o755)
        desktop = m.applications_dir() / "cnc-eladasok-v14.desktop"
        desktop.parent.mkdir(parents=True, exist_ok=True)
        desktop.write_text(
            "[Desktop Entry]\nType=Application\n"
            'Exec="' + str(launcher) + '"\n',
            encoding="utf-8",
        )
        self.assertEqual(m.installed_munkak_dir(app), installed_root)
        self.assertEqual(m.version(app), "2026.10.24-95")

    def test_munkak_version_from_checkout_when_no_kde_copy(self):
        app = m.BY_KEY["Munkak_eladasok"]
        clone = m.managed_dir() / app.key
        clone.mkdir(parents=True)
        (clone / "main.py").write_text('UI_VERSION = "2026.10.24-95"\n')
        self.assertEqual(m.version(app), "2026.10.24-95")

    def test_missing_app_is_not_installed(self):
        with patch.object(m, "working_desktop", return_value=None):
            self.assertFalse(m.installed(m.BY_KEY["gas"]))

    def test_player_repository_and_kde_metadata(self):
        app = m.BY_KEY["player"]
        self.assertEqual(app.desktop_pattern, "across-player.desktop")
        self.assertEqual(app.version_file, "player.py")
        self.assertEqual(m.repo_url(app), "https://github.com/Across32/player.git")
        self.assertTrue(m.same_remote("git@github.com:Across32/player.git", app))
        self.assertFalse(m.same_remote("https://github.com/not-Across32/player.git", app))

    def test_player_recognizes_documented_clone_directory(self):
        app = m.BY_KEY["player"]
        directory = self.home / ".local/share/across-player"
        directory.mkdir(parents=True)
        with patch.object(m.Path, "home", return_value=self.home):
            self.assertEqual(m.source_dir(app), directory)

    def test_player_recovers_git_repo_from_system_wrapper(self):
        app = m.BY_KEY["player"]
        repo = self.home / "media source with spaces" / "player"
        repo.mkdir(parents=True)
        (repo / ".git").mkdir()
        exe = self.home / ".local/bin/across-player"
        exe.parent.mkdir(parents=True)
        exe.write_text(
            "#!/usr/bin/env bash\n"
            "exec /usr/bin/python " + __import__("shlex").quote(str(repo / "player.py")) + ' "$@"\n',
            encoding="utf-8",
        )
        exe.chmod(0o755)
        desktop = m.applications_dir() / "across-player.desktop"
        desktop.parent.mkdir(parents=True)
        desktop.write_text("[Desktop Entry]\nType=Application\nExec=" + str(exe) + " %f\n", encoding="utf-8")
        with patch.object(m, "valid_checkout", side_effect=lambda candidate, _app: candidate == repo):
            self.assertEqual(m.root_from_desktop(app), repo)

    def test_player_ready_without_virtual_environment(self):
        app = m.BY_KEY["player"]
        directory = self.home / ".local/share/across-player"
        directory.mkdir(parents=True)
        (directory / "player.py").write_text("# source", encoding="utf-8")
        wrapper = self.home / ".local/bin/across-player"
        wrapper.parent.mkdir(parents=True)
        wrapper.write_text("#!/bin/sh\n", encoding="utf-8")
        wrapper.chmod(0o755)
        with patch.object(m.Path, "home", return_value=self.home):
            self.assertTrue(m.is_ready(app, directory))
            self.assertTrue(m.installed(app))
            self.assertEqual(m.version(app), "—")

    def test_player_install_only_missing_system_packages(self):
        app = m.BY_KEY["player"]
        clone = self.home / "repo"
        clone.mkdir()
        (clone / "install.sh").write_text("#!/bin/bash\n", encoding="utf-8")

        def probe(args, **kwargs):
            if args[:2] == ["pacman", "-Qq"]:
                return __import__("subprocess").CompletedProcess(
                    args, 1 if args[2] in ("pyside6", "xorg-xwayland") else 0
                )
            return __import__("subprocess").CompletedProcess(args, 1)

        with patch.object(m, "ensure_source", return_value=clone), \
             patch.object(m, "installed", return_value=True), \
             patch.object(m.shutil, "which", return_value="/usr/bin/fake"), \
             patch.object(m.subprocess, "run", side_effect=probe), \
             patch.object(m, "run_command") as execute:
            m.install_or_update(app, "install")
        execute.assert_any_call(
            "sudo", "pacman", "-S", "--needed", "pyside6", "xorg-xwayland"
        )
        execute.assert_any_call("bash", str(clone / "install.sh"), cwd=clone)

    def test_csomagkezelo_repository_and_kde_launcher(self):
        app = m.BY_KEY["csomagkezelo"]
        self.assertEqual(app.desktop_pattern, "csomagkezelo.desktop")
        self.assertEqual(app.version_file, "csomagkezelo/__init__.py")
        self.assertEqual(m.repo_url(app), "https://github.com/Across32/csomagkezelo.git")
        self.assertTrue(m.same_remote("git@github.com:Across32/csomagkezelo.git", app))
        self.assertFalse(m.same_remote("https://github.com/other/csomagkezelo.git", app))

    def test_csomagkezelo_version_from_python_init(self):
        app = m.BY_KEY["csomagkezelo"]
        source = m.managed_dir() / app.key
        init = source / app.version_file
        init.parent.mkdir(parents=True)
        init.write_text('"""Package app."""\n__version__ = "0.1.0"\n', encoding="utf-8")
        self.assertEqual(m.version(app), "0.1.0")

    def test_csomagkezelo_existing_kde_desktop_recovers_checkout(self):
        app = m.BY_KEY["csomagkezelo"]
        clone = self.home / "source code" / "csomagkezelo"
        clone.mkdir(parents=True)
        (clone / ".git").mkdir()
        (clone / "main.py").write_text("# app", encoding="utf-8")
        desktop = m.applications_dir() / "csomagkezelo.desktop"
        desktop.parent.mkdir(parents=True)
        desktop.write_text(
            "[Desktop Entry]\nType=Application\n"
            "Exec=" + sys.executable + " " + __import__("shlex").quote(str(clone / "main.py")) + "\n",
            encoding="utf-8",
        )
        with patch.object(m, "valid_checkout", side_effect=lambda path, _spec: path == clone):
            self.assertEqual(m.root_from_desktop(app), clone)
            self.assertTrue(m.installed(app))

    def test_csomagkezelo_user_checkout_is_reused(self):
        app = m.BY_KEY["csomagkezelo"]
        clone = self.home / "csomagkezelo"
        clone.mkdir()
        with patch.object(m.Path, "home", return_value=self.home), \
             patch.object(m, "valid_checkout", side_effect=lambda path, _spec: path == clone):
            self.assertEqual(m.source_dir(app), clone)

    def test_csomagkezelo_install_uses_its_existing_installer(self):
        app = m.BY_KEY["csomagkezelo"]
        clone = self.home / "source"
        clone.mkdir()
        (clone / "install.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        with patch.object(m, "ensure_source", return_value=clone), \
             patch.object(m, "installed", return_value=True), \
             patch.object(m.shutil, "which", return_value="/usr/bin/git"), \
             patch.object(m, "run_command") as execute:
            m.install_or_update(app, "install")
        execute.assert_called_once_with("bash", str(clone / "install.sh"), cwd=clone)

    def test_github_url(self):
        self.assertEqual(
            m.repo_url(m.BY_KEY["Movie_database"]),
            "https://github.com/Across32/Movie_database.git",
        )


if __name__ == "__main__":
    unittest.main()
