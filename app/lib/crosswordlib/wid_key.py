# widgets.py
import html
import os
import weakref

from PyQt6.QtWidgets import QWidget, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QPainter, QFontMetrics, QColor, QImage
from PyQt6.QtCore import QRect, Qt, QUrl
from app.lib.formlib.widgets import (
    EditableTextWidget,
    WidgetSetting,
    LabelWidget,
)
from app.lib.crosswordlib.const_color import Col
from app.lib.crosswordlib.clear_helpers import clear_clue_widgets
from app.lib.crosswordlib.geometry import (
    blackout_rect,
    snapped_blackout_square,
)
from app.lib.crosswordlib.inline_images import (
    BLACKOUT_ALL,
    BLACKOUT_NONE,
    BLACKOUT_OPAQUE,
    InlineImageError,
    normalize_inline_image,
    normalize_inline_images,
    pack_text_content,
    resolve_asset_path,
    unpack_text_content,
)
from app.lib.formlib.layouts import RowLayout, ColLayout

KEY_NUMBER = 80

STR_ROW_KEY_TITLE = "row_title"
STR_ROW_KEY_TITLE_SIZE = "row_title_size"
STR_ROW_KEY = "row_key"
STR_ROW_KEY_SIZE = "row_key_size"
STR_COL_KEY_TITLE = "col_title"
STR_COL_KEY_TITLE_SIZE = "col_title_size"
STR_COL_KEY_SIZE = "col_key_size"
STR_COL_KEY = "col_key"
KEY_NAME_LENGTH = "key_name_length"
KEY_TRANS = "key_trans"
KEY_SORT = "key_sort"

TYPE_ROW = "type_row"
TYPE_COL = "type_col"
TYPE_KEY = "type_key"


