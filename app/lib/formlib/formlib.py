# formlib.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QAction, QGridLayout
from PyQt5.QtCore import Qt

class WidgetMaker:
    """
    抽象ベース：make()でQWidgetを返す
    """
    def __init__(self, size = [-1, -1], mergin = [5, 5, 5, 5]):
        self.mergin = mergin
        self.size = size
    def make(self) -> QWidget:
        raise NotImplementedError
    def is_layout_widget(self):
        return False

class MainWindow(QMainWindow):
    class Node:
        def __init__(self, size, widget: QWidget):
            self.size = size            # size: コンテナの場合 (rows, cols)
            self.widget = widget        # QWidget
            self.children = []          # 追加された子ノード

        def add(self, path, size, maker: WidgetMaker):
            if not path:
                # 子を生成し、適切にレイアウトに追加
                child = maker.make()
                layout = self.widget.layout()
                # QGridLayout なら自動セル配置
                if isinstance(layout, QGridLayout):
                    rows, cols = self.size
                    idx = len(self.children)
                    r = idx // cols
                    c = idx % cols
                    layout.addWidget(child, r, c)
                else:
                    layout.addWidget(child)
                # 子ノードとして保持
                self.children.append(MainWindow.Node(size, child))
            else:
                idx = path.pop()
                self.children[idx].add(path, size, maker)

    def __init__(self, size, maker: WidgetMaker):
        super().__init__()
        self.setWindowTitle('クロスワード作成')
        self.setFixedSize(size[0], size[1])

        # ルートコンテナ生成
        root_widget = maker.make()
        self.root = MainWindow.Node(size, root_widget)

        # メニューバー設定
        self._init_menu()

        # 中央ウィジェットに設定
        self.setCentralWidget(root_widget)

    def _init_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('ファイル')
        exit_act = QAction('終了', self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

    def add(self, path, maker: WidgetMaker, size=-1):
        # パスを逆順にして渡す
        self.root.add(list(path)[::-1], size, maker)

class Application:
    """
    QApplication を生成し、MainWindow を表示するラッパー。
    """
    def __init__(self, maker: WidgetMaker):
        self.app = QApplication(sys.argv)
        # デフォルトサイズ 800x600
        self.window = MainWindow((800,600), maker)

    def add(self, path, maker: WidgetMaker, size=-1):
        self.window.add(path, maker, size)

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())