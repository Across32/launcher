"""Responsive Launcher layout checks for eight visible cards without scrolling."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("ACROSS32_DISABLE_UPDATE_CHECK", "1")

from PySide6.QtWidgets import QApplication, QPushButton
from launcher import AppCard, Launcher, responsive_columns
from app_manager import APPS


class CompactLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        with patch("launcher.installed", return_value=True), \
             patch("launcher.version", return_value="1.0.0"), \
             patch("launcher.revision", return_value="12345678"):
            self.window = Launcher()
        self.addCleanup(self.window.close)

    def test_four_columns_show_eight_apps_in_two_rows_without_scroll(self):
        with patch("launcher.installed", return_value=True), \
             patch("launcher.version", return_value="1.0.0"), \
             patch("launcher.revision", return_value="12345678"):
            self.window.resize(1450, 870)
            self.window.show()
            self.app.processEvents()
            self.window.refresh()
            self.app.processEvents()
            self.assertEqual(self.window._columns, 4)
            self.assertEqual(self.window.grid.count(), len(APPS))
            self.assertIsNotNone(self.window.grid.itemAtPosition(1, 3))
            self.assertEqual(self.window.scroll.verticalScrollBar().maximum(), 0)

    def test_card_dimensions_are_compact_and_actions_remain(self):
        self.assertEqual(responsive_columns(1450), 4)
        self.assertEqual(responsive_columns(1050), 3)
        self.assertEqual(responsive_columns(820), 2)
        self.assertEqual(responsive_columns(1120), 4)
        with patch("launcher.version", return_value="1.0.0"), \
             patch("launcher.revision", return_value="12345678"):
            card = AppCard(APPS[0], True, False, self.window)
        self.addCleanup(card.close)
        self.assertLessEqual(card.maximumHeight(), 260)
        self.assertLessEqual(card.minimumWidth(), 255)
        self.assertEqual(len(card.findChildren(QPushButton, "history")), 1)
        self.assertEqual(len(card.findChildren(QPushButton, "primary")), 1)
        self.assertEqual(len(card.findChildren(QPushButton, "secondary")), 1)

    def test_resize_to_narrow_screen_keeps_scroll_fallback(self):
        with patch("launcher.installed", return_value=True), \
             patch("launcher.version", return_value="1.0.0"), \
             patch("launcher.revision", return_value="12345678"):
            self.window.resize(1040, 760)
            self.window.show()
            self.app.processEvents()
            self.window.refresh()
            self.assertEqual(self.window._columns, 3)
            self.assertEqual(self.window.grid.count(), len(APPS))
            self.window.resize(840, 680)
            self.app.processEvents()
            self.window.refresh()
            self.assertEqual(self.window._columns, 2)
            self.assertEqual(self.window.grid.count(), len(APPS))


if __name__ == "__main__":
    unittest.main()
