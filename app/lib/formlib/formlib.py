# formlib.py
import os
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QAction,
    QGridLayout,
    QVBoxLayout,
    QBoxLayout,
)
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QInputDialog,
)

from .jsonio import JsonFileBuilder

PICTURE_FOLDER_NNAME = "picture"
DATA_FILE_NAME = "data.json"


class ApplicationNotify:
    def init_data(self, data):
        pass

    def save(self):
        pass

    def load(self, data):
        pass

    def new_project(self):
        pass


class MainWindow(QMainWindow):
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
            return child

    def __init__(self, size, notify: ApplicationNotify):
        super().__init__()
        self.setWindowTitle("フォーム")
        self.setFixedSize(size[0], size[1])
        self.notify = notify

        # ルートコンテナ生成
        root_widget = QWidget()
        layout = QVBoxLayout(root_widget)
        layout.setSpacing(0)
        self.root = MainWindow.Node(size, root_widget)

        palette = root_widget.palette()
        palette.setColor(QPalette.Window, Qt.white)  # RGB値で指定
        root_widget.setAutoFillBackground(True)
        root_widget.setPalette(palette)

        # メニューバー設定
        self._init_menu()

        # 中央ウィジェットに設定
        self.setCentralWidget(root_widget)

    def _init_menu(self):
        menubar = self.menuBar()
        if not menubar:
            raise Exception
        file_menu = menubar.addMenu("ファイル")
        if not file_menu:
            raise Exception

        prj_act = QAction("新規プロジェクト", self)
        prj_act.triggered.connect(self.notify.new_project)
        file_menu.addAction(prj_act)

        save_act = QAction("ファイル保存", self)
        save_act.triggered.connect(self.notify.save)
        file_menu.addAction(save_act)

        load_act = QAction("ファイル読み込み", self)
        load_act.triggered.connect(self.notify.load)
        file_menu.addAction(load_act)

        exit_act = QAction("終了", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

    def add(self, path, widget: QWidget, size=-1):
        # パスを逆順にして渡す
        widget = self.root.add(list(path)[::-1], size, widget)
        return widget


class WorkSpace:
    def make_workspace(self, data, path="~"):
        # selected_dir = QFileDialog.getExistingDirectory(
        #     None,
        #     "ベースとなるフォルダを選択",
        #     os.path.expanduser(path),  # 初期表示はホーム
        #     QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        # )
        # if not selected_dir:
        #     return

        folder_name, ok = QInputDialog.getText(
            None,
            "新規フォルダ名を指定",
            "作成するフォルダ名を入力してください：",
        )
        if not ok or not folder_name.strip():
            return  # キャンセルまたは空文字

        target_dir = os.path.join(path, folder_name.strip())
        picture_dir = os.path.join(target_dir, PICTURE_FOLDER_NNAME)
        try:
            os.makedirs(target_dir, exist_ok=False)
            os.makedirs(picture_dir, exist_ok=False)
        except OSError as e:
            QMessageBox.critical(
                None, "エラー", f"フォルダ作成に失敗しました:\n{e}"
            )
            return

        # ⑤ JSON ファイルを書き出し
        json_path = os.path.join(target_dir, DATA_FILE_NAME)
        builder = JsonFileBuilder()
        builder.add("data", data)
        builder.save(json_path)

        QMessageBox.information(
            None, "完了", f"プロジェクトを作成しました：\n{target_dir}"
        )

        return target_dir


class Application:
    """
    QApplication を生成し、MainWindow を表示するラッパー。
    """

    def __init__(self, size, notify: ApplicationNotify):
        self.app = QApplication(sys.argv)
        # デフォルトサイズ 800x600
        self.window = MainWindow(size, notify)

        # 初期設定ファイル読み込み
        builder = JsonFileBuilder()
        path = "init.json"
        data = builder.load(path)
        notify.init_data(data)

    def add(self, path, widget: QWidget, size=-1):
        self.window.add(path, widget, size)

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())

    def save(self, data, path="init.json"):
        builder = JsonFileBuilder()
        builder.add("data", data)
        file = os.path.join(path, DATA_FILE_NAME)
        builder.save(file)

    def load(self, path):
        builder = JsonFileBuilder()
        file = os.path.join(path, DATA_FILE_NAME)
        data = builder.load(file)
        if data:
            return data["data"]
        else:
            return None

    def new_project(self, data, path="init.json"):
        workspace = WorkSpace()
        return workspace.make_workspace(data, path)
