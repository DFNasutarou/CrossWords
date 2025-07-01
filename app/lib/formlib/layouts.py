# layouts.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout


class Row:
    """
    水平コンテナ：子ウィジェットを横方向に並べます。
    """

    def make(self):
        parent = QWidget()
        layout = QHBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        return parent


class Column:
    """
    垂直コンテナ：子ウィジェットを縦方向に並べます。
    """

    def make(self):
        parent = QWidget()
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        return parent


class Table:
    """
    グリッドコンテナ：子ウィジェットを表形式に配置します。
    size パラメータで (行数, 列数) を受け取り、セルを自動配置します。
    """

    def make(self):
        parent = QWidget()
        layout = QGridLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        return parent
