# widgets.py
from PyQt5.QtWidgets import (
    QWidget,
    QLayout,
    QInputDialog,
)
from ..formlib.widgets import WidgetSetting, EditableTextWidget
from .wid_cell import CellBoard
from .wid_key import (
    KeyWidget,
    BlackOutText,
)
from app.lib.crosswordlib.black_setting_panel import BlackPanelForm, KeyData
from app.lib.crosswordlib.format_setting_panel import (
    FormatPanelForm,
    FormatData,
)
from app.lib.formlib.widgets import GraphicWidget
from app.lib.formlib.layouts import RowLayout, ColLayout
from app.lib.crosswordlib.const_color import Col
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
        # base.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.pic = GraphicWidget()
        base.addWidget(self.pic)

        palette = self.palette()
        palette.setColor(QPalette.Window, Col.white)  # RGB値で指定
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        title = BlackTitleText("指示文", self)
        base.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        board_widget = QWidget()
        board = ColLayout(board_widget)

        base.addWidget(board_widget)

        cell_board = CellBoard(self.board_size, self)

        board.addWidget(cell_board)
        key = KeyWidget(self)
        board.addWidget(key)

        key.visible_update(*cell_board.get_num_list())

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
        self.key.visible_update(*self.cell_board.get_num_list())
        self.world.load(data["world"])

        self.title.set_text(self.world.data[WorldSetting.TITLE_TEXT])
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

    def trans_board(self):
        self.cell_board.trans()
        self.key.trans_key()

    def sort_key(self):
        self.key.sort_key()

    def switch_title(self):
        self.world.data[WorldSetting.SHOW_TITLE] = (
            1 - self.world.data[WorldSetting.SHOW_TITLE]
        )
        self.world_update()

    def black_setting_panel(self):
        kg_list = self.key.get_visible_list()
        kd_list = [KeyData.clone_key_data(kg) for kg in kg_list]
        BlackOutText.set_black(1)

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

        self.world_update()

    def format_setting_panel(self):
        fd = FormatData(
            self.world.title,
            self.world.key_title,
            self.world.key_set,
            self.world.key_text,
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
        board_number=None,
        board_text=None,
        key_black=None,
        show_ans=None,
        title: WidgetSetting | None = None,
        key_title: WidgetSetting | None = None,
        key_set: WidgetSetting | None = None,
        board: WidgetSetting | None = None,
    ):
        # 黒塗り、表示を変更
        if board_black != None:
            self.world.data[WorldSetting.BOARD_BLACK] = (
                1 - self.world.data[WorldSetting.BOARD_BLACK]
            )
        if board_number != None:
            self.world.data[WorldSetting.BOARD_NUMBER] = (
                1 - self.world.data[WorldSetting.BOARD_NUMBER]
            )
        if board_text != None:
            self.world.data[WorldSetting.BOARD_TEXT] = (
                1 - self.world.data[WorldSetting.BOARD_TEXT]
            )
        if key_black != None:
            self.world.data[WorldSetting.BLACK] = (
                1 - self.world.data[WorldSetting.BLACK]
            )
        if show_ans != None:
            self.world.data[WorldSetting.SHOW_ANS] = (
                1 - self.world.data[WorldSetting.SHOW_ANS]
            )
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
        if self.world.data[WorldSetting.SHOW_TITLE]:
            self.title.show()
        else:
            self.title.hide()
        bd: WidgetSetting = self.world.board
        self.cell_board.set_margine(
            bd.data[WidgetSetting.MARGIN], bd.data[WidgetSetting.SIZE]
        )
        self.cell_board.set_board_color(bd.data[WidgetSetting.COLOR])
        self.key.setting_update(
            self.world.key_title,
            self.world.key_set,
            self.world.key_text,
            self.world.key_answer,
        )
        self.key.show_setting(
            self.world.data[WorldSetting.BLACK],
            self.world.data[WorldSetting.SHOW_KEY],
            self.world.data[WorldSetting.SHOW_TEXT],
            self.world.data[WorldSetting.SHOW_ANS],
        )
        self.cell_board.board_black(self.world.data[WorldSetting.BOARD_BLACK])
        self.cell_board.board_number(
            self.world.data[WorldSetting.BOARD_NUMBER]
        )
        self.cell_board.board_text(self.world.data[WorldSetting.BOARD_TEXT])
        self.update()

    def get_capture(self):
        return self.grab()

    def delete_guaid(self):
        EditableTextWidget.guaid = 1 - EditableTextWidget.guaid
        self.update()

    def set_picture(self, pic=None) -> None:
        # 画像をセットする
        # 読み込まなければ削除する
        self.pic.set_pixmap(pic)

    def notify(self, event, data=[]):
        if event == 1:
            self.key.visible_update(*self.cell_board.get_num_list())
        elif event == 2:
            num, text = data
            # self.cell_board.set_answer_row(num, text)
        elif event == 3:
            num, text = data
            # self.cell_board.set_answer_col(num, text)
        elif event == 4:
            self.world.data[WorldSetting.TITLE_TEXT] = data


