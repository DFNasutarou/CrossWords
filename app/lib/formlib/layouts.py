# layouts.py
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QLayout
from PyQt5.QtCore import Qt


class ColLayout(QHBoxLayout):
    """
    水平コンテナ：子ウィジェットを横方向に並べます。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def set_setAlignment(self, type):
        match type:
            case 4:
                self.setAlignment(Qt.AlignmentFlag.AlignLeft)
            case 5:
                self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            case 6:
                self.setAlignment(Qt.AlignmentFlag.AlignRight)


class RowLayout(QVBoxLayout):
    """
    垂直コンテナ：子ウィジェットを縦方向に並べます。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def set_setAlignment(self, type):
        match type:
            case 4:
                self.setAlignment(Qt.AlignmentFlag.AlignLeft)
            case 5:
                self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            case 6:
                self.setAlignment(Qt.AlignmentFlag.AlignRight)


class TableLaout(QGridLayout):
    """
    グリッドコンテナ：子ウィジェットを表形式に配置します。
    size パラメータで (行数, 列数) を受け取り、セルを自動配置します。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def set_setAlignment(self, type):
        match type:
            case 4:
                self.setAlignment(Qt.AlignmentFlag.AlignLeft)
            case 5:
                self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            case 6:
                self.setAlignment(Qt.AlignmentFlag.AlignRight)
