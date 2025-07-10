from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QWidget,
)

from app.lib.formlib.layouts import RowLayout, ColLayout
from app.lib.formlib.widgets import WidgetSetting, QLineEdit


class FormatData:
    def __init__(self, title, key_title, key_set, key_text, key_answer, board):
        self.title = title
        self.key_title = key_title
        self.key_set = key_set
        self.key_text = key_text
        self.key_answer = key_answer
        self.board = board


class FormatWidget(QWidget):
    def __init__(self, format: WidgetSetting, parent=None):
        super().__init__(parent)
        base = ColLayout(self)
        self.font_size = Editter(
            "サイズ", str(format.data[WidgetSetting.SIZE])
        )
        mag = ",".join(map(str, format.data[WidgetSetting.MARGIN]))
        self.margin = Editter("マージン", mag)
        self.space = Editter("スペース", str(format.data[WidgetSetting.SPACE]))
        self.wid = Editter("幅最小値", str(format.data[WidgetSetting.WID]))
        self.font_color = Editter(
            "文字色", str(format.data[WidgetSetting.COLOR])
        )

        base.addWidget(self.font_size)
        base.addWidget(self.margin)
        base.addWidget(self.space)
        base.addWidget(self.wid)
        base.addWidget(self.font_color)

        self.format = format

    def notify(self):
        try:
            self.format.data[WidgetSetting.SIZE] = int(
                self.font_size.get_text()
            )
            mag = list(map(int, self.margin.get_text().split(",")))
            self.format.data[WidgetSetting.MARGIN] = mag
            self.format.data[WidgetSetting.SPACE] = int(self.space.get_text())
            self.format.data[WidgetSetting.WID] = int(self.wid.get_text())
            self.format.data[WidgetSetting.COLOR] = self.font_color.get_text()
        except:
            print("error")
            pass


class Editter(QWidget):
    def __init__(self, text, data):
        super().__init__()
        base = ColLayout(self)
        txt = QLabel(self)
        txt.setText(text)
        self.data = QLineEdit(self)
        self.data.setText(data)
        self.data.setFixedWidth(80)
        base.addWidget(txt)
        base.addWidget(self.data)

    def get_text(self):
        return self.data.text()


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
        key_title_txt.setText("キー種類（タテ/ヨコ）")
        self.key_title = FormatWidget(format.key_title)
        key_set_txt = QLabel(self)
        key_set_txt.setText("キー番号")
        self.key_set = FormatWidget(format.key_set)
        key_txt = QLabel(self)
        key_txt.setText("キーテキスト")
        self.key_txt = FormatWidget(format.key_text)
        key_answer = QLabel(self)
        key_answer.setText("答え")
        self.key_answer = FormatWidget(format.key_answer)
        board_txt = QLabel(self)
        board_txt.setText("ボード")
        self.board = FormatWidget(format.board)

        base.addWidget(title_txt)
        base.addWidget(self.title)
        base.addWidget(key_title_txt)
        base.addWidget(self.key_title)
        base.addWidget(key_set_txt)
        base.addWidget(self.key_set)
        base.addWidget(key_txt)
        base.addWidget(self.key_txt)
        base.addWidget(key_answer)
        base.addWidget(self.key_answer)
        base.addWidget(board_txt)
        base.addWidget(self.board)

    def closeEvent(self, event):
        self.title.notify()
        self.key_title.notify()
        self.key_set.notify()
        self.key_txt.notify()
        self.key_answer.notify()
        self.board.notify()
        super().closeEvent(event)  # これが内部で reject() を呼ぶ

    def on_end(self):
        # モーダルなら accept()、モデルレスなら close()
        self.accept()
