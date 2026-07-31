import unittest

from app.lib.crosswordlib.geometry import snapped_blackout_square


class SnappedBlackoutSquareTest(unittest.TestCase):
    def test_snaps_forward_drag_to_character_boundaries(self):
        self.assertEqual(
            snapped_blackout_square(12, 37, 10, 6),
            [[10.0, 40.0], [0.0, 10.0]],
        )

    def test_snaps_reverse_drag_to_character_boundaries(self):
        self.assertEqual(
            snapped_blackout_square(37, 12, 10, 6),
            [[10.0, 40.0], [0.0, 10.0]],
        )

    def test_clamps_drag_outside_text(self):
        self.assertEqual(
            snapped_blackout_square(-20, 200, 10, 4),
            [[0.0, 40.0], [0.0, 10.0]],
        )

    def test_empty_text_returns_empty_horizontal_range(self):
        self.assertEqual(
            snapped_blackout_square(0, 10, 10, 0),
            [[0.0, 0.0], [0.0, 10.0]],
        )


if __name__ == "__main__":
    unittest.main()
