# widgets.py
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)
from ..formlib.widgets import EditableTextWidget
from .const_color import Col

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
        self.rowkeytext = BlackOutText(self.row_title)
        self.colkeytext = BlackOutText(self.col_title)

        base = QVBoxLayout(self)
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
        for i in range(KEY_NUMBER):
            self.widget_row[i].set_font(self.row_key_size)
            self.widget_row[i].set_key_length(self.key_name_length)
            self.widget_col[i].set_font(self.col_key_size)
            self.widget_col[i].set_key_length(self.key_name_length)

    def default_setting(self):
        self.row_title = "タテのカギ"
        self.row_title_size = 20
        self.row_key_size = 16
        self.col_title = "ヨコのカギ"
        self.col_title_size = 20
        self.col_key_size = 16
        self.key_name_length = 20

    def update(self, row_open_list, col_open_list):
        for i in range(KEY_NUMBER):
            if i in row_open_list:
                self.widget_row[i].show()
            else:
                self.widget_row[i].hide()
            if i in col_open_list:
                self.widget_col[i].show()
            else:
                self.widget_col[i].hide()

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

    def notify(self, tp, num, text):
        if tp == TYPE_ROW:
            event = 2
        elif tp == TYPE_COL:
            event = 3
        self.listener.notify(event, [num, text])


class BlackOutText(EditableTextWidget):
    """
    黒塗り可能なテキスト
    """

    def __init__(self, text="", listner=None, col=Col.black):
        super().__init__(text, listner, col)

    def set_length(self, len):
        self.setFixedWidth(len)


class KeyGroup(QWidget):
    """
    カギ一個分(カギ名、指示、回答)
    """

    def __init__(self, tp, num, listner=None, keyname="", text="", answer=""):
        super().__init__()
        self.tp = tp
        self.num = num
        self.listner = listner
        self.base = QHBoxLayout(self)
        self.keyname = BlackOutText(keyname)
        self.text = BlackOutText(text)
        self.answer = BlackOutText(answer, self)
        self.base.addWidget(self.keyname)
        self.base.addWidget(self.text)
        self.base.addWidget(self.answer)

        self.base.setContentsMargins(0, 0, 0, 0)
        self.base.setSpacing(0)

    def set_text(self, keyname="", text="", answer=""):
        self.keyname.set_text(keyname)
        self.text.set_text(text)
        self.answer.set_text(answer)

    def set_font(self, font_size):
        self.keyname.set_font(font_size)
        self.text.set_font(font_size)
        self.answer.set_font(font_size)

    def set_key_length(self, len):
        self.keyname.set_length(len)

    def get_text(self):
        data = []
        data.append(self.keyname.get_text())
        data.append(self.text.get_text())
        data.append(self.answer.get_text())
        return data

    def notify(self, text):
        if self.listner:
            self.listner.notify(self.tp, self.num, text)
