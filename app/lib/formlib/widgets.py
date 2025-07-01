# widgets.py
from PyQt5.QtWidgets import (
    QLabel,
    QScrollArea,
    QWidget,
    QHBoxLayout,
    QLineEdit,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QPalette, QPainter, QPen, QColor


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


class EditableTextWidget(QWidget):
    """
    クリックするとテキスト入力可能になるウィジェット。
    ラベル表示から QLineEdit に切り替えて編集できる。
    """

    def __init__(self, text="", listner=None, col=Qt.black):
        super().__init__(None)
        self.listner = listner
        base = QHBoxLayout(self)
        base.setContentsMargins(0, 0, 0, 0)
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

    def get_text(self):
        return self.label.text()

    def set_text(self, text):
        self.label.setText(text)
        self.edit.setText(text)

    def set_font(self, font_size):
        font = QFont()
        font.setPointSize(font_size)
        self.label.setFont(font)
        self.edit.setFont(font)

    def paintEvent(self, event):
        super().paintEvent(event)
        # ペン設定
        painter = QPainter(self)
        pen = QPen(QColor("#999999"), 2)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(0, 0, 0, 0))
        painter.end()

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
