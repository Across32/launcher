"""Offline regression tests for KDE login autostart without opening a window."""
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

import autostart


class KDEAutostartTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)
        self.patch_home = patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.base)})
        self.patch_home.start()
        self.addCleanup(self.patch_home.stop)
        self.root = self.base / "launcher with spaces"
        self.root.mkdir()
        self.script = self.root / "run.sh"
        self.script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")

    def test_autostart_is_opt_in_and_persists(self):
        self.assertFalse(autostart.enabled())
        autostart.set_enabled(True, self.script)
        self.assertTrue(autostart.enabled())
        content = autostart.autostart_path().read_text(encoding="utf-8")
        self.assertIn('--start-in-tray', content)
        self.assertIn(f'Exec="{self.script}" --start-in-tray', content)
        self.assertIn('StartupNotify=false', content)
        autostart.set_enabled(False, self.script)
        self.assertFalse(autostart.enabled())
        self.assertFalse(autostart.autostart_path().exists())

    def test_existing_kde_autostart_is_migrated_without_duplicates(self):
        path = autostart.autostart_path()
        path.parent.mkdir(parents=True)
        path.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Across32 – Alkalmazáskezelő\n"
            "Exec=/home/old/launcher/run.sh\n",
            encoding="utf-8",
        )
        self.assertTrue(autostart.repair_existing(self.script))
        self.assertTrue(autostart.enabled())
        self.assertIn("--start-in-tray", path.read_text(encoding="utf-8"))
        self.assertEqual(len(list(path.parent.glob("*.desktop"))), 1)

    def test_no_new_kde_autostart_without_prior_opt_in(self):
        self.assertFalse(autostart.repair_existing(self.script))
        self.assertFalse(autostart.autostart_path().exists())

    def test_disabled_kde_entry_stays_disabled_after_install(self):
        path = autostart.autostart_path()
        path.parent.mkdir(parents=True)
        disabled = ("[Desktop Entry]\n"
                    "Name=Across32 – Alkalmazáskezelő\n"
                    "Exec=/old/run.sh\nHidden=true\n")
        path.write_text(disabled, encoding="utf-8")
        self.assertFalse(autostart.enabled())
        self.assertFalse(autostart.repair_existing(self.script))
        self.assertEqual(path.read_text(encoding="utf-8"), disabled)

    def test_unrelated_existing_desktop_entry_is_preserved(self):
        path = autostart.autostart_path()
        path.parent.mkdir(parents=True)
        existing = "[Desktop Entry]\nName=Some unrelated app\nExec=/opt/unrelated\n"
        path.write_text(existing, encoding="utf-8")
        with self.assertRaises(RuntimeError):
            autostart.set_enabled(True, self.script)
        self.assertEqual(path.read_text(encoding="utf-8"), existing)

    def test_directory_and_executable_field_code_escaping(self):
        folder = self.base / 'launcher "special" 100% $'
        folder.mkdir()
        script = folder / "run.sh"
        script.write_text("#!/bin/sh\n", encoding="utf-8")
        desktop = autostart.desktop_file(script)
        self.assertIn(" --start-in-tray", desktop)
        self.assertIn("100%%", desktop)
        self.assertIn('\\"special\\"', desktop)
        self.assertIn("\\$", desktop)


if __name__ == "__main__":
    unittest.main()