class KeyWidget(QWidget):

    def __init__(self, listener):
        super().__init__()
        self.listener = listener
        self.key_trans = 0
        self.key_sort = 0

        self.data = {}
        self.default_setting()

        self.base = RowLayout(self)
        self._reset_key_position()

    def setting_update(
        self,
        key_title_setting: WidgetSetting | None = None,
        key_setting: WidgetSetting | None = None,
        key_text_setting: WidgetSetting | None = None,
        key_anwser_setting: WidgetSetting | None = None,
    ) -> None:
        if key_title_setting != None:
            BlackKeyTitle.setting(key_title_setting)
        if key_setting != None:
            BlackKeyNameText.setting(key_setting)
        if key_text_setting != None:
            BlackKeyText.setting(key_text_setting)
        if key_anwser_setting != None:
            BlackKeyAnswer.setting(key_anwser_setting)

    def default_setting(self):
        self.data[STR_ROW_KEY_TITLE] = "タテのカギ"
        self.data[STR_ROW_KEY_TITLE_SIZE] = -1
        self.rows = [
            KeyGroup(TYPE_ROW, i, self, str(i), "") for i in range(KEY_NUMBER)
        ]
        for w in self.rows:
            w.hide()  # いったん全部消す

        self.data[STR_ROW_KEY] = [w.save() for w in self.rows]
        self.data[STR_ROW_KEY_SIZE] = -1
        self.data[STR_COL_KEY_TITLE] = "ヨコのカギ"
        self.data[STR_COL_KEY_TITLE_SIZE] = -1
        self.cols = [
            KeyGroup(TYPE_COL, i, self, str(i), "") for i in range(KEY_NUMBER)
        ]
        for w in self.cols:
            w.hide()  # いったん全部消す
        self.data[STR_COL_KEY] = [w.save() for w in self.cols]
        self.data[STR_COL_KEY_SIZE] = -1
        self.data[KEY_NAME_LENGTH] = -1

        self.rowkeytext = BlackKeyTitle(self.data[STR_ROW_KEY_TITLE])
        self.colkeytext = BlackKeyTitle(self.data[STR_COL_KEY_TITLE])

    def visible_update(
        self, row_open_list, col_open_list, row_answer, col_answer
    ):
        for i in range(KEY_NUMBER):
            rf = i < len(row_open_list)
            rk = str(row_open_list[i]) if rf else ""
            rt = row_answer[i] if rf else ""
            self.rows[i].set_all_visible(rf)
            self.rows[i].set_text(keyname=rk, answer=rt)
            cf = i < len(col_open_list)
            ck = str(col_open_list[i]) if cf else ""
            ct = col_answer[i] if cf else ""
            self.cols[i].set_all_visible(cf)
            self.cols[i].set_text(keyname=ck, answer=ct)

    def save(self):
        self.data[STR_ROW_KEY_TITLE] = self.rowkeytext.save()
        self.data[STR_COL_KEY_TITLE] = self.colkeytext.save()
        self.data[STR_ROW_KEY] = [w.save() for w in self.rows]
        self.data[STR_COL_KEY] = [w.save() for w in self.cols]
        self.data[KEY_TRANS] = self.key_trans
        self.data[KEY_SORT] = self.key_sort
        return self.data

    def load(self, data):
        self.data = data
        self.rowkeytext.load(self.data[STR_ROW_KEY_TITLE])
        self.colkeytext.load(self.data[STR_COL_KEY_TITLE])
        for i in range(KEY_NUMBER):
            self.rows[i].load(self.data[STR_ROW_KEY][i])
            self.cols[i].load(self.data[STR_COL_KEY][i])
        self.key_trans = self.data[KEY_TRANS]
        self.key_sort = self.data[KEY_SORT]
        self._reset_key_position()

    def get_visible_list(self):
        ret = []
        ret.append(self.rowkeytext)
        for kg in self.rows:
            if kg.is_visible:
                ret.append(kg)
        ret.append(self.colkeytext)
        for kg in self.cols:
            if kg.is_visible:
                ret.append(kg)
        return ret

    def show_setting(self, black, key, text, answer) -> None:
        BlackOutText.set_black(black)
        for kg in self.rows + self.cols:
            kg.set_visible(key, text, answer)
        self.update()

    def trans_key(self):
        self.key_trans = 1 - self.key_trans
        self._reset_key_position()

    def sort_key(self):
        self.key_sort = 1 - self.key_sort
        self._reset_key_position()

    def clear_clues(self):
        clear_clue_widgets(
            self.rowkeytext,
            self.colkeytext,
            self.rows + self.cols,
        )
        self.update()

    def get_inline_image_targets(self):
        targets = []
        for direction, groups in (
            ("タテ", self.rows),
            ("ヨコ", self.cols),
        ):
            for group in groups:
                if not group.is_visible:
                    continue
                number = group.keyname.get_text() or str(group.num)
                targets.append(
                    (f"{direction} {number}番のカギ文", group.text)
                )
        return targets

    def get_all_inline_image_widgets(self):
        return [
            group.text
            for group in self.rows + self.cols
        ]

    def get_clue_number_patterns(self):
        def pattern(groups):
            values = []
            for group in groups:
                if not group.is_visible:
                    continue
                if group.keyname.get_square():
                    values.append(None)
                    continue
                text = group.keyname.get_text().strip()
                try:
                    values.append(int(text))
                except ValueError:
                    values.append(text)
            return values

        return pattern(self.rows), pattern(self.cols)

    def _reset_key_position(self):
        # スペーサー作成
        spacer = []
        for i in range(3):
            spacer.append(
                QSpacerItem(
                    0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
                )
            )

        # ウィジェットを外す
        while self.base.count():
            item = self.base.takeAt(0)
            if item == None:
                break
            w = item.widget()
            if w:
                self.base.removeWidget(w)
        # ウィジェットを付けなおす
        fkt = self.rowkeytext
        skt = self.colkeytext
        fks = self.rows
        sks = self.cols
        if self.key_sort:
            fkt, skt = skt, fkt
            fks, sks = sks, fks
        if self.key_trans:
            fkt, skt = skt, fkt

        self.base.addWidget(fkt)
        self.base.addItem(spacer[0])
        for i in range(KEY_NUMBER):
            self.base.addWidget(fks[i])
        self.base.addItem(spacer[1])
        self.base.addWidget(skt)
        self.base.addItem(spacer[2])
        for i in range(KEY_NUMBER):
            self.base.addWidget(sks[i])
        self.base.addStretch()

    def check_all_answers(self):
        data = self.rows + self.cols
        for w in data:
            txt = w.answer.get_text()
            if w.isVisible and txt != "":
                w.notify(txt)

    def notify(self, tp, num, text):
        if tp == TYPE_ROW:
            event = 2
        elif tp == TYPE_COL:
            event = 3
        elif tp == TYPE_KEY:
            event = -1
        self.listener.notify(event, [num, text])


