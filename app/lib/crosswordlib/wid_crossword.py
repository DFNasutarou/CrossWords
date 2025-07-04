# widgets.py
from PyQt5.QtWidgets import (
    QWidget,
    QLayout,
    QInputDialog,
)
from ..formlib.widgets import WidgetSetting, EditableTextWidget
from .wid_cell import CellBoard
from .wid_key import KeyWidget, BlackOutText
from .black_setting_panel import BlackPanelForm, KeyData
from .format_setting_panel import FormatPanelForm, FormatData
from ..formlib.layouts import RowLayout, ColLayout
from .const_color import Col
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt

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
        base.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        board_widget = QWidget()
        board = ColLayout(board_widget)

        base.addWidget(board_widget)

        cell_board = CellBoard(
            self.board_size, size[1] - DEFAULT_TITLE_SIZE, self
        )

        board.addWidget(cell_board)
        key = KeyWidget(self)
        board.addWidget(key)

        key.update(*cell_board.get_num_list())

        self.title = title
        self.cell_board = cell_board
        self.key = key
        self.world = WorldSetting()

        # マージン設定
        board.setContentsMargins(10, 10, 10, 10)
        board.setSpacing(20)
        board.update()

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

        self.world_update()
        self.key.check_all_answers()

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
        kd_list = [KeyData.clone_key_data(kg) for kg in kg_list]

        # 子フォームを生成。初期値も渡せる
        dlg = BlackPanelForm(kd_list, parent=self)
        # 子フォームからの submitted シグナルを受け取る
        # dlg.submitted.connect(self.receive_from_child)
        # モーダル表示（親を操作不可にしたいなら exec_()）
        dlg.exec_()
        # モデルレスなら dlg.show() を使います

        # 子フォームを閉じた後の処理
        for kg, kd in zip(kg_list, kd_list):
            KeyData.copy_keydata_setting_to_keygroup(kg, kd)

    def format_setting_panel(self):
        fd = FormatData(
            self.world.title,
            self.world.key_title,
            self.world.key_set,
            self.world.board,
        )

        # 子フォームを生成。初期値も渡せる
        dlg = FormatPanelForm(fd, parent=self)
        # 子フォームからの submitted シグナルを受け取る
        # dlg.submitted.connect(self.receive_from_child)
        # モーダル表示（親を操作不可にしたいなら exec_()）
        dlg.exec_()
        # モデルレスなら dlg.show() を使います

        # 子フォームを閉じた後の処理
        self.world_update()

    def set_world(
        self,
        board_black=None,
        key_black=None,
        show_ans=None,
        title: WidgetSetting | None = None,
        key_title: WidgetSetting | None = None,
        key_set: WidgetSetting | None = None,
        board: WidgetSetting | None = None,
    ):
        # 黒塗り、表示を変更
        if board_black != None:
            pass
            # self.world.data[WorldSetting.FORMAT_BOARD]
        if key_black != None:
            self.world.data[WorldSetting.BLACK] = not self.world.data[
                WorldSetting.BLACK
            ]
        if show_ans != None:
            self.world.data[WorldSetting.SHOW_ANS] = not self.world.data[
                WorldSetting.SHOW_ANS
            ]
        if title != None:
            self.world.title = title
        if key_title != None:
            self.world.key_title = key_title
        if key_set != None:
            self.world.key_set = key_set
        if board != None:
            self.world.board = board

        self.world_update()

    def world_update(self):
        self.title.set_font(self.world.title.data[WidgetSetting.SIZE])
        bd: WidgetSetting = self.world.board
        mg: int = bd.data[WidgetSetting.MARGIN]
        self.cell_board.set_margine(
            [mg, mg, mg, mg], bd.data[WidgetSetting.SIZE]
        )
        self.key.setting_update(self.world.key_title, self.world.key_set)
        self.key.show_setting(
            self.world.data[WorldSetting.BLACK],
            self.world.data[WorldSetting.SHOW_KEY],
            self.world.data[WorldSetting.SHOW_TEXT],
            self.world.data[WorldSetting.SHOW_ANS],
        )

    def get_capture(self):
        return self.grab()

    def delete_guaid(self):
        EditableTextWidget.guaid = not EditableTextWidget.guaid
        self.update()

    def notify(self, event, data=[]):
        if event == 1:
            self.key.update(*self.cell_board.get_num_list())
        elif event == 2:
            num, text = data
            self.cell_board.set_answer_row(num, text)
        elif event == 3:
            num, text = data
            self.cell_board.set_answer_col(num, text)


class WorldSetting:
    # 黒塗り・表示設定
    BLACK = "black"
    SHOW_ANS = "show_ans"
    SHOW_KEY = "show_key"
    SHOW_TEXT = "show_text"
    FORMAT_TITLE = "format_title"
    FORMAT_KEY_TITLE = "format_key_title"
    FORMAT_KEY_SET = "format_key_set"
    FORMAT_BOARD = "format_board"

    def __init__(self):
        self.data = {}
        self.data[WorldSetting.BLACK] = 0
        self.data[WorldSetting.SHOW_ANS] = 1
        self.data[WorldSetting.SHOW_KEY] = 1
        self.data[WorldSetting.SHOW_TEXT] = 1
        self.title = WidgetSetting(60)
        self.key_title = WidgetSetting(20)
        self.key_set = WidgetSetting(16)
        self.board = WidgetSetting(400)

    def save(self):
        self.data[WorldSetting.FORMAT_TITLE] = self.title.save()
        self.data[WorldSetting.FORMAT_KEY_TITLE] = self.key_title.save()
        self.data[WorldSetting.FORMAT_KEY_SET] = self.key_set.save()
        self.data[WorldSetting.FORMAT_BOARD] = self.board.save()
        return self.data

    def load(self, data):
        self.data = data
        self.title.load(self.data[WorldSetting.FORMAT_TITLE])
        self.key_title.load(self.data[WorldSetting.FORMAT_KEY_TITLE])
        self.key_set.load(self.data[WorldSetting.FORMAT_KEY_SET])
        self.board.load(self.data[WorldSetting.FORMAT_BOARD])

    def show_data(self):
        black = self.data[WorldSetting.BLACK]
        key = self.data[WorldSetting.SHOW_KEY]
        text = self.data[WorldSetting.SHOW_TEXT]
        ans = self.data[WorldSetting.SHOW_ANS]
        return [black, key, text, ans]
