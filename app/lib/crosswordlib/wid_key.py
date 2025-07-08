# widgets.py
from PyQt5.QtWidgets import QWidget, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPainter, QFontMetrics
from PyQt5.QtCore import QRect, Qt
from app.lib.formlib.widgets import EditableTextWidget, WidgetSetting
from app.lib.crosswordlib.const_color import Col
from app.lib.formlib.layouts import RowLayout, ColLayout

KEY_NUMBER = 100

STR_ROW_KEY_TITLE = "row_title"
STR_ROW_KEY_TITLE_SIZE = "row_title_size"
STR_ROW_KEY = "row_key"
STR_ROW_KEY_SIZE = "row_key_size"
STR_COL_KEY_TITLE = "col_title"
STR_COL_KEY_TITLE_SIZE = "col_title_size"
STR_COL_KEY_SIZE = "col_key_size"
STR_COL_KEY = "col_key"
KEY_NAME_LENGTH = "key_name_length"

TYPE_ROW = "type_row"
TYPE_COL = "type_col"
TYPE_KEY = "type_key"


class KeyWidget(QWidget):
    def __init__(self, listener):
        super().__init__()
        self.listener = listener

        self.data = {}
        self.default_setting()
        spacer = []
        for i in range(3):
            spacer.append(
                QSpacerItem(
                    0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
                )
            )
        print(spacer)
        base = RowLayout(self)
        base.addWidget(self.rowkeytext)
        base.addItem(spacer[0])
        for i in range(KEY_NUMBER):
            base.addWidget(self.rows[i])
        base.addItem(spacer[1])
        base.addWidget(self.colkeytext)
        base.addItem(spacer[2])
        for i in range(KEY_NUMBER):
            base.addWidget(self.cols[i])
        base.addStretch()

        self.spacer = spacer

    def setting_update(
        self,
        key_title_setting: WidgetSetting | None = None,
        key_setting: WidgetSetting | None = None,
        key_text_setting: WidgetSetting | None = None,
        key_anser_setting: WidgetSetting | None = None,
        black: bool | None = None,
    ) -> None:
        if key_title_setting != None:
            BlackKeyTitle.setting(key_title_setting)
        if key_setting != None:
            BlackKeyNameText.setting(key_setting)
        if key_text_setting != None:
            BlackKeyText.setting(key_text_setting)
        if key_anser_setting != None:
            BlackKeyAnswer.setting(key_anser_setting)

    def default_setting(self):
        self.data[STR_ROW_KEY_TITLE] = "タテのカギ"
        self.data[STR_ROW_KEY_TITLE_SIZE] = -1
        self.rows = [
            KeyGroup(TYPE_ROW, i, self, str(i), "") for i in range(KEY_NUMBER)
        ]
        self.data[STR_ROW_KEY] = [w.save() for w in self.rows]
        self.data[STR_ROW_KEY_SIZE] = -1
        self.data[STR_COL_KEY_TITLE] = "ヨコのカギ"
        self.data[STR_COL_KEY_TITLE_SIZE] = -1
        self.cols = [
            KeyGroup(TYPE_COL, i, self, str(i), "") for i in range(KEY_NUMBER)
        ]
        self.data[STR_COL_KEY] = [w.save() for w in self.cols]
        self.data[STR_COL_KEY_SIZE] = -1
        self.data[KEY_NAME_LENGTH] = -1

        self.rowkeytext = BlackKeyTitle(self.data[STR_ROW_KEY_TITLE])
        self.colkeytext = BlackKeyTitle(self.data[STR_COL_KEY_TITLE])

    def visible_update(self, row_open_list, col_open_list):
        for i in range(KEY_NUMBER):
            self.rows[i].set_all_visible(i in row_open_list)
            self.cols[i].set_all_visible(i in col_open_list)

    def save(self):
        self.data[STR_ROW_KEY_TITLE] = self.rowkeytext.save()
        self.data[STR_COL_KEY_TITLE] = self.colkeytext.save()
        self.data[STR_ROW_KEY] = [w.save() for w in self.rows]
        self.data[STR_COL_KEY] = [w.save() for w in self.cols]
        return self.data

    def load(self, data):
        self.data = data
        self.rowkeytext.load(self.data[STR_ROW_KEY_TITLE])
        self.colkeytext.load(self.data[STR_COL_KEY_TITLE])
        for i in range(KEY_NUMBER):
            self.rows[i].load(self.data[STR_ROW_KEY][i])
            self.cols[i].load(self.data[STR_COL_KEY][i])

    def get_visible_list(self):
        ret = []
        ret.append(self.rowkeytext)
        for kg in self.rows:
            if kg.is_visible:
                ret.append(kg)
        ret.append(self.colkeytext)
        for kg in self.cols:
            if kg.is_visible:
                ret.append(kg)
        return ret

    def show_setting(self, black, key, text, answer) -> None:
        # BlackKeyText.set_black(black)
        # BlackKeyTitle.set_black(black)
        # BlackKeyText.set_black(black)
        BlackOutText.set_black(black)
        for kg in self.rows + self.cols:
            kg.set_visible(key, text, answer)
        self.update()

    def check_all_answers(self):
        data = self.rows + self.cols
        for w in data:
            txt = w.answer.get_text()
            if w.isVisible and txt != "":
                w.notify(txt)

    def notify(self, tp, num, text):
        if tp == TYPE_ROW:
            event = 2
        elif tp == TYPE_COL:
            event = 3
        elif tp == TYPE_KEY:
            event = -1
        self.listener.notify(event, [num, text])


