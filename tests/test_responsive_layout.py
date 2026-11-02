"""Responsive Launcher breakpoints; geometry is checked in a separate Qt smoke process."""
import unittest
from launcher import responsive_columns


class ResponsiveColumnsTests(unittest.TestCase):
    def test_four_columns_when_width_supports_eight_cards_in_two_rows(self):
        for width in (1120, 1280, 1450, 1920):
            with self.subTest(width=width):
                self.assertEqual(responsive_columns(width), 4)

    def test_automatic_narrow_screen_fallback(self):
        self.assertEqual(responsive_columns(1119), 3)
        self.assertEqual(responsive_columns(870), 3)
        self.assertEqual(responsive_columns(869), 2)
        self.assertEqual(responsive_columns(810), 2)


if __name__ == "__main__":
    unittest.main()
