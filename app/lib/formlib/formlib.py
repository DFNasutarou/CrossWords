# formlib.py
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QAction,
    QGridLayout,
    QVBoxLayout,
    QBoxLayout,
    QApplication,
    QWidget,
    QVBoxLayout,
    QMenu,
    QLayout,
)

PICTURE_FOLDER_NAME = "picture"
DATA_FILE_NAME = "data.json"

event_list = {}


class ApplicationNotify:
    menu_dict: dict[str, list[str]] = {}

    def notify(self, menu, sub):
        pass

    # class WidgetTree:
    def __init__(self):
        # ルートコンテナ生成
        root_widget = QWidget()
        layout = QVBoxLayout(root_widget)
        layout.setSpacing(0)
        size = (100, 100)
        self.root = WidgetTree.Node(size, root_widget)

    class Node:
        def __init__(self, size, widget: QWidget):
            self.size = size  # size: コンテナの場合 (rows, cols)
            self.widget = widget  # QWidget
            self.children = []  # 追加された子ノード

        def add(self, path, size, widget: QWidget):
            if path:
                idx = path.pop()
                return self.children[idx].add(path, size, widget)

            # 子を生成し、適切にレイアウトに追加
            child = widget
            layout = self.widget.layout()
            # QGridLayout なら自動セル配置
            if isinstance(layout, QGridLayout):
                rows, cols = self.size
                idx = len(self.children)
                r = idx // cols
                c = idx % cols
                layout.addWidget(child, r, c)
            elif isinstance(layout, QBoxLayout):
                layout.addWidget(child)
            # 子ノードとして保持
            self.children.append(MainWindow.Node(size, child))
            return

    def add(self, path, widget: QWidget, size=-1):
        # パスを逆順にして渡す
        return
        widget = self.root.add(list(path)[::-1], size, widget)
        return widget


class MainWindow(QMainWindow):

    def __init__(self, size):
        super().__init__()
        self.setWindowTitle("フォーム")
        # self.setFixedSize(size[0], size[1])

    def set_widget(self, widget: QWidget):
        # ルートコンテナ生成
        self.setCentralWidget(widget)
        lay = self.layout()
        if lay:
            lay.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def _selected_menu(self, action: QAction):
        if not self.notify:
            return
        menu = self.sender()
        if isinstance(menu, QMenu):
            self.notify.notify(menu.title(), action.text())

    def init_menu(self, notify: ApplicationNotify):
        # メニューバー設定
        self.notify = notify
        menubar = self.menuBar()
        if not menubar:
            raise Exception
        for menu, value in self.notify.menu_dict.items():
            m = menubar.addMenu(menu)
            if not m:
                break
            m.triggered.connect(self._selected_menu)
            for v in value:
                m.addAction(v)


class Application:
    """
    QApplication を生成し、MainWindow を表示するラッパー。
    """

    def __init__(self, size):
        self.app = QApplication(sys.argv)
        # デフォルトサイズ 800x600
        self.window = MainWindow(size)

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())