class BlackOutText(EditableTextWidget):
    """
    黒塗り可能なテキスト
    """

    black = 0

    def __init__(self, text="", listner=None):
        super().__init__(text, listner, Col.black)
        self.data = []
        self.del_ghost()

    def save(self):
        data = [super().save()]
        data.extend(self.get_square())
        return data

    def load(self, data):
        text = data[0]
        super().load(text)
        self.reset_square(data[1:])

    def set_ghost(self, square: list[list[float]]):
        self.ghost = square
        self.update()

    def del_ghost(self):
        self.ghost: list[list[float]] = [[0.0, 0.0], [0.0, 10.0]]
        self.update()

    def add_square(self, square):
        self.data.append(square)
        self.update()

    def add_squares(self, squares):
        for square in squares:
            self.data.append(square)
        self.update()

    def reset_square(self, squares):
        self.data = squares
        self.update()

    def get_square(self):
        return self.data

    def remove_square(self, square):
        if square in self.data:
            self.data.remove(square)
            self.update()

    def square_exchange(self, square):
        font = self.label.font()
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance("あ")
        # if self.label.text() != "":
        #     w = self.label.width() / len(self.label.text())
        # else:
        #     w = 0
        h = self.label.height()

        x1 = max(0, int(w * square[0][0] / 10))
        x2 = min(self.label.width(), int(w * square[0][1] / 10))
        y1 = max(0, int(h * square[1][0] / 10))
        y2 = min(h, int(h * square[1][1] / 10))
        # print(square, w, h, x1, x2, y1, y2)
        return [x1, y1, x2, y2]

    def paintEvent(self, event):
        super().paintEvent(event)
        if BlackOutText.black:
            painter = QPainter(self)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(Col.black)
            for square in self.data:
                t = self.square_exchange(square)
                painter.drawRect(QRect(*t))

            painter.setBrush(Col.ghost)
            t = self.square_exchange(self.ghost)
            painter.drawRect(QRect(*t))

            painter.end()

    def clone(self):
        ret = BlackOutText(self.get_text())
        # ret.set_black(self.black)
        for square in self.get_square():
            ret.add_square(square)
        return ret

    @classmethod
    def set_black(cls, black):
        # 黒塗りするなら1
        cls.black = black


class BlackKeyAnswer(EditableTextWidget):
    wid = 40
    font_size = 16
    margin = [0, 0, 0, 0]
    col = Col.red
    _instances: list["BlackKeyAnswer"] = []

    def __init__(self, text, listener):
        super().__init__(text, listener, BlackKeyAnswer.col)
        self.configure()
        self.__class__._instances.append(self)

    def configure(self):
        self.set_font(BlackKeyAnswer.font_size)
        self.setContentsMargins(*BlackKeyAnswer.margin)
        self.set_minimum_length(BlackKeyAnswer.wid)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.margin = setting.data[WidgetSetting.MARGIN]
        for inst in cls._instances:
            inst.configure()


