"""
cd 'C:/workspace/github/nasu/CrossWords'
python -m app
"""

from .lib.formlib import formlib
from .lib.crosswordlib.wid_crossword import CrossWord
from .workspace import WorkSpace

size = (1000, 660)

WORK_SPACE = "workspace"
PROJECT = "project"


class Notify(formlib.ApplicationNotify):
    MENU_FILE = "ファイル"
    SUB_MENU_NEWPRO = "新規プロジェクト"
    SUB_MENU_SAVE = "ファイル保存"
    SUB_MENU_LOAD = "ファイル読み込み"
    SUB_MENU_EXIT = "終了"
    MENU_BOARD = "盤面設定"
    SUB_MENU_BOARDSIZE = "盤サイズ変更"
    MENU_PANEL = "パネル"
    SUB_MENU_BLACK_SETTING = "黒塗り設定パネル"

    menu_dict = {
        MENU_FILE: [
            SUB_MENU_NEWPRO,
            SUB_MENU_SAVE,
            SUB_MENU_LOAD,
            SUB_MENU_EXIT,
        ],
        MENU_BOARD: [SUB_MENU_BOARDSIZE],
        MENU_PANEL: [SUB_MENU_BLACK_SETTING],
    }

    def __init__(self, app, cross: CrossWord, work):
        self.app = app
        self.cross = cross
        self.work = work

    def notify(self, menu, sub):
        match menu:
            case Notify.MENU_FILE:
                match sub:
                    case Notify.SUB_MENU_NEWPRO:
                        self.new_project()
                    case Notify.SUB_MENU_SAVE:
                        self.save()
                    case Notify.SUB_MENU_LOAD:
                        self.load()
                    case Notify.SUB_MENU_EXIT:
                        self.end_app()
            case Notify.MENU_BOARD:
                match sub:
                    case Notify.SUB_MENU_BOARDSIZE:
                        self.resize_board()
            case Notify.MENU_PANEL:
                match sub:
                    case Notify.SUB_MENU_BLACK_SETTING:
                        self.black_setting_panel()

    def save(self):
        # ファイル保存
        data = self.cross.save()
        self.work.save_project(data)

    def load(self):
        # ファイル読み込み
        data = []
        self.cross.load(data)

    def end_app(self):
        self.app.window.close()

    def new_project(self):
        # プロジェクト新規作成
        data = self.cross.save()
        self.work.make_workspace(data)
        self.save()

    def resize_board(self):
        # ボードの大きさを変更
        self.cross.resize_board()

    def black_setting_panel(self):
        # 黒塗り設定パネルを開く
        self.cross.black_setting_panel()


def main():
    app = formlib.Application(size)
    cross = CrossWord(size)
    work = WorkSpace()
    notify = Notify(app, cross, work)
    app.window.init_menu(notify)
    app.window.set_widget(cross)

    data = work.load_project()
    if data:
        cross.load(data)
    app.run()
