import os

from PyQt5.QtWidgets import (
    QMessageBox,
    QInputDialog,
)
from .lib.formlib.jsonio import JsonFileBuilder

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

        data = data["data"]
        self.workspace = data[WORK_SPACE]
        self.project = data[PROJECT]

    def make_workspace(self, data):
        # selected_dir = QFileDialog.getExistingDirectory(
        #     None,
        #     "ベースとなるフォルダを選択",
        #     os.path.expanduser(path),  # 初期表示はホーム
        #     QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        # )
        # if not selected_dir:
        #     return

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
        print(self.project, file)
        data = builder.load(file)
        if type(data) == dict and "data" in data:
            return data["data"]
        else:
            return None

    def update_init_file(self):
        pass
