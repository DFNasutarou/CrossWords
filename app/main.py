"""
cd 'C:/workspace/github/nasu/CrossWords'
python -m app
"""

from app.lib.formlib import formlib
from app.lib.crosswordlib.wid_crossword import CrossWord
from app.workspace import WorkSpace

size = (600, 400)

WORK_SPACE = "workspace"
PROJECT = "project"


class Notify(formlib.ApplicationNotify):
    MENU_FILE = "ファイル"
    SUB_MENU_NEWPRO = "新規プロジェクト"
    SUB_MENU_SAVE = "プロジェクト保存"
    SUB_MENU_LOAD = "プロジェクト読み込み"
    SUB_PICTURE_SAVE = "画面キャプチャ"
    SUB_MENU_EXIT = "終了"
    MENU_BOARD = "盤面設定"
    SUB_MENU_BOARDSIZE = "【パネル】盤サイズ変更"
    SUB_MENU_BOARD_TRANS = "盤の転置（縦横変換）"
    SUB_MENU_KEY_SORT = "タテヨコカギ入れ替え"
    SUB_MENU_FORMAT_SETTING = "【パネル】フォーマット設定"
    MENU_BLACK = "黒塗り"
    SUB_MENU_BLACK_SETTING = "【パネル】黒塗り設定"
    SUB_MENU_BLACK_BOARD = "盤の黒塗りON/OFF"
    SUB_MENU_BLACK_KEY = "カギの黒塗りON/OFF"
    MENU_SHOW = "表示設定"
    SUB_MENU_BOARD_NUMBER = "盤の数字ON/OFF"
    SUB_MENU_BOARD_TEXT = "盤の文字ON/OFF"
    SUB_MENU_HIDE_TITLE = "タイトルの表示ON/OFF"
    SUB_MENU_HIDE_ANSWER = "答えの表示ON/OFF"
    SUB_MENU_DELETE_GUAID = "ガイド線ON/OFF(揮発)"
    SUB_MENU_SHOW_PICTURE = "上部に画像表示(揮発)"

    menu_dict = {
        MENU_FILE: [
            SUB_MENU_NEWPRO,
            SUB_MENU_SAVE,
            SUB_MENU_LOAD,
            SUB_PICTURE_SAVE,
            SUB_MENU_EXIT,
        ],
        MENU_BOARD: [
            SUB_MENU_BOARD_TRANS,
            SUB_MENU_KEY_SORT,
            SUB_MENU_BOARDSIZE,
            SUB_MENU_FORMAT_SETTING,
        ],
        MENU_BLACK: [
            SUB_MENU_BLACK_BOARD,
            SUB_MENU_BLACK_KEY,
            SUB_MENU_BLACK_SETTING,
        ],
        MENU_SHOW: [
            SUB_MENU_BOARD_NUMBER,
            SUB_MENU_BOARD_TEXT,
            SUB_MENU_HIDE_TITLE,
            SUB_MENU_HIDE_ANSWER,
            SUB_MENU_DELETE_GUAID,
            SUB_MENU_SHOW_PICTURE,
        ],
    }

    def __init__(self, app, cross: CrossWord, work: WorkSpace):
        self.app: formlib.Application = app
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
                    case Notify.SUB_MENU_BOARD_TRANS:
                        self.trans_board()
                    case Notify.SUB_MENU_KEY_SORT:
                        self.sort_key()
                    case Notify.SUB_MENU_FORMAT_SETTING:
                        self.format_setting_panel()
            case Notify.MENU_BLACK:
                match sub:
                    case Notify.SUB_MENU_BLACK_BOARD:
                        self.cross.set_world(board_black=True)
                    case Notify.SUB_MENU_BLACK_KEY:
                        self.cross.set_world(key_black=True)
                    case Notify.SUB_MENU_BLACK_SETTING:
                        self.black_setting_panel()
            case Notify.MENU_SHOW:
                match sub:
                    case Notify.SUB_MENU_BOARD_NUMBER:
                        self.cross.set_world(board_number=True)
                    case Notify.SUB_MENU_BOARD_TEXT:
                        self.cross.set_world(board_text=True)
                    case Notify.SUB_MENU_HIDE_TITLE:
                        self.cross.switch_title()
                    case Notify.SUB_MENU_HIDE_ANSWER:
                        self.cross.set_world(show_ans=True)
                    case Notify.SUB_MENU_DELETE_GUAID:
                        self.cross.delete_guaid()
                    case Notify.SUB_MENU_SHOW_PICTURE:
                        self.show_picture()

    def save(self):
        # ファイル保存
        data = self.cross.save()
        self.work.save_project(data)

    def load(self):
        # ファイル読み込み
        self.work.select_project()
        data = self.work.load_project()
        if data == None:
            return
        txt = self.work.project
        self.app.window.set_title(txt)
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

    def trans_board(self):
        # ボードを転置
        self.cross.trans_board()

    def sort_key(self):
        # キーの順番を入れ替え
        self.cross.sort_key()

    def show_picture(self):
        pic = self.work.load_picture()
        self.cross.set_picture(pic)


def main():
    app = formlib.Application()
    cross = CrossWord(size)
    work = WorkSpace()
    notify = Notify(app, cross, work)
    app.window.init_menu(notify)
    app.window.set_widget(cross)

    data = work.load_project()
    if data:
        txt = work.project
        txt = txt.replace("\\", "/")
        app.window.set_title(txt)
        cross.load(data)
    app.run()
