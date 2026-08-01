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

    def test_unchecked_cells_solve_user_reported_case(self):
        # タテ1,2,3,6／ヨコ1,4,5,7 はクロスしない1文字マスを
        # 許可しないと解が存在しない
        strict = enumerate_boards(
            [1, 2, 3, 6],
            [1, 4, 5, 7],
            sizes=[4],
        )
        relaxed = enumerate_boards(
            [1, 2, 3, 6],
            [1, 4, 5, 7],
            sizes=[4],
            allow_unchecked_cells=True,
        )

        self.assertEqual(len(strict.results), 0)
        self.assertGreater(len(relaxed.results), 0)
        match = relaxed.results[0].numberings[0]
        self.assertEqual(match.vertical_numbers, (1, 2, 3, 6))
        self.assertEqual(match.horizontal_numbers, (1, 4, 5, 7))

    def test_general_search_without_point_symmetry(self):
        outcome = enumerate_boards(
            [1, 2, 3, 5, 7, 9],
            [1, 4, 5, 6, 7, 8, 10],
            sizes=[5],
            require_point_symmetry=False,
            allow_unchecked_cells=True,
            limit=1,
        )

        self.assertEqual(len(outcome.results), 1)

    def test_unchecked_search_finds_real_board(self):
        # save/nasu の実盤面（6×6・点対称・1文字マスあり）の
        # カギ番号から元の盤面が復元できること
        board = (
            (0, 1, 0, 0, 0, 0),
            (0, 0, 1, 0, 0, 1),
            (0, 0, 0, 0, 1, 0),
            (0, 1, 0, 0, 0, 0),
            (1, 0, 0, 1, 0, 0),
            (0, 0, 0, 0, 1, 0),
        )
        outcome = enumerate_boards(
            [1, 3, 4, 6, 9, 10, 12, 13],
            [2, 5, 7, 8, 11, 13, 14, 15],
            sizes=[6],
            numbering_modes=(NUMBERING_TOP_PRIORITY,),
            allow_unchecked_cells=True,
        )

        self.assertIn(board, [c.grid for c in outcome.results])

    def test_isolated_white_cell_is_rejected(self):
        from app.lib.crosswordlib.board_enumerator import (
            no_isolated_white_cells,
        )

        # (0, 2) は横1文字かつ縦1文字の孤立マス
        isolated = (0b1010, 0b0100, 0, 0)
        healthy = (0b1010, 0, 0, 0)

        self.assertFalse(no_isolated_white_cells(isolated, 4))
        self.assertTrue(no_isolated_white_cells(healthy, 4))

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
