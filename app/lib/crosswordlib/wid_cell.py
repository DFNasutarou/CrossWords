# widgets.py
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget,
    QGridLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter, QPen
from .const_color import Col


Cell_Default = -1
Cell_White = 0
Cell_Black = 1
Cell_Double = 2

BOARD_SIZE = "board_size"
GRID_DATA = "grid_data"
MAX_BOARD_SIZE = 30


class CellBoard(QWidget):
    """
    セルグリッドを一括管理するボード
    正方形サイズ n x n (4 <= n <= 9) を受け取り、CellWidget を敷き詰めた QWidget を返します。
    """

    def __init__(self, n: int, size, listener):
        super().__init__()
        if not (4 <= n <= 9):
            raise ValueError("サイズは4～9の範囲で指定してください")
        self.n = n
        self.widget: list[list[CellWidget]] = [
            [CellWidget(r, c, self) for c in range(MAX_BOARD_SIZE)]
            for r in range(MAX_BOARD_SIZE)
        ]
        # self.setFixedHeight(size)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for r in range(self.n):
            for c in range(self.n):
                layout.addWidget(self.widget[r][c], r, c)

        self.row_list = []
        self.col_list = []
        self.resize()

        self.listener = listener

    def resize(self):
        # 盤面の大きさに合わせてウィジェットの大きさを変える
        cell_size = self.height() // self.n
        all_size = self.n * cell_size
        for r in range(MAX_BOARD_SIZE):
            for c in range(MAX_BOARD_SIZE):
                self.widget[r][c].resize(cell_size)
                if r < self.n and c < self.n:
                    self.widget[r][c].show()
                else:
                    self.widget[r][c].hide()
        self.setFixedSize(all_size, all_size)

    def reset(self):
        # 盤面リセット
        num = 1
        self.row_list = []
        self.col_list = []
        self.row_pos: dict[int, tuple[int, int]] = {}
        self.col_pos: dict[int, tuple[int, int]] = {}
        for i in range(self.n):
            for j in range(self.n):
                self.widget[i][j].set_number(None)
                if self.widget[i][j].is_white():
                    row_pre = i == 0 or self.widget[i - 1][j].is_black()
                    row_sur = (
                        i == self.n - 1 or self.widget[i + 1][j].is_black()
                    )
                    col_pre = j == 0 or self.widget[i][j - 1].is_black()
                    col_sur = (
                        j == self.n - 1 or self.widget[i][j + 1].is_black()
                    )
                    if (row_pre and not row_sur) or (col_pre and not col_sur):
                        self.widget[i][j].set_number(num)
                        if row_pre and not row_sur:
                            self.row_list.append(num)
                            self.row_pos[num] = (i, j)
                        if col_pre and not col_sur:
                            self.col_list.append(num)
                            self.col_pos[num] = (i, j)
                        num += 1
                self.widget[i][j].update()

        self.listener.notify(1)

    def notify(self):
        self.reset()

    def save(self):
        save_data = {}
        save_data[BOARD_SIZE] = self.n
        save_data[GRID_DATA] = [
            [self.widget[r][c].get_state() for c in range(self.n)]
            for r in range(self.n)
        ]
        return save_data

    def load(self, load_data):
        self.n = load_data[BOARD_SIZE]
        grid = load_data[GRID_DATA]
        for r in range(self.n):
            for c in range(self.n):
                self.widget[r][c].set_state(grid[r][c])
        self.resize()
        self.reset()

    def get_num_list(self):
        return self.row_list, self.col_list

    def set_answer_row(self, num, text: str):
        if num not in self.row_pos:
            print("未知のエラー: row-", num)
        r, c = self.row_pos[num]
        st = list(text)[::-1]
        for i in range(r, self.n):
            if self.widget[i][c].is_black():
                return
            s = st.pop() if st else ""
            self.widget[i][c].set_char(s)

    def set_answer_col(self, num, text):
        if num not in self.col_pos:
            print("未知のエラー: col-", num)
            return
        r, c = self.row_pos[num]
        st = list(text)[::-1]
        for i in range(c, self.n):
            if self.widget[r][i].is_black():
                return
            s = st.pop() if st else ""
            self.widget[r][i].set_char(s)


class CellWidget(QPushButton):
    """
    クロスワードのセル：クリックで状態を切り替え（0: 白, 1: 黒, 2: 二重四角）。
    """

    def __init__(self, row, col, parent: QWidget, size=40):
        super().__init__()
        self.row = row
        self.col = col
        self.state = Cell_White
        self.setFixedSize(size, size)
        # self.clicked.connect(self.toggle_state)
        self.p = parent
        self.number = None
        self.c = ""

    def mousePressEvent(self, event):
        # --- 右クリックなら二重四角 ---
        if event.button() == Qt.RightButton:
            self.state = Cell_Double

        # --- 左クリックなら白⇔黒 ---
        elif event.button() == Qt.LeftButton:
            # 二重四角からでも「白」に戻したいなら以下のように
            if self.is_black():
                self.state = Cell_White
            else:
                self.state = Cell_Black

        else:
            # それ以外は通常動作
            return super().mousePressEvent(event)

        # 状態変更後の共通処理
        self.p.notify()  # 親に通知
        # self.update()     # paintEvent を呼び出す

    # def toggle_state(self):
    #     self.state = (self.state + 1) % 3
    #     self.p.notify()

    def paintEvent(self, event):
        super().paintEvent(event)
        # ペン設定
        painter = QPainter(self)
        pen = QPen(Col.black, 2)
        painter.setPen(pen)

        if self.is_black():
            painter.fillRect(self.rect(), Col.black)
            # self.setStyleSheet('background-color: black')
        elif self.is_white():
            painter.fillRect(self.rect(), Col.white)
            # self.setStyleSheet('background-color: white')

        painter.drawRect(self.rect().adjusted(0, 0, 0, 0))
        if self.state == Cell_Double:
            # 二重四角を描画
            rect = self.rect().adjusted(4, 4, -4, -4)
            painter.drawRect(rect)

        # 数字設定
        if self.number != None:
            font = QFont()
            font.setPointSize(20)
            painter.setFont(font)
            painter.drawText(2, 22, str(self.number))

        # 文字設定
        if self.c != "":
            font = QFont()
            font.setPointSize(70)
            painter.setFont(font)
            painter.drawText(10, 80, self.c)

        painter.end()

    def set_number(self, number):
        self.number = number

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def is_black(self):
        return self.state == Cell_Black

    def is_white(self):
        return not self.is_black()

    def resize(self, size):
        self.setFixedSize(size, size)

    def set_char(self, c):
        self.c = c
        self.update()