class BlackKeyTitle(BlackOutText):
    wid = 40
    font_size = 40
    margin = [0, 0, 0, 0]
    col = Col.black
    _instances: list["BlackKeyTitle"] = []

    def __init__(self, text):
        super().__init__(text)
        self.configure()
        self.__class__._instances.append(self)

    def configure(self):
        self.set_font(BlackKeyTitle.font_size)
        self.setContentsMargins(*BlackKeyTitle.margin)
        self.set_minimum_length(BlackKeyTitle.wid)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.margin = setting.data[WidgetSetting.MARGIN]
        for inst in cls._instances:
            inst.configure()


class BlackKeyNameText(BlackOutText):
    wid = 40
    font_size = 40
    margin = [0, 0, 0, 0]
    col = Col.black
    _instances: list["BlackKeyNameText"] = []

    def __init__(self, text):
        super().__init__(text)
        self.configure()
        self.__class__._instances.append(self)

    def configure(self):
        self.set_font(BlackKeyNameText.font_size)
        self.setContentsMargins(*BlackKeyNameText.margin)
        self.set_minimum_length(BlackKeyNameText.wid)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.margin = setting.data[WidgetSetting.MARGIN]
        for inst in cls._instances:
            inst.configure()


class BlackKeyText(BlackOutText):
    wid = 40
    font_size = 40
    margin = [0, 0, 0, 0]
    col = Col.black
    _instances: list["BlackKeyText"] = []

    def __init__(self, text):
        super().__init__(text)
        self.configure()
        self.__class__._instances.append(self)

    def configure(self):
        self.set_font(BlackKeyText.font_size)
        self.setContentsMargins(*BlackKeyText.margin)
        self.set_minimum_length(BlackKeyText.wid)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.margin = setting.data[WidgetSetting.MARGIN]
        for inst in cls._instances:
            inst.configure()


class KeyGroup(QWidget):
    """
    カギ一個分(カギ名、指示、回答)
    """

    KEY_NAME = "key_name"
    TEXT = "text"
    ANSWER = "answer"

    def __init__(self, tp, num, listener=None, keyname="", text="", answer=""):
        super().__init__()
        self.tp = tp
        self.num = num
        self.is_visible = True
        self.listener = listener
        self.base = ColLayout(self)
        self.keyname = BlackKeyNameText(keyname)
        self.text = BlackKeyText(text)
        self.answer = BlackKeyAnswer(answer, self)
        self.widgets: list[EditableTextWidget] = [
            self.keyname,
            self.text,
            self.answer,
        ]

        for key in self.widgets:
            self.base.addWidget(key)

        # マージン設定
        self.base.setSpacing(8)
        self.base.update()

    def save(self):
        data = {}
        data[KeyGroup.KEY_NAME] = self.keyname.save()
        data[KeyGroup.TEXT] = self.text.save()
        data[KeyGroup.ANSWER] = self.answer.save()
        return data

    def load(self, data):
        self.keyname.load(data[KeyGroup.KEY_NAME])
        self.text.load(data[KeyGroup.TEXT])
        self.answer.load(data[KeyGroup.ANSWER])

    def set_text(self, keyname="", text="", answer=""):
        for w, v in zip(self.widgets, [keyname, text, answer]):
            w.set_text(v)

    # def read_setting(self, data: WidgetSetting):
    #     self.set_font(data.data[WidgetSetting.SIZE])

    # def set_font(self, font_size):
    #     for w in self.widgets:
    #         w.set_font(font_size)

    def get_text(self):
        data = []
        for w in self.widgets:
            data.append(w.get_text())
        return data

    def set_visible(self, key=True, text=True, answer=True):
        # 表示設定　基本的には答えを非表示にするのに使う
        for w, v in zip(self.widgets, [key, text, answer]):
            if v:
                w.show()
            else:
                w.hide()

    def set_all_visible(self, is_visible):
        self.is_visible = is_visible
        if self.is_visible:
            self.show()
        else:
            self.hide()

    # def set_min_size(self, key, text, answer):
    #     for w, v in zip(self.widgets, [key, text, answer]):
    #         w.set_minimum_length(v)

    # def set_black(self, black):
    #     self.keyname.set_black(black)
    #     self.text.set_black(black)

    def notify(self, text):
        if self.listener:
            self.listener.notify(self.tp, self.num, text)
