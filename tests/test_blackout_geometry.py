import unittest

from app.lib.crosswordlib.geometry import blackout_rect, scaled_dimensions


class BlackoutRectTest(unittest.TestCase):
    def test_converts_end_points_to_width_and_height(self):
        rect = blackout_rect(
            [[50.0, 140.0], [2.0, 8.0]],
            unit_width=10,
            content_width=200,
            content_height=40,
        )

        self.assertEqual(rect, [50, 8, 90, 24])

    def test_offsets_rectangle_by_content_position(self):
        rect = blackout_rect(
            [[0.0, 20.0], [0.0, 10.0]],
            unit_width=10,
            content_width=200,
            content_height=40,
            offset_x=12,
            offset_y=7,
        )

        self.assertEqual(rect, [12, 7, 20, 40])

    def test_clamps_rectangle_to_content_area(self):
        rect = blackout_rect(
            [[-10.0, 500.0], [-2.0, 12.0]],
            unit_width=10,
            content_width=80,
            content_height=30,
            offset_x=5,
            offset_y=4,
        )

        self.assertEqual(rect, [5, 4, 80, 30])

    def test_accepts_reversed_ranges(self):
        rect = blackout_rect(
            [[40.0, 10.0], [10.0, 0.0]],
            unit_width=10,
            content_width=100,
            content_height=20,
        )

        self.assertEqual(rect, [10, 0, 30, 20])


class ScaledDimensionsTest(unittest.TestCase):
    def test_doubles_both_dimensions(self):
        self.assertEqual(scaled_dimensions(600, 400, 2), (1200, 800))

    def test_rejects_non_positive_scale(self):
        with self.assertRaises(ValueError):
            scaled_dimensions(600, 400, 0)


if __name__ == "__main__":
    unittest.main()
