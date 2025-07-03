from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QStackedWidget,
    QPushButton,
    QWidget,
    QListWidget,
)
from PyQt5.QtCore import pyqtSignal

from ..formlib.widgets import SquareSetter
from ..formlib.layouts import RowLayout, ColLayout
from .wid_key import KeyGroup, BlackOutText


class BlackPanelForm(QDialog):
    # このシグナルで文字列を親に送信できる
    submitted = pyqtSignal(str)

    def __init__(self, kg_list: list[KeyGroup], parent=None):
        super().__init__(parent)
        self.setWindowTitle("黒塗り設定")
        self.resize(1000, 600)

        if kg_list == []:
            return
        base = ColLayout(self)

        main_panel = QWidget()
        lay = RowLayout(main_panel)
        key_list = QListWidget()
        base.addWidget(main_panel)
        base.addWidget(key_list)

        stack = QStackedWidget()
        for kg in kg_list:
            kd = KeyData(kg)
            key_list.addItem(kd.text())

            page = BlackEditor(kg)
            stack.addWidget(page)

        lay.addWidget(stack)
        self.op = OperatorPanel(kg_list[0], self)
        lay.addWidget(self.op)

        key_list.currentRowChanged.connect(stack.setCurrentIndex)
        key_list.currentRowChanged.connect(self.row_changed)

        self.kg_list = kg_list
        self.stack = stack

    def row_changed(self):
        kg = self.kg_list[self.stack.currentIndex()]
        self.op.set_kg(kg)

    def on_send(self):
        text = self.input.text()
        self.submitted.emit(text)

    def on_end(self):
        # モーダルなら accept()、モデルレスなら close()
        self.accept()


class OperatorPanel(QWidget):
    def __init__(self, kg: KeyGroup, parent: BlackPanelForm):
        super().__init__()
        self.p = parent

        base = ColLayout(self)

        self.key_op = BlackOperation(kg.keyname, "カギ番号：")
        self.text_op = BlackOperation(kg.text, "問題文：")

        base.addWidget(self.key_op)
        base.addWidget(self.text_op)

        if kg.keyname.get_text() == "":
            self.key_op.hide()

        # btn_end = QPushButton("終了", self)
        # btn_end.clicked.connect(self.on_end)
        # base.addWidget(btn_end)

    def set_kg(self, kg: KeyGroup):
        self.key_op.set_bk(kg.keyname)
        self.text_op.set_bk(kg.text)

        if kg.keyname.get_text() == "":
            self.key_op.hide()
        else:
            self.key_op.show()

    def on_end(self):
        self.p.on_end()


class BlackOperation(QWidget):
    def __init__(self, bk: BlackOutText, txt: str):
        super().__init__()
        self.bk = bk
        base = RowLayout(self)
        valid = [0, 100, 4]
        label = QLabel(self)
        label.setText(txt)
        self.setter = SquareSetter(self, valid, valid)

        edit = QWidget()
        el = ColLayout(edit)
        half_btn = QPushButton("半分")
        half_btn.clicked.connect(self.on_half_btn)
        all_btn = QPushButton("全部")
        all_btn.clicked.connect(self.on_all_btn)
        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self.on_add_btn)
        el.addWidget(half_btn)
        el.addWidget(all_btn)
        el.addWidget(add_btn)

        self.bl = BlackList()
        remove_btn = QPushButton("削除")
        remove_btn.clicked.connect(self.on_remove_btn)

        base.addWidget(label)
        base.addWidget(self.setter)
        base.addWidget(edit)
        base.addWidget(self.bl)
        base.addWidget(remove_btn)

    def set_bk(self, bk: BlackOutText):
        self.bk = bk
        ghost = bk.ghost
        self.setter.set_square(ghost)
        self.bl.set_item(self.bk.get_square())

    def on_add_btn(self):
        square = self.setter.get_square()
        ret = self.bl.add_item(square)
        if ret:
            self.bk.add_square(square)
        self.bk.del_ghost()

    def on_half_btn(self):
        h = 10.0
        w = len(self.bk.get_text()) * 5
        square = [[0.0, w], [0.0, h]]
        self.setter.set_square(square)

    def on_all_btn(self):
        h = 10.0
        w = len(self.bk.get_text()) * 10
        square = [[0.0, w], [0.0, h]]
        self.setter.set_square(square)

    def on_remove_btn(self):
        ret = self.bl.pop_selected_item()
        self.bk.remove_square(ret)

    def notify(self):
        ans = self.setter.get_square()
        self.bk.set_ghost(ans)


class BlackList(QListWidget):
    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.clear()
        self.addItem("")
        self.list = [[[0.0, 0.0], [0.0, 0.0]]]

    def pop_selected_item(self):
        n = self.currentRow()
        if n == len(self.list) - 1:
            return [[0.0, 0.0], [0.0, 0.0]]
        self.takeItem(n)
        return self.list.pop(n)

    def set_item(self, square_list):
        self.init()
        for square in square_list:
            self.add_item(square)

    def add_item(self, square):
        if square in self.list:
            return False
        s = (
            str(square[0][0])
            + ","
            + str(square[0][1])
            + ","
            + str(square[1][0])
            + ","
            + str(square[1][1])
        )
        self.list.insert(0, square)
        self.insertItem(0, s)
        return True


class BlackEditor(QWidget):
    def __init__(self, kg: KeyGroup):
        super().__init__()
        self.kg = kg
        self.keyname = BlackOutText(kg.keyname.get_text())
        self.textstr = BlackOutText(kg.text.get_text())
        self.keyname.add_squares(kg.keyname.get_square())
        self.textstr.add_squares(kg.text.get_square())
        self.keyname.set_font(kg.keyname.get_font())
        self.textstr.set_font(kg.text.get_font())
        self.keyname.set_black(1)
        self.textstr.set_black(1)

        base = ColLayout(self)
        if self.keyname.get_text() != "":
            base.addWidget(self.keyname)
        base.addWidget(self.textstr)


class KeyData(QLabel):
    def __init__(self, kg: KeyGroup):
        super().__init__()
        num = kg.keyname.get_text()
        text = kg.text.get_text()
        if num != "":
            disp = num + " " + text[:5]
        else:
            disp = text[:5]

        self.setText(disp)