class BlackOutText(EditableTextWidget):
    """
    黒塗り可能なテキスト
    """

    black = 0
    black_color = QColor("000000")
    ghost_color = QColor("#ffcccc")
    image_assets = {}
    project_root = ""
    _image_cache = {}
    _all_instances = weakref.WeakSet()

    def __init__(self, text="", listner=None):
        # 問題文・カギ文は Enter で改行できる複数行編集にする
        super().__init__(
            text,
            listner,
            BlackOutText.black_color,
            multiline=True,
        )
        self.data = []
        self._plain_text = str(text)
        self._inline_images = []
        self._drag_start_x = None
        self._drag_active = False
        self._drag_listener = None
        self.label.mousePressEvent = self._drag_mouse_press
        self.label.mouseMoveEvent = self._drag_mouse_move
        self.label.mouseReleaseEvent = self._drag_mouse_release
        BlackOutText._all_instances.add(self)
        self._refresh_label()
        self.del_ghost()

    def save(self):
        return pack_text_content(
            self.get_text(),
            self.get_square(),
            self._inline_images,
        )

    def load(self, data):
        text, squares, inline_images = unpack_text_content(data)
        self.set_text(text)
        self.reset_square(squares)
        self.reset_inline_images(inline_images)

    def get_text(self):
        return self._plain_text

    def set_text(self, text):
        if text is None:
            return
        self._plain_text = str(text)
        self.edit.setText(self._plain_text)
        self._inline_images = normalize_inline_images(
            self._inline_images,
            len(self._plain_text),
        )
        self._refresh_label()

    def _finish_edit(self):
        self.set_text(self.edit.text())
        self.edit.hide()
        self.label.show()
        if self.listner:
            self.listner.notify(self.get_text())

    def get_inline_images(self):
        return [dict(image) for image in self._inline_images]

    def reset_inline_images(self, images):
        self._inline_images = normalize_inline_images(
            images,
            len(self.get_text()),
        )
        self._refresh_label()

    def add_inline_image(self, image):
        normalized = normalize_inline_image(image, len(self.get_text()))
        self._inline_images.append(normalized)
        self._inline_images.sort(
            key=lambda item: (item["position"], item["id"])
        )
        self._refresh_label()
        return normalized

    def update_inline_image(self, image_id, values):
        for index, current in enumerate(self._inline_images):
            if current["id"] != image_id:
                continue
            updated = dict(current)
            updated.update(values)
            self._inline_images[index] = normalize_inline_image(
                updated,
                len(self.get_text()),
            )
            self._inline_images.sort(
                key=lambda item: (item["position"], item["id"])
            )
            self._refresh_label()
            return True
        return False

    def remove_inline_image(self, image_id):
        previous_size = len(self._inline_images)
        self._inline_images = [
            image
            for image in self._inline_images
            if image["id"] != image_id
        ]
        if len(self._inline_images) != previous_size:
            self._refresh_label()
            return True
        return False

    def _refresh_label(self):
        if not self._inline_images:
            self.label.setTextFormat(Qt.TextFormat.PlainText)
            self.label.setText(self._plain_text)
            self.label.updateGeometry()
            return

        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setText(
            self.render_rich_text(self._plain_text, self._inline_images)
        )
        self.label.updateGeometry()

    @classmethod
    def render_rich_text(cls, text, images):
        """本文と差し込み画像一覧から表示用の RichText を生成する。

        images は position 昇順で並んでいること。
        画像差し込みパネルの「挿入後のイメージ」プレビューでも使う。
        """
        fragments = []
        text_position = 0
        for image in images:
            position = image["position"]
            fragments.append(cls._html_text(text[text_position:position]))
            fragments.append(cls._image_html(image))
            text_position = position
        fragments.append(cls._html_text(text[text_position:]))
        return "".join(fragments)

    @staticmethod
    def _html_text(text):
        return (
            html.escape(text)
            .replace(" ", "&nbsp;")
            .replace("\n", "<br>")
        )

    @classmethod
    def _image_html(cls, image):
        mode = image["blackout"] if BlackOutText.black else BLACKOUT_NONE
        image_source = BlackOutText._image_source(
            image["asset_id"],
            mode,
        )
        line_break = "<br>" if image.get("line_break") else ""
        if not image_source:
            return (
                '<span style="color:#aa0000">［画像なし］</span>'
                + line_break
            )
        return (
            f'<img src="{html.escape(image_source, quote=True)}" '
            f'width="{image["width"]}" height="{image["height"]}" />'
            + line_break
        )

    @classmethod
    def _image_source(cls, asset_id, mode):
        cache_key = (asset_id, mode)
        if cache_key in cls._image_cache:
            return cls._image_cache[cache_key]

        asset = cls.image_assets.get(asset_id)
        if not asset:
            return ""
        try:
            asset_path = resolve_asset_path(
                cls.project_root,
                asset.get("path", ""),
            )
        except (InlineImageError, OSError):
            return ""
        if not os.path.isfile(asset_path):
            return ""
        if mode == BLACKOUT_NONE:
            source = QUrl.fromLocalFile(asset_path).toString()
            cls._image_cache[cache_key] = source
            return source

        source = QImage(asset_path)
        if source.isNull():
            return ""

        if mode == BLACKOUT_ALL:
            rendered = QImage(source.size(), QImage.Format.Format_ARGB32)
            rendered.fill(QColor("black"))
        elif mode == BLACKOUT_OPAQUE:
            rendered = source.convertToFormat(QImage.Format.Format_ARGB32)
            painter = QPainter(rendered)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(rendered.rect(), QColor("black"))
            painter.end()
        else:
            return ""

        rendered_directory = os.path.join(
            cls.project_root,
            "picture",
            "inline",
            ".rendered",
        )
        try:
            os.makedirs(rendered_directory, exist_ok=True)
            rendered_path = os.path.join(
                rendered_directory,
                f"{asset_id}-{mode}.png",
            )
            if not rendered.save(rendered_path, "PNG"):
                return ""
        except OSError:
            return ""

        image_source = QUrl.fromLocalFile(rendered_path).toString()
        cls._image_cache[cache_key] = image_source
        return image_source

    @classmethod
    def set_image_assets(cls, assets, project_root=None):
        cls.image_assets = assets
        if project_root is not None:
            cls.project_root = project_root
        cls._image_cache = {}
        for instance in list(cls._all_instances):
            instance._refresh_label()

    def set_ghost(self, square: list[list[float]]):
        self.ghost = square
        self.update()

    def del_ghost(self):
        self.ghost: list[list[float]] = [[0.0, 0.0], [0.0, 10.0]]
        self.update()

    def add_square(self, square):
        if square not in self.data:
            self.data.append(square)
            self.update()

    def add_squares(self, squares):
        for square in squares:
            self.data.append(square)
        self.update()

    def reset_square(self, squares):
        self.data = squares
        self.update()

    def get_square(self):
        return self.data

    def remove_square(self, square):
        if square in self.data:
            self.data.remove(square)
            self.update()

    def set_drag_listener(self, listener):
        self._drag_listener = listener

    def _snapped_drag_square(self, x):
        font_metrics = QFontMetrics(self.label.font())
        unit_width = font_metrics.horizontalAdvance("あ")
        return snapped_blackout_square(
            self._text_x_from_display_x(self._drag_start_x, unit_width),
            self._text_x_from_display_x(x, unit_width),
            unit_width,
            len(self.get_text()),
        )

    def _text_x_from_display_x(self, display_x, unit_width):
        image_offset = 0
        for image in self._inline_images:
            image_start = image["position"] * unit_width + image_offset
            image_end = image_start + image["width"]
            if display_x < image_start:
                break
            if display_x <= image_end:
                return image["position"] * unit_width
            image_offset += image["width"]
        return display_x - image_offset

    def _drag_mouse_press(self, event):
        if (
            not BlackOutText.black
            or event.button() != Qt.MouseButton.LeftButton
        ):
            self._start_edit(event)
            return
        self._drag_start_x = event.pos().x()
        self._drag_active = False
        event.accept()

    def _drag_mouse_move(self, event):
        if (
            self._drag_start_x is None
            or not event.buttons() & Qt.MouseButton.LeftButton
        ):
            return
        if abs(event.pos().x() - self._drag_start_x) >= 3:
            self._drag_active = True
        if self._drag_active:
            self.set_ghost(self._snapped_drag_square(event.pos().x()))
        event.accept()

    def _drag_mouse_release(self, event):
        if (
            self._drag_start_x is None
            or event.button() != Qt.MouseButton.LeftButton
        ):
            return

        if self._drag_active:
            square = self._snapped_drag_square(event.pos().x())
            if square[0][0] != square[0][1]:
                if self._drag_listener:
                    self._drag_listener(square)
                else:
                    self.add_square(square)
            self.del_ghost()
        else:
            self.del_ghost()
            self._start_edit(event)

        self._drag_start_x = None
        self._drag_active = False
        event.accept()

    def square_exchange(self, square):
        font = self.label.font()
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance("あ")
        label_rect = self.label.geometry()
        rect = blackout_rect(
            square,
            unit_width=w,
            content_width=label_rect.width(),
            content_height=label_rect.height(),
            offset_x=label_rect.x(),
            offset_y=label_rect.y(),
        )
        rect[0] += self._image_width_before(square[0][0], True)
        rect[2] += (
            self._image_width_before(square[0][1], False)
            - self._image_width_before(square[0][0], True)
        )
        return rect

    def _image_width_before(self, text_unit, include_boundary):
        width = 0
        for image in self._inline_images:
            image_unit = image["position"] * 10
            if image_unit < text_unit or (
                include_boundary and image_unit == text_unit
            ):
                width += image["width"]
        return width

    def paintEvent(self, event):
        super().paintEvent(event)
        if BlackOutText.black:
            painter = QPainter(self)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(BlackOutText.black_color)
            for square in self.data:
                t = self.square_exchange(square)
                painter.drawRect(QRect(*t))

            painter.setBrush(BlackOutText.ghost_color)
            t = self.square_exchange(self.ghost)
            painter.drawRect(QRect(*t))

            painter.end()

    def clone(self):
        ret = BlackOutText(self.get_text())
        # ret.set_black(self.black)
        for square in self.get_square():
            ret.add_square(square)
        ret.reset_inline_images(self.get_inline_images())
        return ret

    @classmethod
    def set_black(cls, black):
        # 黒塗りするなら1
        cls.black = black
        for instance in list(cls._all_instances):
            instance._refresh_label()


