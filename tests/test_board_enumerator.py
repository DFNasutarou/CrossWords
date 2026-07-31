import unittest

from app.lib.crosswordlib.board_enumerator import (
    BLACK,
    NUMBERING_LEFT_PRIORITY,
    NUMBERING_TOP_PRIORITY,
    BoardEnumerationError,
    board_rules_valid,
    build_symmetric_rows,
    clue_numbers,
    enumerate_boards,
    normalize_clue_pattern,
    parse_clue_pattern_text,
    pattern_matches,
    point_symmetric,
    size_can_match,
    vertical_clue_count,
)


class BoardEnumeratorTest(unittest.TestCase):
    def test_normalizes_blackout_markers(self):
        self.assertEqual(
            normalize_clue_pattern(["1", "黒", "?", 5]),
            (1, None, None, 5),
        )

    def test_parses_comma_space_and_newline_separated_input(self):
        self.assertEqual(
            parse_clue_pattern_text("1, 黒  4\n5"),
            (1, None, 4, 5),
        )

    def test_rejects_impossible_known_number_gap(self):
        with self.assertRaises(BoardEnumerationError):
            normalize_clue_pattern([1, None, None, 3])

    def test_pattern_matches_unknown_numbers(self):
        self.assertTrue(
            pattern_matches((1, None, None, 5), (1, 2, 4, 5))
        )
        self.assertFalse(
            pattern_matches((1, None, None, 5), (1, 2, 4, 6))
        )

    def test_builds_point_symmetric_rows(self):
        rows = build_symmetric_rows([0b0001, 0b0100], None, 4)

        self.assertTrue(point_symmetric(rows, 4))
        self.assertEqual(rows, (0b0001, 0b0100, 0b0010, 0b1000))

    def test_rejects_adjacent_black_or_single_character_clue(self):
        adjacent = (0b0011, 0, 0, 0b1100)
        single = (0b0100, 0, 0, 0b0010)

        self.assertFalse(board_rules_valid(adjacent, 4))
        self.assertFalse(board_rules_valid(single, 4))

    def test_even_size_requires_even_clue_counts(self):
        self.assertFalse(size_can_match(4, 3, 4))
        self.assertFalse(size_can_match(4, 4, 3))

    def test_odd_size_requires_matching_parity(self):
        self.assertFalse(size_can_match(5, 4, 5))

    def test_numbering_modes_can_produce_different_sequences(self):
        rows = (
            0b0001,
            0b0100,
            0b0010,
            0b1000,
        )

        top = clue_numbers(rows, 4, NUMBERING_TOP_PRIORITY)
        left = clue_numbers(rows, 4, NUMBERING_LEFT_PRIORITY)

        self.assertNotEqual(top, left)

    def test_enumerates_four_by_four_boards_and_deduplicates_modes(self):
        outcome = enumerate_boards(
            [None, None, None, None],
            [None, None, None, None],
            sizes=[4],
        )

        self.assertGreater(len(outcome.results), 0)
        self.assertEqual(
            len({candidate.grid for candidate in outcome.results}),
            len(outcome.results),
        )
        for candidate in outcome.results:
            self.assertTrue(board_rules_valid(
                tuple(
                    sum(
                        cell == BLACK and (1 << col) or 0
                        for col, cell in enumerate(row)
                    )
                    for row in candidate.grid
                ),
                candidate.size,
            ))
            self.assertEqual(
                vertical_clue_count(
                    tuple(
                        sum(
                            cell == BLACK and (1 << col) or 0
                            for col, cell in enumerate(row)
                        )
                        for row in candidate.grid
                    ),
                    candidate.size,
                ),
                4,
            )

    def test_exact_numbers_remove_inconsistent_numbering_mode(self):
        outcome = enumerate_boards(
            [1, 2, 3, 4],
            [1, 5, 6, 7],
            sizes=[4],
        )

        all_white = next(
            candidate
            for candidate in outcome.results
            if not candidate.black_cells
        )
        self.assertEqual(
            [match.mode for match in all_white.numberings],
            [NUMBERING_TOP_PRIORITY],
        )

    def test_odd_center_is_white_for_odd_clue_counts(self):
        outcome = enumerate_boards(
            [None] * 5,
            [None] * 5,
            sizes=[5],
            limit=1,
        )

        self.assertEqual(outcome.results[0].grid[2][2], 0)

    def test_odd_center_is_black_for_even_clue_counts(self):
        outcome = enumerate_boards(
            [None] * 6,
            [None] * 6,
            sizes=[5],
            limit=1,
        )

        self.assertEqual(outcome.results[0].grid[2][2], BLACK)

    def test_applies_result_limit(self):
        outcome = enumerate_boards(
            [None, None, None, None],
            [None, None, None, None],
            sizes=[4],
            limit=1,
        )

        self.assertEqual(len(outcome.results), 1)
        self.assertTrue(outcome.truncated)


if __name__ == "__main__":
    unittest.main()
