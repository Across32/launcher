"""Test history accuracy, persisted icons and no-loss Git mirror backups."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

import app_icons
import github_backup as backup
import release_history as history
from app_manager import BY_KEY


class NewFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

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

    def test_default_icon_uses_existing_kde_icon(self):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root)}):
            icon_file = self.root / "actual-app-icon.png"
            image = QImage(48, 48, QImage.Format.Format_ARGB32)
            image.fill(QColor("#6888ad"))
            self.assertTrue(image.save(str(icon_file), "PNG"))
            desktop = self.root / "applications"
            desktop.mkdir()
            (desktop / "laser-studio.desktop").write_text(
                "[Desktop Entry]\nType=Application\n"
                f"Icon={icon_file}\nExec=/usr/bin/python3\n",
                encoding="utf-8",
            )
            icon = app_icons.selected_icon(BY_KEY["laser"])
            self.assertFalse(icon.isNull())

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
            '{"nameWithOwner":"Across32/laser","isPrivate":true},'
            '{"nameWithOwner":"Across32/player","isPrivate":true},'
            '{"nameWithOwner":"Across32/csomagkezelo","isPrivate":true}]'
        )
        with patch.object(backup.shutil, "which", return_value="/usr/bin/gh"), \
             patch.object(backup, "command", side_effect=["", data]) as command:
            self.assertEqual(backup.private_repositories(), ["csomagkezelo", "laser", "player", "relief"])
            self.assertEqual(command.call_count, 2)  # No duplicate player lookup.

    def test_player_backup_is_added_when_private_repo_listing_omits_it(self):
        listing = ('[{"nameWithOwner":"Across32/laser","isPrivate":true},'
                   '{"nameWithOwner":"Across32/csomagkezelo","isPrivate":true}]')
        player = '{"nameWithOwner":"Across32/player","isPrivate":true}'
        with patch.object(backup.shutil, "which", return_value="/usr/bin/gh"), \
             patch.object(backup, "command", side_effect=["", listing, player]) as cmd:
            repos = backup.private_repositories()
        self.assertEqual(repos, ["csomagkezelo", "laser", "player"])
        self.assertEqual(cmd.call_args.args[:5],
                         ("gh", "repo", "view", "Across32/player", "--json"))

    def test_player_backup_rejects_unverified_public_or_inaccessible_repo(self):
        listing = ('[{"nameWithOwner":"Across32/laser","isPrivate":true},'
                   '{"nameWithOwner":"Across32/csomagkezelo","isPrivate":true}]')
        public = '{"nameWithOwner":"Across32/player","isPrivate":false}'
        with patch.object(backup.shutil, "which", return_value="/usr/bin/gh"), \
             patch.object(backup, "command", side_effect=["", listing, public]):
            with self.assertRaisesRegex(RuntimeError, "nem igazolható privát"):
                backup.private_repositories()

    def test_player_backup_has_one_stable_mirror_and_bundle_name(self):
        with patch.object(backup, "BACKUP_ROOT", self.root):
            mirror, bundle = backup.names("player")
        self.assertEqual(mirror, self.root / "Across32__player.git")
        self.assertEqual(bundle, self.root / "Across32__player.bundle")

    def test_csomagkezelo_is_retrieved_if_private_list_omits_it(self):
        listing = '[{"nameWithOwner":"Across32/player","isPrivate":true}]'
        package = '{"nameWithOwner":"Across32/csomagkezelo","isPrivate":true}'
        with patch.object(backup.shutil, "which", return_value="/usr/bin/gh"), \
             patch.object(backup, "command", side_effect=["", listing, package]) as cmd:
            self.assertEqual(backup.private_repositories(), ["csomagkezelo", "player"])
            self.assertEqual(cmd.call_args.args[:5],
                             ("gh", "repo", "view", "Across32/csomagkezelo", "--json"))

    def test_csomagkezelo_requires_verified_private_visibility(self):
        listing = '[{"nameWithOwner":"Across32/player","isPrivate":true}]'
        public = '{"nameWithOwner":"Across32/csomagkezelo","isPrivate":false}'
        with patch.object(backup.shutil, "which", return_value="/usr/bin/gh"), \
             patch.object(backup, "command", side_effect=["", listing, public]):
            with self.assertRaisesRegex(RuntimeError, "nem igazolható privát"):
                backup.private_repositories()

    def test_csomagkezelo_fixed_backup_paths_no_duplicate_files(self):
        with patch.object(backup, "BACKUP_ROOT", self.root):
            mirror, bundle = backup.names("csomagkezelo")
            self.assertEqual(mirror, self.root / "Across32__csomagkezelo.git")
            self.assertEqual(bundle, self.root / "Across32__csomagkezelo.bundle")

            def emulate(*argv, capture=False, timeout=None):
                if "clone" in argv:
                    Path(argv[-1]).mkdir()
                    (Path(argv[-1]) / "current").write_text("new", encoding="utf-8")
                if "bundle" in argv and "create" in argv:
                    Path(argv[argv.index("create") + 1]).write_bytes(b"BUNDLE")
                if "rev-parse" in argv:
                    return "1" * 40 + "\n"
                return ""

            with patch.object(backup, "command", side_effect=emulate):
                for _ in range(2):
                    backup.backup_one("csomagkezelo")
            self.assertEqual(len(list(self.root.glob("Across32__csomagkezelo.bundle"))), 1)
            self.assertEqual(len(list(self.root.glob("Across32__csomagkezelo.git"))), 1)
            self.assertEqual((mirror / "current").read_text(), "new")
            self.assertEqual(bundle.read_bytes(), b"BUNDLE")

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