class BlackKeyAnswer(LabelWidget):
    wid = 40
    font_size = 10
    marg = [0, 0, 0, 0]
    col = "#000000"
    _instances: list["BlackKeyAnswer"] = []

    def __init__(self, text, listener):
        super().__init__(text, listener)
        self.configure()
        self.__class__._instances.append(self)

    def configure(self):
        self.set_font(BlackKeyAnswer.font_size)
        # self.setContentsMargins(*BlackKeyAnswer.margin)
        # self.set_minimum_length(BlackKeyAnswer.wid)
        self.set_color(BlackKeyAnswer.col)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.marg = setting.data[WidgetSetting.MARGIN]
        cls.col = setting.data[WidgetSetting.COLOR]
        for inst in cls._instances:
            inst.configure()


class BlackKeyTitle(BlackOutText):
    wid = 40
    font_size = 10
    margin = [0, 0, 0, 0]
    col = Col.black
    _instances: list["BlackKeyTitle"] = []

    def __init__(self, text):
        super().__init__(text)
        self.configure()
        self.__class__._instances.append(self)

    def configure(self):
        self.set_font(BlackKeyTitle.font_size)
        self.setContentsMargins(*BlackKeyTitle.margin)
        self.set_minimum_length(BlackKeyTitle.wid)
        self.set_color(BlackKeyTitle.col)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.margin = setting.data[WidgetSetting.MARGIN]
        cls.col = setting.data[WidgetSetting.COLOR]
        for inst in cls._instances:
            inst.configure()


