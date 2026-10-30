"""Tests for the actual running Launcher build/version identification."""
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import version_info


class LauncherVersionTests(unittest.TestCase):
    def test_version_is_named_release_from_repo_version_file(self):
        self.assertEqual(version_info.launcher_version(), "v1.4.0")

    def test_version_invalid_never_displays_untrusted_content(self):
        with patch.object(version_info.VERSION_FILE.__class__, "read_text", return_value="bad (test)\n"):
            self.assertEqual(version_info.launcher_version(), "ismeretlen")

    def test_title_bar_includes_version_and_build_revision(self):
        with patch.object(version_info, "git_revision", return_value="89abcdef"):
            text = version_info.title_text()
        self.assertIn("Alkalmazáskezelő", text)
        self.assertIn("v1.4.0", text)
        self.assertIn("89abcdef", text)

    def test_git_unavailable_still_shows_release(self):
        with patch.object(version_info, "git_revision", return_value=""):
            self.assertEqual(version_info.build_label(), "v1.4.0")

    def test_launcher_version_cli_does_not_open_gui(self):
        repo = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [__import__("sys").executable, str(repo / "launcher.py"), "--version"],
            capture_output=True, text=True, timeout=12, check=True,
        )
        self.assertIn("v1.4.0", result.stdout)
        self.assertIn("Futtatási mappa:", result.stdout)


if __name__ == "__main__":
    unittest.main()
