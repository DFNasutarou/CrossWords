# widgets.py
from PyQt5.QtWidgets import (
    QWidget,
    QLayout,
    QInputDialog,
)
from .wid_cell import CellBoard
from .wid_key import KeyWidget, BlackOutText
from .black_setting_panel import BlackPanelForm
from ..formlib.layouts import RowLayout, ColLayout
from .const_color import Col
from PyQt5.QtGui import QPalette

DEFAULT_BOARD_SIZE = 5
DEFAULT_CELL_SIZE = 40

DEFAULT_TITLE_SIZE = 60


class CrossWord(QWidget):
    def __init__(self, size):
        super().__init__()
        self.board_size = DEFAULT_BOARD_SIZE
        self.cell_size = DEFAULT_CELL_SIZE

        base = RowLayout(self)
        base.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        palette = self.palette()
        palette.setColor(QPalette.Window, Col.white)  # RGB値で指定
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        title = BlackOutText("最終指示をここに表示")
        title.setFixedHeight(DEFAULT_TITLE_SIZE)
        base.addWidget(title)

        board_widget = QWidget()
        # board_widget.setSizePolicy(
        #     QSizePolicy.Preferred, QSizePolicy.Expanding
        # )
        board = ColLayout(board_widget)

        # base.addWidget(board_widget, stretch=1)
        base.addWidget(board_widget)

        cell_board = CellBoard(
            self.board_size, size[1] - DEFAULT_TITLE_SIZE, self
        )
        # cell_board.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        board.addWidget(cell_board)
        key = KeyWidget(self)
        board.addWidget(key)

        key.update(*cell_board.get_num_list())
        self.cell_board = cell_board
        self.key = key
        self.world = WorldSetting()

    def save(self):
        data = {}
        data["cell"] = self.cell_board.save()
        data["key"] = self.key.save()
        data["world"] = self.world.save()
        return data

    def load(self, data):
        self.cell_board.load(data["cell"])
        self.key.load(data["key"])
        self.key.update(*self.cell_board.get_num_list())
        self.world.load(data["world"])

    def resize_board(self):
        # ボードの大きさを変更

        size, ok = QInputDialog.getInt(
            None,
            "盤サイズ変更",
            "盤のサイズを入力してください",
            value=5,
            min=4,
            max=9,
            step=1,
        )
        if not ok:
            return  # キャンセル
        self.cell_board.resize(size)

    def black_setting_panel(self):
        kg_list = self.key.get_visible_list()
        # self.key.show_setting(1, 1, 1, 1)

        # 子フォームを生成。初期値も渡せる
        dlg = BlackPanelForm(kg_list, parent=self)
        # 子フォームからの submitted シグナルを受け取る
        # dlg.submitted.connect(self.receive_from_child)
        # モーダル表示（親を操作不可にしたいなら exec_()）
        dlg.exec_()
        # モデルレスなら dlg.show() を使います

        # 子フォームを閉じた後の処理
        w = self.world
        self.key.show_setting(*self.world.show_data())

    def notify(self, event, data=[]):
        if event == 1:
            self.key.update(*self.cell_board.get_num_list())
        elif event == 2:
            num, text = data
            self.cell_board.set_answer_row(num, text)
        elif event == 3:
            num, text = data
            self.cell_board.set_answer_col(num, text)


BLACK = "black"
SHOW_ANS = "show_ans"
SHOW_KEY = "show_key"
SHOW_TEXT = "show_text"


class WorldSetting:
    # パネルから戻った時に変更するものを管理
    def __init__(self):
        self.black = 0
        self.show_ans = 1
        self.show_key = 1
        self.show_text = 1

    def save(self):
        save_data = {}
        save_data[BLACK] = self.black
        save_data[SHOW_ANS] = self.show_ans
        save_data[SHOW_KEY] = self.show_key
        save_data[SHOW_TEXT] = self.show_text
        return save_data

    def load(self, load_data):
        self.black = load_data[BLACK]
        self.show_ans = load_data[SHOW_ANS]
        self.show_key = load_data[SHOW_KEY]
        self.show_text = load_data[SHOW_TEXT]

    def show_data(self):
        return [self.black, self.show_key, self.show_text, self.show_ans]