class BlackKeyNameText(BlackOutText):
    wid = 40
    font_size = 10
    margin = [0, 0, 0, 0]
    col = Col.black
    _instances: list["BlackKeyNameText"] = []

    def __init__(self, text):
        super().__init__(text)
        self.configure()
        self.__class__._instances.append(self)

    def configure(self):
        self.set_font(BlackKeyNameText.font_size)
        self.setContentsMargins(*BlackKeyNameText.margin)
        self.set_minimum_length(BlackKeyNameText.wid)
        self.set_color(BlackKeyNameText.col)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.margin = setting.data[WidgetSetting.MARGIN]
        cls.col = setting.data[WidgetSetting.COLOR]
        for inst in cls._instances:
            inst.configure()


class BlackKeyText(BlackOutText):
    wid = 40
    font_size = 10
    margin = [0, 0, 0, 0]
    col = Col.black
    _instances: list["BlackKeyText"] = []

    def __init__(self, text):
        super().__init__(text)
        self.configure()
        self.__class__._instances.append(self)

    def configure(self):
        self.set_font(BlackKeyText.font_size)
        self.setContentsMargins(*BlackKeyText.margin)
        self.set_minimum_length(BlackKeyText.wid)
        self.set_color(BlackKeyText.col)

    @classmethod
    def setting(cls, setting: WidgetSetting):
        cls.wid = setting.data[WidgetSetting.WID]
        cls.font_size = setting.data[WidgetSetting.SIZE]
        cls.margin = setting.data[WidgetSetting.MARGIN]
        cls.col = setting.data[WidgetSetting.COLOR]
        BlackOutText.black_color = QColor(setting.data[WidgetSetting.COLOR])
        for inst in cls._instances:
            inst.configure()


