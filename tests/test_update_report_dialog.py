"""Offscreen regression tests for readable GitHub update report dialog."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QPlainTextEdit, QPushButton

from launcher import UpdateReportDialog, Launcher


class UpdateReportDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_dark_background_has_explicit_light_text_and_scroll_view(self):
        dialog = UpdateReportDialog(
            "GitHub verzióellenőrzés – 8/8 repó\n\n"
            "Filmadatbázis: 315 → 316 (FRISSÍTÉS ELÉRHETŐ)"
        )
        self.addCleanup(dialog.close)
        self.assertEqual(dialog.objectName(), "updateReportDialog")
        self.assertTrue(dialog.report_text.isReadOnly())
        self.assertIsInstance(dialog.report_text, QPlainTextEdit)
        self.assertIn("8/8 repó", dialog.report_text.toPlainText())
        self.assertIn("FRISSÍTÉS ELÉRHETŐ", dialog.report_text.toPlainText())
        self.assertEqual(dialog.report_text.palette().color(QPalette.ColorRole.Text).name(), "#eef6ff")
        self.assertEqual(dialog.report_text.palette().color(QPalette.ColorRole.Base).name(), "#18283a")
        self.assertIn("QPlainTextEdit#updateReportText", dialog.styleSheet())
        self.assertIn("color: #eef6ff", dialog.styleSheet())
        self.assertGreaterEqual(dialog.minimumWidth(), 500)
        dialog.show()
        self.app.processEvents()
        self.assertTrue(dialog.report_text.isVisible())

    def test_error_heading_and_copy_report_button(self):
        message = "Laser Studio: 0.8.49 – HIBA: HTTP 401"
        dialog = UpdateReportDialog(message, has_errors=True)
        self.addCleanup(dialog.close)
        self.assertIn("hibával", dialog.heading.text())
        copy_button = dialog.findChild(QPushButton, "updateReportCopy")
        self.assertIsNotNone(copy_button)
        copy_button.click()
        self.assertEqual(QApplication.clipboard().text(), message)
        self.assertIsNotNone(dialog.findChild(QPushButton, "updateReportClose"))

    def test_manual_scan_uses_custom_dialog_not_unreadable_message_box(self):
        with patch.dict(os.environ, {"ACROSS32_DISABLE_UPDATE_CHECK": "1"}):
            window = Launcher()
        self.addCleanup(window.close)
        window._scan_results = {app.key: {"ok": True} for app in __import__("app_manager").APPS}
        window._manual_update_summary = True
        worker = __import__("PySide6.QtCore", fromlist=["QProcess"]).QProcess(window)
        worker.start("true", [])
        worker.waitForFinished(3000)
        window.update_process = worker
        with patch.object(UpdateReportDialog, "exec", return_value=0) as show, \
             patch("launcher.QMessageBox.information") as old_info, \
             patch("launcher.QMessageBox.warning") as old_warn:
            window.update_scan_finished(0, worker.exitStatus())
        show.assert_called_once_with()
        old_info.assert_not_called()
        old_warn.assert_not_called()
        self.assertFalse(window._manual_update_summary)


if __name__ == "__main__":
    unittest.main()
