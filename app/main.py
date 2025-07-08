"""
cd 'C:/workspace/github/nasu/CrossWords'
python -m app
"""

from app.lib.formlib import formlib
from app.lib.crosswordlib.wid_crossword import CrossWord
from app.workspace import WorkSpace

size = (1000, 660)

WORK_SPACE = "workspace"
PROJECT = "project"


class Notify(formlib.ApplicationNotify):
    MENU_FILE = "ファイル"
    SUB_MENU_NEWPRO = "新規プロジェクト"
    SUB_MENU_SAVE = "ファイル保存"
    SUB_MENU_LOAD = "ファイル読み込み"
    SUB_PICTURE_SAVE = "画面キャプチャ"
    SUB_MENU_EXIT = "終了"
    MENU_BOARD = "盤面設定"
    SUB_MENU_BOARDSIZE = "盤サイズ変更"
    MENU_PANEL = "パネル"
    SUB_MENU_BLACK_SETTING = "黒塗り設定パネル"
    SUB_MENU_FORMAT_SETTING = "フォーマット設定パネル"
    MENU_BLACK = "黒塗り"
    # SUB_MENU_BLACK_TITLE = "指示文を塗る"
    SUB_MENU_BLACK_BOARD = "ボードを塗る"
    SUB_MENU_BOARD_NUMBER = "ボードの数字を消す"
    SUB_MENU_BOARD_TEXT = "ボードの文字を消す"
    SUB_MENU_BLACK_KEY = "キーを塗る"
    # SUB_MENU_BLACK_TEXT = "テキストを塗る"
    SUB_MENU_HIDE_ANSWER = "答えを隠す"
    SUB_MENU_DELETE_GUAID = "枠線を消す"

    menu_dict = {
        MENU_FILE: [
            SUB_MENU_NEWPRO,
            SUB_MENU_SAVE,
            SUB_MENU_LOAD,
            SUB_PICTURE_SAVE,
            SUB_MENU_EXIT,
        ],
        MENU_BOARD: [SUB_MENU_BOARDSIZE],
        MENU_PANEL: [SUB_MENU_BLACK_SETTING, SUB_MENU_FORMAT_SETTING],
        MENU_BLACK: [
            # SUB_MENU_BLACK_TITLE,
            SUB_MENU_BLACK_BOARD,
            SUB_MENU_BOARD_NUMBER,
            SUB_MENU_BOARD_TEXT,
            SUB_MENU_BLACK_KEY,
            # SUB_MENU_BLACK_TEXT,
            SUB_MENU_HIDE_ANSWER,
            SUB_MENU_DELETE_GUAID,
        ],
    }

    def __init__(self, app, cross: CrossWord, work: WorkSpace):
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
                    case Notify.SUB_PICTURE_SAVE:
                        self.capture()
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
                    case Notify.SUB_MENU_FORMAT_SETTING:
                        self.format_setting_panel()
            case Notify.MENU_BLACK:
                match sub:
                    # case Notify.SUB_MENU_BLACK_TITLE:
                    case Notify.SUB_MENU_BLACK_BOARD:
                        self.cross.set_world(board_black=True)
                    case Notify.SUB_MENU_BOARD_NUMBER:
                        self.cross.set_world(board_number=True)
                    case Notify.SUB_MENU_BOARD_TEXT:
                        self.cross.set_world(board_text=True)
                    case Notify.SUB_MENU_BLACK_KEY:
                        self.cross.set_world(key_black=True)
                    # case Notify.SUB_MENU_BLACK_TEXT:
                    case Notify.SUB_MENU_HIDE_ANSWER:
                        self.cross.set_world(show_ans=True)
                    case Notify.SUB_MENU_DELETE_GUAID:
                        self.cross.delete_guaid()

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

    def format_setting_panel(self):
        # フォーマット設定パネルを開く
        self.cross.format_setting_panel()

    def capture(self):
        cap = self.cross.get_capture()
        self.work.save_capture(cap)

    def delete_guaid(self):
        # ガイドを消す
        self.cross.delete_guaid()


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
