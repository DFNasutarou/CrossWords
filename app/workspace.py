import os, re

from PyQt5.QtWidgets import (
    QMessageBox,
    QInputDialog,
    QFileDialog,
)
from app.lib.formlib.jsonio import JsonFileBuilder
from PyQt5.QtGui import QPixmap

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
        builder = JsonFileBuilder()
        file = os.path.join(self.project, DATA_FILE_NAME)
        data = builder.load(file)
        if type(data) == dict and "data" in data:
            self.update_init_file()
            return data["data"]
        else:
            return None

    def select_project(self):
        # 単一ファイル選択ダイアログ
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

    def update_init_file(self):
        data = {}
        data[WORK_SPACE] = self.workspace
        data[PROJECT] = self.project

        builder = JsonFileBuilder()
        builder.add("data", data)
        builder.save(INIT_JSON)
