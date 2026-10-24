"""Test history accuracy, persisted icons and no-loss Git mirror backups."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QImage

import app_icons
import github_backup as backup
import release_history as history
from app_manager import BY_KEY


class NewFeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_hungarian_changelog_exact_version_and_date(self):
        markdown = (
            "# Fejlesztések\n"
            "## 0.8.45 – 2026-10-24\n"
            "- Javított vonalzó és koordinátarendszer.\n"
            "## 0.8.44 – 2026-10-23\n"
            "- Tesztnaplók az Asztalon.\n"
        )
        entries = history.changelog_updates(markdown, [])
        self.assertEqual([x.version for x in entries], ["v0.8.45", "v0.8.44"])
        self.assertEqual([x.date for x in entries], ["2026-10-24", "2026-10-23"])
        self.assertIn("Javított vonalzó", entries[0].description)

    def test_changelog_no_fake_date(self):
        entries = history.changelog_updates("## v306\n- Új naptár\n", [])
        self.assertEqual(entries[0].date, "Nincs megadva")

    def test_git_history_without_release_number_uses_real_sha(self):
        spec = BY_KEY["gas"]
        with patch.object(history, "commit_version", return_value=""):
            result = history.git_updates(
                spec, [("f" * 40, "2026-10-03", "Add monthly invoice detection")]
            )
        self.assertEqual(result[0].version, "Git ffffffff")
        self.assertEqual(result[0].date, "2026-10-03")
        self.assertIn("Számlák", result[0].description)

    def test_icon_persists_and_can_reset(self):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root)}):
            original = self.root / "sample.png"
            image = QImage(96, 96, QImage.Format.Format_ARGB32)
            image.fill(QColor("#50789a"))
            self.assertTrue(image.save(str(original), "PNG"))
            spec = BY_KEY["relief"]
            installed = app_icons.save_icon(spec, str(original))
            self.assertTrue(installed.exists())
            self.assertEqual(installed.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(app_icons.icon_path(spec), installed)
            app_icons.delete_icon(spec)
            self.assertFalse(installed.exists())

    def test_invalid_icon_does_not_replace_existing(self):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root)}):
            spec = BY_KEY["relief"]
            source = self.root / "good.png"
            image = QImage(32, 32, QImage.Format.Format_ARGB32)
            image.fill(QColor("blue"))
            self.assertTrue(image.save(str(source), "PNG"))
            old = app_icons.save_icon(spec, str(source)).read_bytes()
            bad = self.root / "bad.png"
            bad.write_text("not an image", encoding="utf-8")
            with self.assertRaises(ValueError):
                app_icons.save_icon(spec, str(bad))
            self.assertEqual(app_icons.icon_path(spec).read_bytes(), old)

    def test_private_repo_filter(self):
        data = (
            '[{"nameWithOwner":"Across32/relief","isPrivate":true},'
            '{"nameWithOwner":"Across32/public","isPrivate":false},'
            '{"nameWithOwner":"Across32/laser","isPrivate":true}]'
        )
        with patch.object(backup.shutil, "which", return_value="/usr/bin/gh"), \
             patch.object(backup, "command", side_effect=["", data]):
            self.assertEqual(backup.private_repositories(), ["laser", "relief"])

    def test_one_good_backup_replaces_old_two_fixed_names(self):
        with patch.object(backup, "BACKUP_ROOT", self.root):
            mirror, bundle = backup.names("gas")
            mirror.mkdir()
            (mirror / "revision").write_text("OLD", encoding="utf-8")
            bundle.write_text("OLD BUNDLE", encoding="utf-8")

            def emulate(*argv, capture=False, timeout=None):
                if "clone" in argv:
                    new = Path(argv[-1])
                    new.mkdir()
                    (new / "revision").write_text("NEW", encoding="utf-8")
                if "bundle" in argv and "create" in argv:
                    Path(argv[argv.index("create") + 1]).write_bytes(b"VALID BUNDLE")
                if "rev-parse" in argv:
                    return "a" * 40 + "\n"
                return ""

            with patch.object(backup, "command", side_effect=emulate):
                outcome = backup.backup_one("gas")
            self.assertEqual(outcome["revision"], "a" * 40)
            self.assertEqual((mirror / "revision").read_text(), "NEW")
            self.assertEqual(bundle.read_bytes(), b"VALID BUNDLE")
            self.assertEqual(len(list(self.root.glob("*bundle"))), 1)
            self.assertEqual(len(list(self.root.glob("*.git"))), 1)

    def test_failed_backup_preserves_prior_pair(self):
        with patch.object(backup, "BACKUP_ROOT", self.root):
            mirror, bundle = backup.names("relief")
            mirror.mkdir()
            (mirror / "revision").write_text("PRIOR", encoding="utf-8")
            bundle.write_text("PRIOR BUNDLE", encoding="utf-8")

            def failure(*argv, capture=False, timeout=None):
                if "clone" in argv:
                    Path(argv[-1]).mkdir()
                if "create" in argv:
                    Path(argv[argv.index("create") + 1]).write_bytes(b"BUNDLE")
                if "verify" in argv:
                    raise subprocess.CalledProcessError(1, argv)
                return ""
            with patch.object(backup, "command", side_effect=failure):
                with self.assertRaises(subprocess.CalledProcessError):
                    backup.backup_one("relief")
            self.assertEqual((mirror / "revision").read_text(), "PRIOR")
            self.assertEqual(bundle.read_text(), "PRIOR BUNDLE")


if __name__ == "__main__":
    unittest.main()
