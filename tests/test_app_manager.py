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

    def test_six_repo_keys(self):
        self.assertEqual(
            [app.key for app in m.APPS],
            ["relief", "Movie_database", "Munkak_eladasok", "laser", "tankolas", "gas"],
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

    def test_missing_app_is_not_installed(self):
        with patch.object(m, "working_desktop", return_value=None):
            self.assertFalse(m.installed(m.BY_KEY["gas"]))

    def test_github_url(self):
        self.assertEqual(
            m.repo_url(m.BY_KEY["Movie_database"]),
            "https://github.com/Across32/Movie_database.git",
        )


if __name__ == "__main__":
    unittest.main()
