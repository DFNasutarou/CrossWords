# widgets.py
from PyQt5.QtWidgets import (
    QPushButton,
    QWidget,
    QLineEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter, QPen, QColor
from app.lib.formlib.layouts import TableLaout

Cell_Default = -1
Cell_White = 0
Cell_Black = 1
Cell_Double = 2

BOARD_SIZE = "board_size"
GRID_DATA = "grid_data"
MAX_BOARD_SIZE = 30
BOARD_TRANS = "board_trans"


class CellBoard(QWidget):
    """
    セルグリッドを一括管理するボード
    正方形サイズ n x n (4 <= n <= 9) を受け取り、CellWidget を敷き詰めた QWidget を返します。
    """

    def __init__(self, n: int, listener):
        super().__init__()
        if not (4 <= n <= 9):
            raise ValueError("サイズは4～9の範囲で指定してください")

        self.widget: list[list[CellWidget]] = [
            [CellWidget(r, c, self) for c in range(MAX_BOARD_SIZE)]
            for r in range(MAX_BOARD_SIZE)
        ]

        self.trans_board = 0
        self.board = TableLaout(self)
        self.set_board()

        self.row_list = []
        self.row_answer = []
        self.col_list = []
        self.col_answer = []
        self.resize(n)

        self.listener = listener

    def set_margine(self, margine=[0, 0, 0, 0], size=400):
        margine = [0, 0, 0, 0]
        self.board.setContentsMargins(*margine)
        self.setFixedHeight(size)
        self.resize(self.n)

    def resize(self, n):
        # 盤面の大きさに合わせてウィジェットの大きさを変える
        self.n = n

        cell_size = self.height() // self.n
        for r in range(MAX_BOARD_SIZE):
            for c in range(MAX_BOARD_SIZE):
                self.widget[r][c].resize(cell_size)
                if r < self.n and c < self.n:
                    self.widget[r][c].show()
                else:
                    self.widget[r][c].hide()

    def set_board(self):
        # 盤を配置
        for r in range(MAX_BOARD_SIZE):
            for c in range(MAX_BOARD_SIZE):
                w = self.widget[r][c]
                self.board.removeWidget(w)
                # w.setParent(None)
        if self.trans_board:
            for r in range(MAX_BOARD_SIZE):
                for c in range(MAX_BOARD_SIZE):
                    self.board.addWidget(self.widget[c][r], r, c)
        else:
            for r in range(MAX_BOARD_SIZE):
                for c in range(MAX_BOARD_SIZE):
                    self.board.addWidget(self.widget[r][c], r, c)

        self.update()

    def trans(self):
        self.trans_board = 1 - self.trans_board
        self.set_board()

    def reset(self):
        # 盤面リセット
        num = 1
        self.row_list = []
        self.row_answer = []
        self.col_list = []
        self.col_answer = []
        # self.row_pos: dict[int, tuple[int, int]] = {}
        # self.col_pos: dict[int, tuple[int, int]] = {}
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
                            txt = ""
                            n = i
                            while self.widget[n][j].is_white() and n < self.n:
                                if self.widget[n][j].c == "":
                                    txt += " "
                                else:
                                    txt += self.widget[n][j].c
                                n += 1
                            self.row_answer.append(txt)
                            # self.row_pos[num] = (i, j)
                        if col_pre and not col_sur:
                            self.col_list.append(num)
                            txt = ""
                            n = j
                            while self.widget[i][n].is_white() and n < self.n:
                                if self.widget[i][n].c == "":
                                    txt += " "
                                else:
                                    txt += self.widget[i][n].c
                                n += 1
                            self.col_answer.append(txt)
                            # self.col_pos[num] = (i, j)
                        num += 1
                self.widget[i][j].update()
        self.listener.notify(1)

    def notify(self):
        self.reset()

    def save(self):
        save_data = {}
        save_data[BOARD_SIZE] = self.n
        save_data[GRID_DATA] = [
            [self.widget[r][c].save() for c in range(self.n)]
            for r in range(self.n)
        ]
        save_data[BOARD_TRANS] = self.trans_board
        return save_data

    def load(self, load_data):
        n = load_data[BOARD_SIZE]
        grid = load_data[GRID_DATA]
        for r in range(n):
            for c in range(n):
                self.widget[r][c].load(grid[r][c])
        self.trans_board = load_data[BOARD_TRANS]
        self.resize(n)
        self.reset()
        self.set_board()

    def get_num_list(self):
        return self.row_list, self.col_list, self.row_answer, self.col_answer

    # def set_answer_row(self, num, text: str):
    #     if num not in self.row_pos:
    #         print("未知のエラー: row-", num)
    #     r, c = self.row_pos[num]
    #     st = list(text)[::-1]
    #     for i in range(r, self.n):
    #         if self.widget[i][c].is_black():
    #             return
    #         s = st.pop() if st else ""
    #         self.widget[i][c].set_char(s)

    # def set_answer_col(self, num, text):
    #     if num not in self.col_pos:
    #         print("未知のエラー: col-", num)
    #         return
    #     r, c = self.col_pos[num]
    #     st = list(text)[::-1]
    #     for i in range(c, self.n):
    #         if self.widget[r][i].is_black():
    #             return
    #         s = st.pop() if st else ""
    #         self.widget[r][i].set_char(s)

    def set_board_color(self, col):
        CellWidget.board_col = col

    def board_black(self, is_black):
        CellWidget.board_black = is_black

    def board_number(self, is_number_show):
        CellWidget.board_number_show = is_number_show

    def board_text(self, is_text_show):
        CellWidget.board_text_show = is_text_show


class CellWidget(QPushButton):
    """
    クロスワードのセル：クリックで状態を切り替え（0: 白, 1: 黒, 2: 二重四角）。
    """

    board_black = 0
    board_number_show = 1
    board_text_show = 1
    board_col = "#000000"
    state_num = 2

    STATE = "state"
    CHARACTOR = "charactor"

    def __init__(self, row, col, parent: QWidget, size=40) -> None:
        super().__init__()
        self.row = row
        self.col = col
        self.state = Cell_White
        self.setFixedSize(size, size)
        # self.clicked.connect(self.toggle_state)
        self.p = parent
        self.number = None
        self.c = ""

        self.square_par = 8
        self.number_par = 20
        self.char_par = 60

    def mousePressEvent(self, event):
        # --- 右クリックなら編集モード ---
        if event.button() == Qt.MouseButton.RightButton:
            font = QFont()
            n = self.height() * 0.5
            font.setPointSize(int(n))
            editor = QLineEdit(self)
            editor.setFrame(False)
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            editor.setText(self.c)
            editor.setFont(font)
            editor.setGeometry(self.rect())
            editor.show()
            editor.setFocus()

            def finish_edit():
                txt = editor.text()
                self.set_char(txt[:1])  # 先頭１文字だけ
                editor.deleteLater()
                self.p.notify()  # 親に通知

            # Enter キーかフォーカスが外れたら確定
            editor.returnPressed.connect(finish_edit)
            editor.editingFinished.connect(finish_edit)

        # --- 左クリックなら白⇔黒 ---
        elif event.button() == Qt.MouseButton.LeftButton:
            self.state = (self.state + 1) % CellWidget.state_num

        else:
            # それ以外は通常動作
            return super().mousePressEvent(event)

        # 状態変更後の共通処理
        self.p.notify()  # 親に通知

    def paintEvent(self, event):
        super().paintEvent(event)
        # ペン設定
        painter = QPainter(self)
        pen = QPen(QColor(CellWidget.board_col), 2)
        painter.setPen(pen)

        if self.is_black():
            painter.fillRect(self.rect(), QColor(CellWidget.board_col))
            # self.setStyleSheet('background-color: black')
        elif self.is_white():
            painter.fillRect(self.rect(), QColor("#ffffff"))
            # self.setStyleSheet('background-color: white')

            painter.drawRect(self.rect().adjusted(0, 0, 0, 0))
            if self.state == Cell_Double:
                # 二重四角を描画
                n = self.height() * self.square_par // 100
                n = max(n, 1)
                rect = self.rect().adjusted(n, n, -n, -n)
                painter.drawRect(rect)

            # 数字設定
            if self.number != None and CellWidget.board_number_show:
                font = QFont()
                n = self.height() * self.number_par // 100
                font.setPointSize(n)
                painter.setFont(font)
                painter.drawText(2, n + 2, str(self.number))

            # 文字設定
            if self.c != "" and CellWidget.board_text_show:
                font = QFont()
                n = self.height() * self.char_par // 100
                font.setPointSize(n)
                painter.setFont(font)
                painter.drawText(
                    self.rect().adjusted(4, 4, 4, 4),
                    Qt.AlignmentFlag.AlignCenter,
                    self.c,
                )

        painter.end()

    def set_number(self, number):
        self.number = number

    # def get_state(self):
    #     return self.state

    def set_state(self, state):
        self.state = state

    def is_black(self):
        if CellWidget.board_black:
            return True
        return self.state == Cell_Black

    def is_white(self):
        return not self.is_black()

    def resize(self, size):
        self.setFixedSize(size, size)

    def set_char(self, c):
        self.c = c
        self.update()

    def change_state_num(self):
        if CellWidget.state_num == 2:
            CellWidget.state_num = 3
        else:
            CellWidget.state_num = 2

    def save(self):
        data = {}
        data[CellWidget.STATE] = self.state
        data[CellWidget.CHARACTOR] = self.c
        return data

    def load(self, data):
        self.state = data[CellWidget.STATE]
        self.c = data[CellWidget.CHARACTOR]
