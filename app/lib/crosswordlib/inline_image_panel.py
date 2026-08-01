import os
import shutil
import uuid

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFontMetrics,
    QImage,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.lib.crosswordlib.inline_images import (
    BLACKOUT_ALL,
    BLACKOUT_NONE,
    BLACKOUT_OPAQUE,
    MAX_IMAGE_BYTES,
    InlineImageError,
    create_image_asset,
    create_inline_image,
    make_asset_relative_path,
    referenced_asset_ids,
    resolve_asset_path,
)
from app.lib.crosswordlib.wid_key import BlackOutText


class PositionLabel(QWidget):
    """対象の文を表示し、クリックで挿入位置を選べるプレビュー。

    現在の挿入位置は文中に赤いキャレット（縦線）で表示する。
    """

    position_selected = pyqtSignal(int)

    PADDING = 8
    CARET_WIDTH = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._position = 0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("文中をクリックすると、その位置を挿入位置に設定します")
        self.setMinimumHeight(40)

    def set_content(self, text):
        self._text = text
        self._position = min(self._position, len(text))
        self._update_height()
        self.update()

    def set_position(self, position):
        self._position = max(0, min(position, len(self._text)))
        self.update()

    def _boundaries(self):
        """文字境界 0～len(text) の描画座標 (x, y) の一覧を返す。"""
        metrics = QFontMetrics(self.font())
        usable = max(20, self.width() - self.PADDING * 2)
        x = 0
        y = 0
        points = []
        for character in self._text:
            width = metrics.horizontalAdvance(character)
            if x + width > usable and x > 0:
                x = 0
                y += metrics.height()
            points.append((x, y))
            x += width
        points.append((x, y))
        return points

    def _update_height(self):
        metrics = QFontMetrics(self.font())
        last_y = self._boundaries()[-1][1]
        self.setMinimumHeight(
            last_y + metrics.height() + self.PADDING * 2
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_height()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f3f3f3"))
        painter.setPen(QColor("#cccccc"))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        metrics = QFontMetrics(self.font())
        points = self._boundaries()
        painter.setPen(QColor("#222222"))
        for index, character in enumerate(self._text):
            x, y = points[index]
            painter.drawText(
                self.PADDING + x,
                self.PADDING + y + metrics.ascent(),
                character,
            )

        caret_x, caret_y = points[self._position]
        painter.setPen(QPen(QColor("#dd0000"), self.CARET_WIDTH))
        painter.drawLine(
            self.PADDING + caret_x,
            self.PADDING + caret_y,
            self.PADDING + caret_x,
            self.PADDING + caret_y + metrics.height(),
        )
        painter.end()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)

        points = self._boundaries()
        line_height = QFontMetrics(self.font()).height()
        click_x = event.pos().x() - self.PADDING
        click_y = event.pos().y() - self.PADDING

        def distance(point):
            x, y = point
            return (abs(y + line_height / 2 - click_y), abs(x - click_x))

        position = min(
            range(len(points)),
            key=lambda index: distance(points[index]),
        )
        self.position_selected.emit(position)
        event.accept()


