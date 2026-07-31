import unittest

from app.lib.crosswordlib.clear_helpers import (
    clear_cells,
    clear_clue_widgets,
)


class FakeCell:
    def __init__(self):
        self.state = 1
        self.char = "字"
        self.number = 3

    def set_state(self, state):
        self.state = state

    def set_char(self, char):
        self.char = char

    def set_number(self, number):
        self.number = number


class FakeText:
    def __init__(self, text="元の文字"):
        self.text = text
        self.squares = ["黒塗り"]

    def reset_square(self, squares):
        self.squares = squares

    def set_text(self, text):
        self.text = text


class FakeKeyGroup:
    def __init__(self):
        self.keyname = FakeText("1")
        self.text = FakeText("カギ文")
        self.answer = FakeText("答え")


class ClearCellsTest(unittest.TestCase):
    def test_clears_only_cells_inside_current_board(self):
        cells = [[FakeCell() for _ in range(3)] for _ in range(3)]

        clear_cells(cells, board_size=2, white_state=0)

        for row in range(2):
            for col in range(2):
                self.assertEqual(cells[row][col].state, 0)
                self.assertEqual(cells[row][col].char, "")
                self.assertIsNone(cells[row][col].number)
        self.assertEqual(cells[2][2].state, 1)
        self.assertEqual(cells[2][2].char, "字")


class ClearCluesTest(unittest.TestCase):
    def test_clears_clue_text_and_blackouts_but_keeps_numbers_and_answers(self):
        row_title = FakeText("タテのカギ")
        col_title = FakeText("ヨコのカギ")
        key_group = FakeKeyGroup()

        clear_clue_widgets(row_title, col_title, [key_group])

        self.assertEqual(row_title.text, "タテのカギ")
        self.assertEqual(col_title.text, "ヨコのカギ")
        self.assertEqual(row_title.squares, [])
        self.assertEqual(col_title.squares, [])
        self.assertEqual(key_group.keyname.text, "1")
        self.assertEqual(key_group.keyname.squares, [])
        self.assertEqual(key_group.text.text, "")
        self.assertEqual(key_group.text.squares, [])
        self.assertEqual(key_group.answer.text, "答え")


if __name__ == "__main__":
    unittest.main()
