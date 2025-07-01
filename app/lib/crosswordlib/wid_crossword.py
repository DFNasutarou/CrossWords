# widgets.py
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QSizePolicy,
)
from .wid_cell import CellBoard
from .wid_key import KeyWidget, BlackOutText


DEFAULT_BOARD_SIZE = 5
DEFAULT_CELL_SIZE = 40

DEFAULT_TITLE_SIZE = 60


class CrossWord(QWidget):
    def __init__(self, size):
        super().__init__()
        self.board_size = DEFAULT_BOARD_SIZE
        self.cell_size = DEFAULT_CELL_SIZE

        base = QVBoxLayout(self)
        base.setSpacing(0)
        title = BlackOutText("最終指示をここに表示")
        title.setFixedHeight(DEFAULT_TITLE_SIZE)
        base.addWidget(title)

        board_widget = QWidget()
        board_widget.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding
        )
        board = QHBoxLayout(board_widget)
        board.setSpacing(0)
        base.addWidget(board_widget, stretch=1)

        cell_board = CellBoard(
            self.board_size, size[1] - DEFAULT_TITLE_SIZE, self
        )
        cell_board.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        board.addWidget(cell_board)
        cell_board.resize()
        key = KeyWidget(self)
        board.addWidget(key)

        key.update(*cell_board.get_num_list())
        self.cell_board = cell_board
        self.key = key

    def save(self):
        data = {}
        data["cell"] = self.cell_board.save()
        data["key"] = self.key.save()
        return data

    def load(self, data):
        self.cell_board.load(data["cell"])
        self.key.load(data["key"])
        self.key.update(*self.cell_board.get_num_list())

    def notify(self, event, data=[]):
        if event == 1:
            self.key.update(*self.cell_board.get_num_list())
        elif event == 2:
            num, text = data
            self.cell_board.set_answer_row(num, text)
        elif event == 3:
            num, text = data
            self.cell_board.set_answer_col(num, text)
