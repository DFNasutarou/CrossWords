"""
cd 'C:/workspace/github/nasu/CrossWords'
python -m app
"""

from .lib.formlib import formlib
from .lib.crosswordlib.wid_crossword import CrossWord

size = (1000, 660)

WORK_SPACE = "workspace"
PROJECT = "project"


class Notify(formlib.ApplicationNotify):
    def init_data(self, data):
        # initデータ読み込み結果通知
        data = data["data"]
        self.workspace = data[WORK_SPACE]
        self.project = data[PROJECT]

    def save(self):
        # ファイル保存
        if not self.cross:
            return
        data = self.cross.save()
        path = self.project
        self.app.save(data, path)

    def load(self):
        # ファイル読み込み
        if not self.cross:
            return
        data = []
        self.cross.load(data)

    def new_project(self):
        # プロジェクト新規作成
        if not self.cross:
            return
        data = self.cross.save()
        self.project = self.app.new_project(data, self.workspace)
        self.init_data_update()

    def set_instance(self, cross, app):
        # フォームウィジェット設定
        self.cross = cross
        self.app = app
        data = self.app.load(self.project)
        if data != None:
            self.cross.load(data)

    def init_data_update(self):
        # initファイルを更新
        data = {}
        data[WORK_SPACE] = self.workspace
        data[PROJECT] = self.project
        self.app.save(data)


def main():
    notify = Notify()
    app = formlib.Application(size, notify)
    cross = CrossWord(size)
    notify.set_instance(cross, app)
    app.add([], cross)
    app.run()