class WorldSetting:
    # 黒塗り・表示設定
    BLACK = "black"
    BOARD_BLACK = "board_black"
    BOARD_NUMBER = "board_number"
    BOARD_TEXT = "board_text"
    SHOW_TITLE = "show_title"
    SHOW_ANS = "show_ans"
    SHOW_KEY = "show_key"
    SHOW_TEXT = "show_text"
    TITLE_TEXT = "title_text"
    FORMAT_TITLE = "format_title"
    FORMAT_KEY_TITLE = "format_key_title"
    FORMAT_KEY_SET = "format_key_set"
    FORMAT_KEY_TEXT = "format_key_text"
    FORMAT_KEY_ANSWER = "format_key_answer"
    FORMAT_BOARD = "format_board"

    def __init__(self):
        self.data = {}
        self.data[WorldSetting.BLACK] = 0
        self.data[WorldSetting.BOARD_BLACK] = 0
        self.data[WorldSetting.BOARD_NUMBER] = 1
        self.data[WorldSetting.BOARD_TEXT] = 1
        self.data[WorldSetting.SHOW_TITLE] = 1
        self.data[WorldSetting.SHOW_ANS] = 1
        self.data[WorldSetting.SHOW_KEY] = 1
        self.data[WorldSetting.SHOW_TEXT] = 1
        self.data[WorldSetting.TITLE_TEXT] = "指示文"
        self.title = WidgetSetting(60, 600, "#0000000")
        self.key_title = WidgetSetting(20, 100, "#0000000")
        self.key_set = WidgetSetting(16, 32, "#0000000")
        self.key_text = WidgetSetting(16, 480, "#0000000")
        self.key_answer = WidgetSetting(16, 96, "#0000000")
        self.board = WidgetSetting(400, 400, "#0000000")

    def save(self):
        self.data[WorldSetting.FORMAT_TITLE] = self.title.save()
        self.data[WorldSetting.FORMAT_KEY_TITLE] = self.key_title.save()
        self.data[WorldSetting.FORMAT_KEY_SET] = self.key_set.save()
        self.data[WorldSetting.FORMAT_KEY_TEXT] = self.key_text.save()
        self.data[WorldSetting.FORMAT_KEY_ANSWER] = self.key_answer.save()
        self.data[WorldSetting.FORMAT_BOARD] = self.board.save()
        return self.data

    def load(self, data):
        for k, v in data.items():
            self.data[k] = v
        self.title.load(self.data[WorldSetting.FORMAT_TITLE])
        self.key_title.load(self.data[WorldSetting.FORMAT_KEY_TITLE])
        self.key_set.load(self.data[WorldSetting.FORMAT_KEY_SET])
        self.key_text.load(self.data[WorldSetting.FORMAT_KEY_TEXT])
        self.key_answer.load(self.data[WorldSetting.FORMAT_KEY_ANSWER])
        self.board.load(self.data[WorldSetting.FORMAT_BOARD])

    def show_data(self):
        black = self.data[WorldSetting.BLACK]
        key = self.data[WorldSetting.SHOW_KEY]
        text = self.data[WorldSetting.SHOW_TEXT]
        ans = self.data[WorldSetting.SHOW_ANS]
        return [black, key, text, ans]


class BlackTitleText(BlackOutText):
    wid = 40
    font_size = 40
    margin = [0, 0, 0, 0]
    col = Col.black
    _instances: list["BlackTitleText"] = []

    def __init__(self, text, notify):
        super().__init__(text, self)
        self.configure()
        self.__class__._instances.append(self)
        self.listener = notify

    def configure(self):
        self.set_font(BlackTitleText.font_size)
        self.setContentsMargins(*BlackTitleText.margin)
        self.set_minimum_length(BlackTitleText.wid)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.margin = setting.data[WidgetSetting.MARGIN]
        for inst in cls._instances:
            inst.configure()

    def notify(self, text):
        if self.listener:
            self.listener.notify(4, text)