class KeyGroup(QWidget):
    """
    カギ一個分(カギ名、指示、回答)
    """

    KEY_NAME = "key_name"
    TEXT = "text"
    ANSWER = "answer"

    def __init__(self, tp, num, listener=None, keyname="", text="", answer=""):
        super().__init__()
        self.tp = tp
        self.num = num
        self.is_visible = True
        self.listener = listener
        self.base = ColLayout(self)
        self.keyname = BlackKeyNameText(keyname)
        self.text = BlackKeyText(text)
        self.answer = BlackKeyAnswer(answer, self)
        self.widgets: list[EditableTextWidget] = [
            self.keyname,
            self.text,
            self.answer,
        ]

        for key in self.widgets:
            self.base.addWidget(key)

        # マージン設定
        self.base.setSpacing(8)
        self.base.update()

    def save(self):
        data = {}
        data[KeyGroup.KEY_NAME] = self.keyname.save()
        data[KeyGroup.TEXT] = self.text.save()
        data[KeyGroup.ANSWER] = self.answer.save()
        return data

    def load(self, data):
        self.keyname.load(data[KeyGroup.KEY_NAME])
        self.text.load(data[KeyGroup.TEXT])
        self.answer.load(data[KeyGroup.ANSWER])

    def set_text(self, keyname=None, text=None, answer=None):
        for w, v in zip(self.widgets, [keyname, text, answer]):
            w.set_text(v)

    # def read_setting(self, data: WidgetSetting):
    #     self.set_font(data.data[WidgetSetting.SIZE])

    # def set_font(self, font_size):
    #     for w in self.widgets:
    #         w.set_font(font_size)

    def get_text(self):
        data = []
        for w in self.widgets:
            data.append(w.get_text())
        return data

    def set_visible(self, key=True, text=True, answer=True):
        # 表示設定　基本的には答えを非表示にするのに使う
        for w, v in zip(self.widgets, [key, text, answer]):
            if v:
                w.show()
            else:
                w.hide()

    def set_all_visible(self, is_visible):
        self.is_visible = is_visible
        if self.is_visible:
            self.show()
        else:
            self.hide()

    # def set_min_size(self, key, text, answer):
    #     for w, v in zip(self.widgets, [key, text, answer]):
    #         w.set_minimum_length(v)

    # def set_black(self, black):
    #     self.keyname.set_black(black)
    #     self.text.set_black(black)

    def notify(self, text):
        if self.listener:
            self.listener.notify(self.tp, self.num, text)
