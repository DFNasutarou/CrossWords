import os, re

from PyQt5.QtWidgets import (
    QMessageBox,
    QInputDialog,
    QFileDialog,
)
from app.lib.formlib.jsonio import JsonFileBuilder
from PyQt5.QtGui import QPixmap, QPainter, QPageSize
from PyQt5.QtSvg import QSvgGenerator
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import QSizeF

WORK_SPACE = "workspace"
PROJECT = "project"
PICTURE_FOLDER_NAME = "picture"
DATA_FILE_NAME = "data.json"
INIT_JSON = "init.json"


class WorkSpace:
    def __init__(self):
        # 初期設定ファイル読み込み
        builder = JsonFileBuilder()
        data = builder.load(INIT_JSON)
        if data == None:
            print("data is none")
            return
        data = data["data"]
        if type(data) != dict:
            print("data is error")
            return

        self.workspace = str(data[WORK_SPACE])
        self.project = str(data[PROJECT])

    def make_workspace(self, data):
        path = self.workspace

        folder_name, ok = QInputDialog.getText(
            None,
            "新規フォルダ名を指定",
            "作成するフォルダ名を入力してください：",
        )
        if not ok or not folder_name.strip():
            return  # キャンセルまたは空文字

        target_dir = os.path.join(path, folder_name.strip())
        picture_dir = os.path.join(target_dir, PICTURE_FOLDER_NAME)
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

        self.project = target_dir
        self.save_workspace_data()

    def save_workspace_data(self):
        data = {}
        data[WORK_SPACE] = self.workspace
        data[PROJECT] = self.project

        builder = JsonFileBuilder()
        builder.add("data", data)
        builder.save(INIT_JSON)

    def save_project(self, data):
        builder = JsonFileBuilder()
        builder.add("data", data)
        file = os.path.join(self.project, DATA_FILE_NAME)
        builder.save(file)

    def load_project(self):
        # self.projectに指定されているデータを読み込み
        builder = JsonFileBuilder()
        file = os.path.join(self.project, DATA_FILE_NAME)
        data = builder.load(file)
        if type(data) == dict and "data" in data:
            self.update_init_file()
            return data["data"]
        else:
            return None

    def select_project(self):
        # プロジェクトを選択
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "data.jsonを選択",
            self.workspace,  # 初期ディレクトリ
            "jsonファイル (*.json);",  # フィルタ
        )
        if not file_path:
            return
        if self.workspace not in file_path:
            print("ワークスペース外のファイルは選択できません")
            return
        normalized = file_path.replace("\\", "/")
        file_path = file_path.removeprefix(self.workspace)
        pattern = rf"({re.escape(self.workspace)}/[^/]+)"
        m = re.search(pattern, normalized)
        if m != None:
            self.project = m.group(1)

    def save_capture(self, cap: QPixmap):
        # pngでスクリーンキャプチャ取得
        file_name, ok = QInputDialog.getText(
            None,
            "ファイル名を指定",
            "作成するファイル名を入力してください：",
        )
        if not ok or not file_name.strip():
            return  # キャンセルまたは空文字

        picture_dir = os.path.join(self.project, PICTURE_FOLDER_NAME)
        picture_file = os.path.join(picture_dir, file_name)
        success = cap.save(picture_file + ".png", "PNG")
        if success:
            print(file_name + ".png に保存しました")
        else:
            print("保存に失敗しました")

    def save_svg(self, widget):
        # svgでスクリーンキャプチャ取得
        file = self.select_output_file()
        if file == None:
            return
        svg_file = file + ".svg"

        generator = QSvgGenerator()
        generator.setFileName(svg_file)  # 出力ファイル名
        generator.setSize(widget.size())  # 出力サイズ(px単位)
        generator.setViewBox(widget.rect())  # 座標系 (0,0)-(width,height)
        generator.setTitle("PyQt5 Widget SVG Export")
        generator.setDescription("Exported from a PyQt5 widget")

        # ペインタでウィジェットを SVG に描画
        painter = QPainter(generator)
        widget.render(painter)
        painter.end()

    def select_output_file(self):
        file_name, ok = QInputDialog.getText(
            None,
            "ファイル名を指定",
            "作成するファイル名を入力してください：",
        )
        if not ok or not file_name.strip():
            return  # キャンセルまたは空文字

        picture_dir: str = os.path.join(self.project, PICTURE_FOLDER_NAME)
        picture_file = os.path.join(picture_dir, file_name)

        return picture_file

    def save_widget_as_pdf(self, widget):
        file = self.select_output_file()
        if file == None:
            return
        filename = file + ".pdf"
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        size = QSizeF(widget.size())
        printer.setPageSize(QPageSize(size, QPageSize.Point, "MyCustom"))
        # .setPageSize(QPrinter.Letter)  # 用紙サイズなども設定可能
        painter = QPainter(printer)
        w_rect = widget.rect()
        p_rect = printer.pageRect()
        # X, Y それぞれ別にスケーリング
        sx = p_rect.width() / w_rect.width()
        sy = p_rect.height() / w_rect.height()
        painter.scale(sx, sy)  # 縦横で別スケール指定すると縦横比が変わる
        widget.render(painter)
        painter.end()

    def load_picture(self):
        # 画像を読み込む
        # 単一ファイル選択ダイアログ
        file_path, ok = QFileDialog.getOpenFileName(
            None,
            "画像ファイルを選択",
            self.workspace,  # 初期ディレクトリ
            "画像ファイル (*.png *.jpg *.bmp)",  # フィルタ
        )
        if not ok:
            return None
        return QPixmap(file_path)

    def load_picture_pdf(self):
        # 画像を読み込む
        # 単一ファイル選択ダイアログ
        file_path, ok = QFileDialog.getOpenFileName(
            None,
            "画像ファイルを選択",
            self.workspace,  # 初期ディレクトリ
            "画像ファイル (*.svg *.pdf)",  # フィルタ
        )
        if not ok:
            return None
        return file_path

    def update_init_file(self):
        # initファイルを更新
        data = {}
        data[WORK_SPACE] = self.workspace
        data[PROJECT] = self.project

        builder = JsonFileBuilder()
        builder.add("data", data)
        builder.save(INIT_JSON)
