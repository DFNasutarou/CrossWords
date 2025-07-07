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


class KeyData:
    def __init__(self, keyname: BlackOutText, textstr: BlackOutText):
        super().__init__()
        text = textstr.get_text()
        disp = text[:5]

        if keyname != None:
            num = keyname.get_text()
            disp = num + " " + disp

        self.disp = disp
        self.keyname = keyname
        self.textstr = textstr

        self.exist_keyname = keyname != None

    @staticmethod
    def clone_key_data(kg: KeyGroup):
        if isinstance(kg, KeyGroup):
            keyname = KeyData.clone_blackout_text(kg.keyname)
            textstr = KeyData.clone_blackout_text(kg.text)
        else:
            keyname = None
            textstr: BlackOutText = KeyData.clone_blackout_text(kg)

        return KeyData(keyname, textstr)

    @staticmethod
    def clone_blackout_text(bt: BlackOutText) -> BlackOutText:
        nbt = BlackOutText(bt.get_text())
        nbt.add_squares(bt.get_square())
        nbt.set_font(bt.get_font())
        nbt.set_minimum_length(bt.minimumWidth())
        return nbt

    @staticmethod
    def copy_keydata_setting_to_keygroup(kg: KeyGroup, kd: "KeyData"):
        if isinstance(kg, KeyGroup):
            kg.keyname.reset_square(kd.keyname.get_square())
            kg.keyname.set_text(kd.keyname.get_text())
            kg.text.reset_square(kd.textstr.get_square())
            kg.text.set_text(kd.textstr.get_text())
        else:
            kg.reset_square(kd.textstr.get_square())
            kg.set_text(kd.textstr.get_text())


class BlackPanelForm(QDialog):
    # このシグナルで文字列を親に送信できる
    submitted = pyqtSignal(str)

    def __init__(self, kd_list: list[KeyData], parent=None):
        super().__init__(parent)
        self.setWindowTitle("黒塗り設定")
        self.resize(1000, 600)

        if kd_list == []:
            return
        base = ColLayout(self)

        main_panel = QWidget()
        lay = RowLayout(main_panel)
        key_list = QListWidget()
        base.addWidget(main_panel)
        base.addWidget(key_list)

        stack = QStackedWidget()
        for kd in kd_list:
            key_list.addItem(kd.disp)

            page = BlackEditor(kd)
            stack.addWidget(page)

        lay.addWidget(stack)
        self.op = OperatorPanel(kd_list[0], self)
        lay.addWidget(self.op)

        key_list.currentRowChanged.connect(stack.setCurrentIndex)
        key_list.currentRowChanged.connect(self.row_changed)

        self.stack = stack
        self.kd_list = kd_list

    def row_changed(self):
        kd = self.kd_list[self.stack.currentIndex()]
        self.op.set_kg(kd)

    def on_send(self):
        text = self.input.text()
        self.submitted.emit(text)

    def on_end(self):
        # モーダルなら accept()、モデルレスなら close()
        self.accept()


class OperatorPanel(QWidget):
    def __init__(self, kd: KeyData, parent: BlackPanelForm):
        super().__init__()
        self.p = parent

        base = ColLayout(self)

        self.key_op = BlackOperation(kd.keyname, "カギ番号：")
        self.text_op = BlackOperation(kd.textstr, "問題文：")

        base.addWidget(self.key_op)
        base.addWidget(self.text_op)

        if not kd.exist_keyname:
            self.key_op.hide()

    def set_kg(self, kd: KeyData):
        self.text_op.set_bk(kd.textstr)

        if kd.exist_keyname:
            self.key_op.set_bk(kd.keyname)
            self.key_op.show()
        else:
            self.key_op.hide()

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
    def __init__(self, kd: KeyData):
        super().__init__()

        base = ColLayout(self)
        if kd.exist_keyname:
            base.addWidget(kd.keyname)
        base.addWidget(kd.textstr)

        # self.kg = kg
