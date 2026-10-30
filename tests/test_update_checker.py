"""Offline unit tests: GitHub release comparison, caching and status persistence."""
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime

import update_checker as u
from app_manager import BY_KEY


class RemoteUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name) / "versions.json"

    def test_numeric_versions_not_lexicographic(self):
        self.assertTrue(u.newer_release("0.8.50", "0.8.9"))
        self.assertTrue(u.newer_release("v309", "v308"))
        self.assertTrue(u.newer_release("2026.10.25-96", "2026.10.24-95"))
        self.assertFalse(u.newer_release("0.8.9", "0.8.50"))
        self.assertFalse(u.newer_release("1.3.0", "1.3"))
        self.assertFalse(u.newer_release("1.3.0", "1.3.0"))
        self.assertFalse(u.newer_release("", "1.2.0"))
        self.assertFalse(u.newer_release("Git 1234", "Git abcd"))
        self.assertFalse(u.newer_release("unknown", "—"))

    def test_version_parser_supports_each_repo_type(self):
        from app_manager import parse_version_source
        self.assertEqual(parse_version_source(BY_KEY["Munkak_eladasok"],
                         'APP_NAME = "x"\nUI_VERSION = "2026.10.24-95"\n'), "2026.10.24-95")
        self.assertEqual(parse_version_source(BY_KEY["Movie_database"], "308\n"), "308")
        self.assertEqual(parse_version_source(BY_KEY["tankolas"], "1.0.4\n"), "1.0.4")
        self.assertEqual(parse_version_source(BY_KEY["laser"], 'VERSION = "0.8.50"\n'), "0.8.50")
        self.assertEqual(parse_version_source(BY_KEY["csomagkezelo"], '__version__ = "0.1.0"\n'), "0.1.0")
        self.assertEqual(parse_version_source(BY_KEY["relief"], '[project]\nversion = "0.8.45"\n'), "0.8.45")
        self.assertEqual(parse_version_source(BY_KEY["gas"], 'version = "0.1.0"\n'), "0.1.0")

    def test_fetched_private_repo_release_reads_original_version(self):
        payload = {
            "encoding": "base64",
            "content": base64.b64encode(b'UI_VERSION = "2026.10.25-96"\n').decode()
        }
        with patch.object(u, "api_json", return_value=payload) as api:
            latest = u.fetch_remote(BY_KEY["Munkak_eladasok"])
        self.assertEqual(latest["remote_version"], "2026.10.25-96")
        self.assertEqual(latest["remote_sha"], "")
        self.assertEqual(api.call_args.args[0],
                         "repos/Across32/Munkak_eladasok/contents/main.py?ref=main")

    def test_player_github_commit_fallback(self):
        sha = "a" * 40
        with patch.object(u, "api_json", return_value={"sha": sha}):
            self.assertEqual(u.fetch_remote(BY_KEY["player"])["remote_sha"], sha)
        with patch.object(u, "revision", return_value="b" * 7):
            self.assertTrue(u.update_available(BY_KEY["player"], "Git bbbbbbb",
                                               {"remote_version": "", "remote_sha": sha}))
        with patch.object(u, "revision", return_value="a" * 8):
            self.assertFalse(u.update_available(BY_KEY["player"], "Git aaaaaaaa",
                                                {"remote_version": "", "remote_sha": sha}))

    def test_persistent_warning_only_ends_when_new_version_installed(self):
        record = {"remote_version": "0.8.50", "remote_sha": ""}
        self.assertTrue(u.update_available(BY_KEY["laser"], "0.8.49", record))
        u.save_cache({"laser": record}, self.cache)
        loaded = u.read_cache(self.cache)
        self.assertEqual(loaded["laser"], record)
        self.assertTrue(u.update_available(BY_KEY["laser"], "0.8.49", loaded["laser"]))
        self.assertFalse(u.update_available(BY_KEY["laser"], "0.8.50", loaded["laser"]))
        self.assertFalse(u.update_available(BY_KEY["laser"], "0.8.51", loaded["laser"]))

    def test_failed_or_malformed_cache_is_not_treated_as_new_release(self):
        self.assertEqual(u.read_cache(self.cache), {})
        self.cache.write_text("bad json")
        self.assertEqual(u.read_cache(self.cache), {})
        u.save_cache({"laser": {"remote_version": "0.8.50", "remote_sha": ""}}, self.cache)
        self.assertEqual(oct(self.cache.stat().st_mode & 0o777), "0o600")
        self.assertFalse(u.update_available(BY_KEY["laser"], "0.8.48",
                          {"remote_version": "not-a-version", "remote_sha": ""}))

    def test_no_false_update_on_unknown_local_version(self):
        self.assertFalse(u.update_available(BY_KEY["Munkak_eladasok"], "—",
                             {"remote_version": "2026.10.25-96", "remote_sha": ""}))

    def test_no_remote_overwrite_if_private_github_unavailable(self):
        original = {"laser": {"remote_version": "0.8.50", "remote_sha": ""}}
        u.save_cache(original, self.cache)
        with patch.object(u, "read_cache", return_value=original), \
             patch.object(u, "fetch_remote", side_effect=RuntimeError("offline")), \
             patch.object(u, "save_cache") as save:
            import io
            from contextlib import redirect_stdout
            with redirect_stdout(io.StringIO()):
                self.assertEqual(u.scan(), 0)
        save.assert_not_called()
        self.assertEqual(u.read_cache(self.cache)["laser"], original["laser"])


if __name__ == "__main__":
    unittest.main()
