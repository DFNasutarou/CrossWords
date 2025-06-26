# widgets.py
from PyQt5.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QScrollArea, QWidget, QGridLayout, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from .formlib import WidgetMaker

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
    def __init__(self, widget, width = 100, resizable = True):
        super().__init__()
        self.setWidgetResizable(resizable)
        self.setWidget(widget)
        self.setFixedWidth(width)

class CellMaker(WidgetMaker):
    """
    セルグリッドを一括生成するWidgetMaker。
    正方形サイズ n x n (4 <= n <= 9) を受け取り、CellWidget を敷き詰めた QWidget を返します。
    """
    def __init__(self, n, cell_size=40):
        if not (4 <= n <= 9):
            raise ValueError('サイズは4～9の範囲で指定してください')
        self.n = n
        self.cell_size = cell_size
        self.all_size = n * cell_size

    def make(self):
        parent = QWidget()
        layout = QGridLayout(parent)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        parent.setFixedSize(self.all_size, self.all_size) 

        for r in range(self.n):
            for c in range(self.n):
                w = CellWidget(r, c, size=self.cell_size)
                layout.addWidget(w, r, c)
        return parent

class CellWidget(QPushButton):
    """
    クロスワードのセル：クリックで状態を切り替え（0: 白, 1: 黒, 2: 二重四角）。
    """
    def __init__(self, row, col, size = 40, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.state = 0
        self.setFixedSize(size, size)
        self.clicked.connect(self.toggle_state)

    def toggle_state(self):
        self.state = (self.state + 1) % 3
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.state == 1:
            self.setStyleSheet('background-color: black')
        else:
            self.setStyleSheet('background-color: white')
        # if self.state == 2:
        #     # 二重四角を描画
        #     painter = QPainter(self)
        #     pen = QPen(Qt.black, 2)
        #     painter.setPen(pen)
        #     rect = self.rect().adjusted(4,4,-4,-4)
        #     painter.drawRect(rect)
        #     painter.end()

class InstructionBar(WidgetMaker):
    """
    上部の最終指示表示用ラベル。
    """
    def __init__(self, text, font_size = 20, size = [200, 28]):
        super().__init__(size)
        self.widget = QLabel()
        self.widget.setText(text)
        self.widget.setAlignment(Qt.AlignCenter)
        self.widget.setFixedHeight(self.size[1])

        font = QFont()
        font.setPointSize(font_size)
        self.widget.setFont(font)
    def make(self):# -> Any:
        return self.widget

class EditableTextWidget(QWidget):
    """
    クリックするとテキスト入力可能になるウィジェット。
    ラベル表示から QLineEdit に切り替えて編集できる。
    """
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.label = QLabel(text, self)
        self.edit = QLineEdit(text, self)
        self.edit.hide()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.edit)
        # クリックで編集開始
        self.label.mousePressEvent = self._start_edit
        # 編集完了でラベルに反映
        self.edit.editingFinished.connect(self._finish_edit)

        font = QFont()
        font.setPointSize(20)
        self.label.setFont(font)
    def _start_edit(self, event):
        self.label.hide()
        self.edit.show()
        self.edit.setFocus()

    def _finish_edit(self):
        text = self.edit.text()
        self.label.setText(text)
        self.edit.hide()
        self.label.show()

class TextInputMaker(WidgetMaker):
    """
    EditableTextWidget を作るMaker。
    初期テキストを受け取り入力可能テキストを返す。
    """
    def __init__(self, text=''):
        self.text = text
    def make(self):
        return EditableTextWidget(self.text)


class ClueEditor(QTableWidget):
    """
    カギ編集用テーブル：番号／テキスト列。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['番号', 'カギ'])
        self.verticalHeader().setVisible(False)

    def load_from_file(self, path):
        with open(path, encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]
        self.setRowCount(len(lines))
        for i, line in enumerate(lines):
            num, clue = line.split(':',1)
            self.setItem(i, 0, QTableWidgetItem(num))
            self.setItem(i, 1, QTableWidgetItem(clue))

    def save_to_file(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            for r in range(self.rowCount()):
                num = self.item(r,0).text()
                clue = self.item(r,1).text()
                f.write(f"{num}:{clue}\n")