class InlineImagePanel(QDialog):
    def __init__(
        self,
        targets,
        assets,
        project_root,
        all_image_widgets=None,
        parent=None,
    ):
        super().__init__(parent)
        self.targets = targets
        self.assets = assets
        self.project_root = project_root
        self.all_image_widgets = all_image_widgets or [
            target for _, target in targets
        ]
        self._updating_size = False

        self.setWindowTitle("画像の登録・差し込み")
        self.resize(760, 620)

        base = QVBoxLayout(self)
        description = QLabel(
            "画像はプロジェクト内の picture/inline にコピーされます。"
            "挿入位置は0が文頭、文字数と同じ値が文末です。"
        )
        description.setWordWrap(True)
        base.addWidget(description)

        register_row = QHBoxLayout()
        self.asset_combo = QComboBox()
        self.asset_combo.currentIndexChanged.connect(self._asset_changed)
        register_button = QPushButton("画像を登録")
        register_button.clicked.connect(self.register_image)
        relink_button = QPushButton("選択画像を再リンク")
        relink_button.clicked.connect(self.relink_image)
        cleanup_button = QPushButton("未使用画像を整理")
        cleanup_button.clicked.connect(self.cleanup_unused_images)
        register_row.addWidget(QLabel("登録画像"))
        register_row.addWidget(self.asset_combo, 1)
        register_row.addWidget(register_button)
        register_row.addWidget(relink_button)
        register_row.addWidget(cleanup_button)
        base.addLayout(register_row)

        self.asset_preview = QLabel("画像を登録してください")
        self.asset_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.asset_preview.setFixedHeight(130)
        self.asset_preview.setStyleSheet(
            "background: #fafafa; border: 1px solid #cccccc;"
        )
        base.addWidget(self.asset_preview)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self.target_combo = QComboBox()
        for name, target in self.targets:
            self.target_combo.addItem(
                _target_label(name, target.get_text())
            )
        self.target_combo.currentIndexChanged.connect(
            self._target_changed
        )
        self.target_preview = PositionLabel()

        self.position = QSpinBox()
        self.position.setMinimum(0)
        self.target_preview.position_selected.connect(
            self.position.setValue
        )
        self.position_hint = QLabel("0文字目")
        self.position.valueChanged.connect(self._position_changed)
        position_widget = QWidget()
        position_row = QHBoxLayout(position_widget)
        position_row.setContentsMargins(0, 0, 0, 0)
        position_row.addWidget(self.position)
        position_row.addWidget(self.position_hint)
        position_row.addWidget(QLabel("（上の文をクリックして指定できます）"))
        position_row.addStretch()

        size_widget = QWidget()
        size_row = QHBoxLayout(size_widget)
        size_row.setContentsMargins(0, 0, 0, 0)
        self.width = QSpinBox()
        self.height = QSpinBox()
        for spin in (self.width, self.height):
            spin.setRange(8, 800)
            spin.setSuffix(" px")
        self.width.valueChanged.connect(self._width_changed)
        self.height.valueChanged.connect(self._height_changed)
        self.keep_aspect = QCheckBox("縦横比を固定")
        self.keep_aspect.setChecked(True)
        size_row.addWidget(QLabel("幅"))
        size_row.addWidget(self.width)
        size_row.addWidget(QLabel("高さ"))
        size_row.addWidget(self.height)
        size_row.addWidget(self.keep_aspect)
        size_row.addStretch()

        self.blackout = QComboBox()
        self.blackout.addItem("黒塗りなし", BLACKOUT_NONE)
        self.blackout.addItem(
            "透明部分以外を黒塗り",
            BLACKOUT_OPAQUE,
        )
        self.blackout.addItem(
            "透明部分を含め全体を黒塗り",
            BLACKOUT_ALL,
        )
        self.blackout.setCurrentIndex(
            self.blackout.findData(BLACKOUT_OPAQUE)
        )

        form.addRow("差し込み先", self.target_combo)
        form.addRow("対象の文", self.target_preview)
        form.addRow("挿入する文字位置", position_widget)
        form.addRow("表示サイズ", size_widget)
        form.addRow("黒塗り方法", self.blackout)
        base.addWidget(form_widget)

        operation_row = QHBoxLayout()
        add_button = QPushButton("新しく差し込む")
        add_button.clicked.connect(self.add_image)
        update_button = QPushButton("選択項目を更新")
        update_button.clicked.connect(self.update_image)
        delete_button = QPushButton("選択項目を削除")
        delete_button.clicked.connect(self.delete_image)
        operation_row.addWidget(add_button)
        operation_row.addWidget(update_button)
        operation_row.addWidget(delete_button)
        operation_row.addStretch()
        base.addLayout(operation_row)

        base.addWidget(QLabel("差し込み済み画像"))
        self.placement_list = QListWidget()
        self.placement_list.currentItemChanged.connect(
            self._placement_selected
        )
        base.addWidget(self.placement_list, 1)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        close_row.addWidget(close_button)
        base.addLayout(close_row)

        self._refresh_asset_combo()
        self._target_changed()
        self._refresh_placement_list()

    def register_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "画像ファイルを選択",
            self.project_root,
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not file_path:
            return

        try:
            if os.path.getsize(file_path) > MAX_IMAGE_BYTES:
                raise InlineImageError("画像は20MB以下にしてください")
            image = QImage(file_path)
            if image.isNull():
                raise InlineImageError("画像ファイルを読み込めません")

            asset_id = str(uuid.uuid4())
            relative_path = make_asset_relative_path(
                file_path,
                asset_id,
            )
            destination = resolve_asset_path(
                self.project_root,
                relative_path,
            )
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(file_path, destination)
            _, asset = create_image_asset(
                file_path,
                relative_path,
                image.width(),
                image.height(),
                asset_id=asset_id,
            )
            self.assets[asset_id] = asset
            BlackOutText.set_image_assets(
                self.assets,
                self.project_root,
            )
        except (InlineImageError, OSError) as error:
            QMessageBox.critical(self, "画像登録エラー", str(error))
            return

        self._refresh_asset_combo(asset_id)
        self._set_default_size(asset)

    def add_image(self):
        asset_id = self.asset_combo.currentData()
        target = self._current_target()
        if not asset_id or target is None:
            QMessageBox.information(
                self,
                "画像の差し込み",
                "先に画像を登録してください。",
            )
            return

        image = create_inline_image(
            asset_id,
            self.position.value(),
            self.width.value(),
            self.height.value(),
            self.blackout.currentData(),
        )
        target.add_inline_image(image)
        self._refresh_placement_list(image["id"])

    def relink_image(self):
        asset_id = self.asset_combo.currentData()
        asset = self.assets.get(asset_id)
        if not asset:
            QMessageBox.information(
                self,
                "画像の再リンク",
                "再リンクする登録画像を選択してください。",
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "置き換える画像ファイルを選択",
            self.project_root,
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not file_path:
            return

        try:
            if os.path.getsize(file_path) > MAX_IMAGE_BYTES:
                raise InlineImageError("画像は20MB以下にしてください")
            image = QImage(file_path)
            if image.isNull():
                raise InlineImageError("画像ファイルを読み込めません")
            previous_destination = resolve_asset_path(
                self.project_root,
                asset["path"],
            )
            relative_path = make_asset_relative_path(
                file_path,
                asset_id,
            )
            destination = resolve_asset_path(
                self.project_root,
                relative_path,
            )
            same_file = (
                os.path.isfile(destination)
                and os.path.samefile(file_path, destination)
            )
            if not same_file:
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                shutil.copy2(file_path, destination)
            if (
                previous_destination != destination
                and os.path.isfile(previous_destination)
            ):
                os.remove(previous_destination)
            _, updated = create_image_asset(
                file_path,
                relative_path,
                image.width(),
                image.height(),
                asset_id=asset_id,
            )
            self.assets[asset_id] = updated
            self._delete_rendered_files(asset_id)
            BlackOutText.set_image_assets(
                self.assets,
                self.project_root,
            )
        except (InlineImageError, OSError) as error:
            QMessageBox.critical(self, "画像再リンクエラー", str(error))
            return

        self._refresh_asset_combo(asset_id)

    def update_image(self):
        item = self.placement_list.currentItem()
        target = self._current_target()
        asset_id = self.asset_combo.currentData()
        if item is None or target is None or not asset_id:
            return

        previous_target_index, image_id = item.data(Qt.ItemDataRole.UserRole)
        previous_target = self.targets[previous_target_index][1]
        values = {
            "asset_id": asset_id,
            "position": self.position.value(),
            "width": self.width.value(),
            "height": self.height.value(),
            "blackout": self.blackout.currentData(),
        }
        current_target_index = self.target_combo.currentIndex()
        if previous_target is target:
            target.update_inline_image(image_id, values)
        else:
            previous_target.remove_inline_image(image_id)
            values["id"] = image_id
            target.add_inline_image(values)
        self._refresh_placement_list(image_id)

    def delete_image(self):
        item = self.placement_list.currentItem()
        if item is None:
            return
        target_index, image_id = item.data(Qt.ItemDataRole.UserRole)
        answer = QMessageBox.question(
            self,
            "差し込み画像を削除",
            "選択した差し込み画像を文から削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.targets[target_index][1].remove_inline_image(image_id)
        self._refresh_placement_list()

    def cleanup_unused_images(self):
        used = referenced_asset_ids(
            self.all_image_widgets
        )
        unused = [
            asset_id
            for asset_id in self.assets
            if asset_id not in used
        ]
        if not unused:
            QMessageBox.information(
                self,
                "未使用画像の整理",
                "未使用の登録画像はありません。",
            )
            return

        answer = QMessageBox.question(
            self,
            "未使用画像の整理",
            f"未使用の画像{len(unused)}件をプロジェクトから削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        failed = []
        for asset_id in unused:
            asset = self.assets[asset_id]
            try:
                path = resolve_asset_path(
                    self.project_root,
                    asset["path"],
                )
                if os.path.isfile(path):
                    os.remove(path)
                del self.assets[asset_id]
            except (InlineImageError, OSError):
                failed.append(asset.get("name", asset_id))
                continue

            self._delete_rendered_files(asset_id)

        BlackOutText.set_image_assets(self.assets, self.project_root)
        self._refresh_asset_combo()
        if failed:
            QMessageBox.warning(
                self,
                "未使用画像の整理",
                "削除できなかった画像があります:\n" + "\n".join(failed),
            )

    def _refresh_asset_combo(self, selected_id=None):
        if selected_id is None:
            selected_id = self.asset_combo.currentData()
        self.asset_combo.blockSignals(True)
        self.asset_combo.clear()
        for asset_id, asset in self.assets.items():
            self.asset_combo.addItem(asset["name"], asset_id)
        self.asset_combo.blockSignals(False)

        index = self.asset_combo.findData(selected_id)
        if index >= 0:
            self.asset_combo.setCurrentIndex(index)
        elif self.asset_combo.count():
            self.asset_combo.setCurrentIndex(0)
        self._asset_changed()

    def _refresh_placement_list(self, selected_id=None):
        self.placement_list.clear()
        selected_item = None
        blackout_names = {
            BLACKOUT_NONE: "黒塗りなし",
            BLACKOUT_OPAQUE: "透明部分以外",
            BLACKOUT_ALL: "画像全体",
        }
        for target_index, (target_name, target) in enumerate(self.targets):
            for image in target.get_inline_images():
                asset = self.assets.get(image["asset_id"], {})
                text = (
                    f"{target_name}｜{asset.get('name', '画像なし')}｜"
                    f"位置 {image['position']}｜"
                    f"{image['width']}×{image['height']} px｜"
                    f"{blackout_names[image['blackout']]}"
                )
                item = QListWidgetItem(text)
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    (target_index, image["id"]),
                )
                self.placement_list.addItem(item)
                if image["id"] == selected_id:
                    selected_item = item
        if selected_item:
            self.placement_list.setCurrentItem(selected_item)

    def _target_changed(self, _index=None):
        target = self._current_target()
        if target is None:
            self.target_preview.set_content("")
            self.position.setMaximum(0)
            return
        self.target_preview.set_content(target.get_text())
        self.position.setMaximum(len(target.get_text()))
        self.target_preview.set_position(self.position.value())

    def _position_changed(self, value):
        self.position_hint.setText(f"{value}文字目")
        self.target_preview.set_position(value)

    def _asset_changed(self, _index=None):
        asset = self.assets.get(self.asset_combo.currentData())
        if asset:
            self._set_default_size(asset)
            try:
                path = resolve_asset_path(
                    self.project_root,
                    asset["path"],
                )
            except InlineImageError:
                path = ""
            pixmap = QPixmap(path) if path else QPixmap()
            if pixmap.isNull():
                self.asset_preview.setPixmap(QPixmap())
                self.asset_preview.setText("画像が見つかりません。再リンクしてください。")
            else:
                self.asset_preview.setText("")
                self.asset_preview.setPixmap(
                    pixmap.scaled(
                        self.asset_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        else:
            self.asset_preview.setPixmap(QPixmap())
            self.asset_preview.setText("画像を登録してください")

    def _set_default_size(self, asset):
        scale = min(1.0, 160 / max(asset["width"], asset["height"]))
        self._set_size(
            max(8, round(asset["width"] * scale)),
            max(8, round(asset["height"] * scale)),
        )

    def _width_changed(self, value):
        if self._updating_size or not self.keep_aspect.isChecked():
            return
        asset = self.assets.get(self.asset_combo.currentData())
        if not asset:
            return
        height = round(value * asset["height"] / asset["width"])
        self._set_size(value, height)

    def _height_changed(self, value):
        if self._updating_size or not self.keep_aspect.isChecked():
            return
        asset = self.assets.get(self.asset_combo.currentData())
        if not asset:
            return
        width = round(value * asset["width"] / asset["height"])
        self._set_size(width, value)

    def _set_size(self, width, height):
        self._updating_size = True
        self.width.setValue(max(8, min(800, width)))
        self.height.setValue(max(8, min(800, height)))
        self._updating_size = False

    def _placement_selected(self, item, _previous=None):
        if item is None:
            return
        target_index, image_id = item.data(Qt.ItemDataRole.UserRole)
        target = self.targets[target_index][1]
        image = next(
            (
                current
                for current in target.get_inline_images()
                if current["id"] == image_id
            ),
            None,
        )
        if image is None:
            return
        self.target_combo.setCurrentIndex(target_index)
        asset_index = self.asset_combo.findData(image["asset_id"])
        if asset_index >= 0:
            self.asset_combo.setCurrentIndex(asset_index)
        self.position.setValue(image["position"])
        self._set_size(image["width"], image["height"])
        blackout_index = self.blackout.findData(image["blackout"])
        if blackout_index >= 0:
            self.blackout.setCurrentIndex(blackout_index)

    def _current_target(self):
        index = self.target_combo.currentIndex()
        if 0 <= index < len(self.targets):
            return self.targets[index][1]
        return None

    def _delete_rendered_files(self, asset_id):
        rendered_directory = os.path.join(
            self.project_root,
            "picture",
            "inline",
            ".rendered",
        )
        for mode in (BLACKOUT_OPAQUE, BLACKOUT_ALL):
            rendered_path = os.path.join(
                rendered_directory,
                f"{asset_id}-{mode}.png",
            )
            try:
                if os.path.isfile(rendered_path):
                    os.remove(rendered_path)
            except OSError:
                pass


def _target_label(name, text):
    """差し込み先プルダウン用に、カギ名と本文の先頭を組み合わせる。"""
    summary = text.replace("\n", " ").strip()
    if len(summary) > 16:
        summary = summary[:16] + "…"
    if not summary:
        return name
    return f"{name}：{summary}"
