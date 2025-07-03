# widgets.py
from PyQt5.QtWidgets import (
    QWidget,
)
from PyQt5.QtGui import (
    QPainter,
)
from PyQt5.QtCore import QRect, Qt
from ..formlib.widgets import EditableTextWidget
from .const_color import Col
from ..formlib.layouts import RowLayout, ColLayout

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
        self.default_setting()
        self.listener = listener

        self.widget_row = [
            KeyGroup(TYPE_ROW, i, self, str(i), "test")
            for i in range(KEY_NUMBER)
        ]
        self.widget_col = [
            KeyGroup(TYPE_COL, i, self, str(i), "test")
            for i in range(KEY_NUMBER)
        ]
        self.rowkeytext = KeyGroup(TYPE_KEY, 0, None, text=self.row_title)
        self.rowkeytext.set_visible(False, True, False)
        self.colkeytext = KeyGroup(TYPE_KEY, 0, None, text=self.col_title)
        self.colkeytext.set_visible(False, True, False)

        base = RowLayout(self)
        base.setSpacing(0)
        base.addWidget(self.rowkeytext)
        for i in range(KEY_NUMBER):
            base.addWidget(self.widget_row[i])
        base.addWidget(self.colkeytext)
        for i in range(KEY_NUMBER):
            base.addWidget(self.widget_col[i])
        base.addStretch()
        self.setting_update()

    def setting_update(self):
        self.rowkeytext.set_font(self.row_title_size)
        self.colkeytext.set_font(self.col_title_size)
        key = self.key_name_length
        text = 200
        answer = 100
        for i in range(KEY_NUMBER):
            self.widget_row[i].set_font(self.row_key_size)
            self.widget_row[i].set_min_size(key, text, answer)
            self.widget_col[i].set_font(self.col_key_size)
            self.widget_col[i].set_min_size(key, text, answer)

    def default_setting(self):
        self.row_title = "タテのカギ"
        self.row_title_size = 20
        self.row_key_size = 16
        self.col_title = "ヨコのカギ"
        self.col_title_size = 20
        self.col_key_size = 16
        self.key_name_length = 30

    def update(self, row_open_list, col_open_list):
        for i in range(KEY_NUMBER):
            self.widget_row[i].set_all_visible(i in row_open_list)
            self.widget_col[i].set_all_visible(i in col_open_list)

    def save(self):
        save_data = {}
        save_data[STR_ROW_KEY_TITLE] = self.row_title
        save_data[STR_ROW_KEY_TITLE_SIZE] = self.row_title_size
        rows = [keys.get_text() for keys in self.widget_row]
        save_data[STR_ROW_KEY] = rows
        save_data[STR_ROW_KEY_SIZE] = self.row_key_size
        save_data[STR_COL_KEY_TITLE] = self.col_title
        save_data[STR_COL_KEY_TITLE_SIZE] = self.col_title_size
        cols = [keys.get_text() for keys in self.widget_col]
        save_data[STR_COL_KEY] = cols
        save_data[STR_COL_KEY_SIZE] = self.col_key_size
        save_data[KEY_NAME_LENGTH] = self.key_name_length
        return save_data

    def load(self, load_data):
        self.row_title = load_data[STR_ROW_KEY_TITLE]
        self.row_title_size = load_data[STR_ROW_KEY_TITLE_SIZE]
        row_key = load_data[STR_ROW_KEY]
        for i in range(KEY_NUMBER):
            self.widget_row[i].set_text(*row_key[i])
        self.row_key_size = load_data[STR_ROW_KEY_SIZE]
        self.col_title = load_data[STR_COL_KEY_TITLE]
        self.col_title_size = load_data[STR_COL_KEY_TITLE_SIZE]
        col_key = load_data[STR_COL_KEY]
        for i in range(KEY_NUMBER):
            self.widget_col[i].set_text(*col_key[i])
        self.col_key_size = load_data[STR_COL_KEY_SIZE]
        self.key_name_length = load_data[KEY_NAME_LENGTH]

        self.setting_update()

    def get_visible_list(self):
        ret = []
        ret.append(self.rowkeytext)
        for kg in self.widget_row:
            if kg.is_visible:
                ret.append(kg)
        ret.append(self.colkeytext)
        for kg in self.widget_col:
            if kg.is_visible:
                ret.append(kg)
        return ret

    def show_setting(self, black, key, text, answer) -> None:
        for kg in [self.rowkeytext, self.colkeytext]:
            kg.set_black(black)
            kg.set_visible(False, True, False)
        for kg in self.widget_row + self.widget_col:
            kg.set_black(black)
            kg.set_visible(key, text, answer)

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

    def __init__(self, text="", listner=None, col=Col.black):
        super().__init__(text, listner, col)
        self.data = []
        self.black = 0
        self.del_ghost()

    def set_black(self, black):
        # 黒塗りするなら1
        self.black = black

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

    def get_square(self):
        return self.data

    def remove_square(self, square):
        if square in self.data:
            self.data.remove(square)
            self.update()

    def square_exchange(self, square):
        # font = self.label.font()
        # fm = QFontMetrics(font)
        # w = fm.averageCharWidth()
        if self.label.text() != "":
            w = self.label.width() / len(self.label.text())
        else:
            w = 0
        h = self.label.height()

        x1 = max(0, int(w * square[0][0] / 10))
        x2 = min(self.label.width(), int(w * square[0][1] / 10))
        y1 = max(0, int(h * square[1][0] / 10))
        y2 = min(h, int(h * square[1][1] / 10))
        # print(square, w, h, x1, x2, y1, y2)
        return [x1, y1, x2, y2]

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.black:
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
        ret.set_black(self.black)
        for square in self.get_square():
            ret.add_square(square)
        return ret


class KeyGroup(QWidget):
    """
    カギ一個分(カギ名、指示、回答)
    """

    def __init__(self, tp, num, listener=None, keyname="", text="", answer=""):
        super().__init__()
        self.tp = tp
        self.num = num
        self.is_visible = True
        self.listener = listener
        self.base = ColLayout(self)
        self.keyname = BlackOutText(keyname)
        self.text = BlackOutText(text)
        self.answer = EditableTextWidget(answer, self)
        self.widgets: list[QWidget] = [self.keyname, self.text, self.answer]

        for key in self.widgets:
            self.base.addWidget(key)

    def set_text(self, keyname="", text="", answer=""):
        for w, v in zip(self.widgets, [keyname, text, answer]):
            w.set_text(v)

    def set_font(self, font_size):
        for w in self.widgets:
            w.set_font(font_size)

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

    def set_min_size(self, key, text, answer):
        for w, v in zip(self.widgets, [key, text, answer]):
            w.set_minimum_length(v)

    def set_black(self, black):
        self.keyname.set_black(black)
        self.text.set_black(black)

    # def clone(self):
    #     kg = KeyGroup(
    #         self.tp,
    #         self.num,
    #         self.listener,
    #         self.keyname.get_text(),
    #         self.text.get_text(),
    #         self.answer.get_text()
    #     )
    #     kg.keyname.set

    #     return kg

    def notify(self, text):
        if self.listener:
            self.listener.notify(self.tp, self.num, text)
