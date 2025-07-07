# widgets.py
from PyQt5.QtWidgets import (
    QLabel,
    QScrollArea,
    QWidget,
    QLineEdit,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import (
    QPixmap,
    QFont,
    QPalette,
    QPainter,
    QPen,
    QDoubleValidator,
    QColor,
)
from ..formlib.layouts import RowLayout, ColLayout


class WidgetSetting:
    MARGIN = "margin"
    SPACE = "space"
    SIZE = "size"
    WID = "width"

    def __init__(self, size, wid):
        self.data = {}
        self.data[WidgetSetting.MARGIN] = [0, 0, 0, 0]
        self.data[WidgetSetting.SPACE] = 0
        self.data[WidgetSetting.SIZE] = size
        self.data[WidgetSetting.WID] = wid

    def save(self):
        return self.data

    def load(self, data):
        for r, v in data.items():
            self.data[r] = v


class ClickableLabel(QLabel):
    """
    QLabel を継承し、クリック時に 'clicked' シグナルを発行するウィジェット。
    """

    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class TextWidget(ClickableLabel):
    """
    テキストを表示し、折り返しとクリック応答が可能。
    """

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)


class GraphicWidget(ClickableLabel):
    """
    画像を表示し、表示領域に合わせてアスペクト比を保ったリサイズとクリック応答が可能。
    """

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._original = pixmap
        self.setScaledContents(True)
        self.setPixmap(pixmap)

    def resizeEvent(self, event):
        # 元の pixmap を枠内の大きさに合わせてアスペクト比を保ちつつリサイズ
        if self._original:
            scaled = self._original.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled)
        super().resizeEvent(event)


class ScrollArea(QScrollArea):
    def __init__(self, widget, width=100, resizable=True):
        super().__init__()
        self.setWidgetResizable(resizable)
        self.setWidget(widget)
        self.setFixedWidth(width)


class RangeSetter(QWidget):
    def __init__(self, listener, valid: list[float] = [0, 100, 4]):
        super().__init__()
        base = ColLayout(self)
        self.lf = QLineEdit(self)
        self.rg = QLineEdit(self)
        self.lf.setText(str(valid[0]))
        self.rg.setText(str(valid[0]))
        self.lf.setFixedWidth(60)
        self.rg.setFixedWidth(60)
        self.lf.textChanged.connect(self.on_text_changed)
        self.rg.textChanged.connect(self.on_text_changed)
        txt = QLabel(self)
        txt.setText("～")
        base.addWidget(self.lf)
        base.addWidget(txt)
        base.addWidget(self.rg)
        self.listener = listener

        float_validator = QDoubleValidator(
            valid[0], valid[1], int(valid[2]), self
        )  # 小数点以下桁数も指定
        float_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.lf.setValidator(float_validator)
        self.rg.setValidator(float_validator)

        self.valid = valid

    def on_text_changed(self):
        self.listener.notify()

    def set_range(self, rng: list[float]):
        self.lf.setText(str(rng[0]))
        self.rg.setText(str(rng[1]))

    def get_range(self):
        s = self.lf.text()
        e = self.rg.text()
        try:
            s = float(s)
        except:
            s = self.valid[0]
        try:
            e = float(e)
        except:
            e = self.valid[1]
        return [s, e]


class SquareSetter(QWidget):
    def __init__(self, listener, validx, validy):
        super().__init__()
        base = RowLayout(self)
        self.xrange = RangeSetter(self, validx)
        self.yrange = RangeSetter(self, validy)
        width_txt = QLabel(self)
        width_txt.setText("幅")
        height_txt = QLabel(self)
        height_txt.setText("高さ")
        base.addWidget(width_txt)
        base.addWidget(self.xrange)
        base.addWidget(height_txt)
        base.addWidget(self.yrange)
        self.listener = listener

    def notify(self):
        self.listener.notify()

    def get_square(self):
        return [self.xrange.get_range(), self.yrange.get_range()]

    def set_square(self, square: list[list[float]]):
        self.xrange.set_range(square[0])
        self.yrange.set_range(square[1])


class EditableTextWidget(QWidget):
    """
    クリックするとテキスト入力可能になるウィジェット。
    ラベル表示から QLineEdit に切り替えて編集できる。
    """

    guaid = 1

    def __init__(self, text="", listner=None, col=Qt.black):
        super().__init__(None)
        self.listner = listner
        base = ColLayout(self)
        self.label = QLabel(text, self)
        self.edit = QLineEdit(text, self)
        self.edit.hide()
        base.addWidget(self.label)
        base.addWidget(self.edit)
        # クリックで編集開始
        self.label.mousePressEvent = self._start_edit
        # 編集完了でラベルに反映
        self.edit.editingFinished.connect(self._finish_edit)

        palette = self.label.palette()
        palette.setColor(QPalette.WindowText, col)
        self.label.setPalette(palette)

        self.edit.setStyleSheet(
            """
            /* 通常時 */
            QLineEdit {
                background-color: white;
                color: #eeeeee;
            }
            /* フォーカス（編集中）時 */
            QLineEdit:focus {
                background-color: white;  
                color: #eeeeee;          
            }
            """
        )

    def save(self):
        # 現在の情報を書き出す
        data = self.get_text()
        return data

    def load(self, data):
        # 情報を読み取る
        self.set_text(data)

    def get_text(self):
        return self.label.text()

    def set_text(self, text):
        self.label.setText(text)
        self.edit.setText(text)

    def set_font(self, font_size):
        font = QFont("MS Gothic", font_size)
        self.label.setFont(font)
        self.edit.setFont(font)

    def get_font(self):
        return self.label.font().pointSize()

    def paintEvent(self, event):
        super().paintEvent(event)
        if EditableTextWidget.guaid:
            painter = QPainter(self)
            pen = QPen(QColor("#999999"), 2)
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(0, 0, 0, 0))
            painter.end()

    def set_setAlignment(self, type):
        match type:
            case 4:
                self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            case 5:
                self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            case 6:
                self.label.setAlignment(Qt.AlignmentFlag.AlignRight)

    def set_minimum_length(self, width):
        self.label.setMinimumWidth(width)
        self.edit.setMinimumWidth(width)

    def _start_edit(self, event) -> None:
        self.label.hide()
        self.edit.show()
        self.edit.setFocus()

    def _finish_edit(self):
        text = self.edit.text()
        self.label.setText(text)
        self.edit.hide()
        self.label.show()
        if self.listner:
            self.listner.notify(text)
