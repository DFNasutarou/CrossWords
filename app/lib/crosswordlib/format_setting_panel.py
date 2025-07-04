from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QWidget,
)

from ..formlib.layouts import RowLayout, ColLayout
from ..formlib.widgets import WidgetSetting, QLineEdit


class FormatData:
    def __init__(self, title, key_title, key_set, board):
        self.title = title
        self.key_title = key_title
        self.key_set = key_set
        self.board = board


class FormatWidget(QWidget):
    def __init__(self, format: WidgetSetting, parent=None):
        super().__init__(parent)
        base = ColLayout(self)
        font_txt = QLabel(self)
        font_txt.setText("サイズ")
        self.font_size = QLineEdit(self)
        self.font_size.setText(str(format.data[WidgetSetting.SIZE]))
        margine_txt = QLabel(self)
        margine_txt.setText("マージン")
        self.margin = QLineEdit(self)
        self.margin.setText(str(format.data[WidgetSetting.MARGIN]))
        space_txt = QLabel(self)
        space_txt.setText("スペース")
        self.space = QLineEdit(self)
        self.space.setText(str(format.data[WidgetSetting.SPACE]))

        base.addWidget(font_txt)
        base.addWidget(self.font_size)
        base.addWidget(margine_txt)
        base.addWidget(self.margin)
        base.addWidget(space_txt)
        base.addWidget(self.space)

        self.format = format

    def notify(self):
        try:
            self.format.data[WidgetSetting.SIZE] = int(self.font_size.text())
            self.format.data[WidgetSetting.MARGIN] = int(self.margin.text())
            self.format.data[WidgetSetting.SPACE] = int(self.space.text())
        except:
            pass


class FormatPanelForm(QDialog):
    def __init__(self, format: FormatData, parent=None):
        super().__init__(parent)
        self.setWindowTitle("フォーマット設定")
        self.resize(1000, 600)

        base = RowLayout(self)
        title_txt = QLabel(self)
        title_txt.setText("指示文")
        self.title = FormatWidget(format.title)
        key_title_txt = QLabel(self)
        key_title_txt.setText("キー名")
        self.key_title = FormatWidget(format.key_title)
        key_set_txt = QLabel(self)
        key_set_txt.setText("キー")
        self.key_set = FormatWidget(format.key_set)
        board_txt = QLabel(self)
        board_txt.setText("ボード")
        self.board = FormatWidget(format.board)

        base.addWidget(title_txt)
        base.addWidget(self.title)
        base.addWidget(key_title_txt)
        base.addWidget(self.key_title)
        base.addWidget(key_set_txt)
        base.addWidget(self.key_set)
        base.addWidget(board_txt)
        base.addWidget(self.board)

    def closeEvent(self, event):
        self.title.notify()
        self.key_title.notify()
        self.key_set.notify()
        self.board.notify()
        super().closeEvent(event)  # これが内部で reject() を呼ぶ

    def on_end(self):
        # モーダルなら accept()、モデルレスなら close()
        self.accept()
