from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.lib.crosswordlib.board_enumerator import (
    BLACK,
    NUMBERING_LEFT_PRIORITY,
    NUMBERING_TOP_PRIORITY,
    BoardEnumerationError,
    enumerate_boards,
    parse_clue_pattern_text,
)


class EnumerationWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int, int, int)

    def __init__(
        self,
        vertical,
        horizontal,
        sizes,
        modes,
        limit,
    ):
        super().__init__()
        self.vertical = vertical
        self.horizontal = horizontal
        self.sizes = sizes
        self.modes = modes
        self.limit = limit
        self.cancel_requested = False

    @pyqtSlot()
    def run(self):
        try:
            outcome = enumerate_boards(
                self.vertical,
                self.horizontal,
                sizes=self.sizes,
                numbering_modes=self.modes,
                limit=self.limit,
                is_cancelled=lambda: self.cancel_requested,
                on_progress=self.progress.emit,
            )
            self.finished.emit(outcome)
        except BoardEnumerationError as error:
            self.failed.emit(str(error))
        except Exception as error:
            self.failed.emit(f"探索中にエラーが発生しました: {error}")

    def cancel(self):
        self.cancel_requested = True


class BoardPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.candidate = None
        self.setMinimumSize(300, 300)

    def set_candidate(self, candidate):
        self.candidate = candidate
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("white"))
        if self.candidate is None:
            painter.setPen(QColor("#666666"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "候補盤面を選択してください",
            )
            painter.end()
            return

        size = self.candidate.size
        side = min(self.width(), self.height()) - 20
        cell_size = max(1, side // size)
        board_size = cell_size * size
        left = (self.width() - board_size) // 2
        top = (self.height() - board_size) // 2

        painter.setPen(QPen(QColor("black"), 1))
        for row in range(size):
            for col in range(size):
                x = left + col * cell_size
                y = top + row * cell_size
                if self.candidate.grid[row][col] == BLACK:
                    painter.fillRect(
                        x,
                        y,
                        cell_size,
                        cell_size,
                        QColor("black"),
                    )
                else:
                    painter.fillRect(
                        x,
                        y,
                        cell_size,
                        cell_size,
                        QColor("white"),
                    )
                painter.drawRect(x, y, cell_size, cell_size)
        painter.setPen(QPen(QColor("black"), 3))
        painter.drawRect(left, top, board_size, board_size)
        painter.end()


class BoardEnumeratorPanel(QDialog):
    def __init__(
        self,
        vertical_pattern,
        horizontal_pattern,
        on_apply,
        parent=None,
    ):
        super().__init__(parent)
        self.on_apply = on_apply
        self.outcome = None
        self.thread = None
        self.worker = None
        self.close_after_finish = False

        self.setWindowTitle("カギ番号から盤面を列挙")
        self.resize(980, 680)

        base = QVBoxLayout(self)
        help_text = QLabel(
            "番号は空白またはカンマで区切ります。見えない番号は「黒」と"
            "入力してください。盤面サイズを固定せず、指定範囲を探索します。"
        )
        help_text.setWordWrap(True)
        base.addWidget(help_text)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self.vertical_input = QLineEdit(
            _format_pattern(vertical_pattern)
        )
        self.horizontal_input = QLineEdit(
            _format_pattern(horizontal_pattern)
        )

        size_widget = QWidget()
        size_row = QHBoxLayout(size_widget)
        size_row.setContentsMargins(0, 0, 0, 0)
        self.minimum_size = QSpinBox()
        self.minimum_size.setRange(4, 9)
        self.minimum_size.setValue(4)
        self.maximum_size = QSpinBox()
        self.maximum_size.setRange(4, 9)
        self.maximum_size.setValue(9)
        size_row.addWidget(self.minimum_size)
        size_row.addWidget(QLabel("～"))
        size_row.addWidget(self.maximum_size)
        size_row.addStretch()

        self.numbering_mode = QComboBox()
        self.numbering_mode.addItem(
            "不明（上優先・左優先を両方探索）",
            (
                NUMBERING_TOP_PRIORITY,
                NUMBERING_LEFT_PRIORITY,
            ),
        )
        self.numbering_mode.addItem(
            "上優先",
            (NUMBERING_TOP_PRIORITY,),
        )
        self.numbering_mode.addItem(
            "左優先",
            (NUMBERING_LEFT_PRIORITY,),
        )

        limit_widget = QWidget()
        limit_row = QHBoxLayout(limit_widget)
        limit_row.setContentsMargins(0, 0, 0, 0)
        self.result_limit = QSpinBox()
        self.result_limit.setRange(1, 1000000)
        self.result_limit.setValue(1000)
        self.no_limit = QCheckBox("上限なし（全列挙）")
        self.no_limit.toggled.connect(
            lambda checked: self.result_limit.setDisabled(checked)
        )
        limit_row.addWidget(self.result_limit)
        limit_row.addWidget(self.no_limit)
        limit_row.addStretch()

        form.addRow("タテのカギ番号", self.vertical_input)
        form.addRow("ヨコのカギ番号", self.horizontal_input)
        form.addRow("盤面サイズ", size_widget)
        form.addRow("採番方式", self.numbering_mode)
        form.addRow("結果件数", limit_widget)
        base.addWidget(form_widget)

        action_row = QHBoxLayout()
        self.start_button = QPushButton("探索開始")
        self.start_button.clicked.connect(self.start_search)
        self.cancel_button = QPushButton("探索を中断")
        self.cancel_button.clicked.connect(self.cancel_search)
        self.cancel_button.setDisabled(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.status = QLabel("探索条件を入力してください")
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.cancel_button)
        action_row.addWidget(self.progress, 1)
        action_row.addWidget(self.status)
        base.addLayout(action_row)

        splitter = QSplitter()
        self.result_list = QListWidget()
        self.result_list.currentItemChanged.connect(
            self.result_selected
        )
        self.preview = BoardPreview()
        splitter.addWidget(self.result_list)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        base.addWidget(splitter, 1)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(QLabel("反映時の採番方式"))
        self.apply_mode = QComboBox()
        bottom_row.addWidget(self.apply_mode)
        bottom_row.addStretch()
        self.apply_button = QPushButton("選択した盤面を反映")
        self.apply_button.clicked.connect(self.apply_selected)
        self.apply_button.setDisabled(True)
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.reject)
        bottom_row.addWidget(self.apply_button)
        bottom_row.addWidget(close_button)
        base.addLayout(bottom_row)

    def start_search(self):
        if self.thread is not None:
            return
        try:
            vertical = parse_clue_pattern_text(
                self.vertical_input.text()
            )
            horizontal = parse_clue_pattern_text(
                self.horizontal_input.text()
            )
            minimum = self.minimum_size.value()
            maximum = self.maximum_size.value()
            if minimum > maximum:
                raise BoardEnumerationError(
                    "盤面サイズの最小値が最大値を超えています"
                )
        except BoardEnumerationError as error:
            QMessageBox.warning(self, "探索条件エラー", str(error))
            return

        limit = None if self.no_limit.isChecked() else self.result_limit.value()
        if limit is None:
            answer = QMessageBox.question(
                self,
                "全列挙を開始",
                "候補数によっては探索に時間がかかります。"
                "件数上限なしで開始しますか？",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.result_list.clear()
        self.preview.set_candidate(None)
        self.apply_mode.clear()
        self.apply_button.setDisabled(True)
        self.outcome = None
        self.start_button.setDisabled(True)
        self.cancel_button.setEnabled(True)
        self.progress.setRange(0, 0)
        self.status.setText("探索中…")

        self.thread = QThread(self)
        self.worker = EnumerationWorker(
            vertical,
            horizontal,
            range(minimum, maximum + 1),
            self.numbering_mode.currentData(),
            limit,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.search_finished)
        self.worker.failed.connect(self.search_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.search_thread_finished)
        self.thread.start()

    def cancel_search(self):
        if self.worker is not None:
            self.worker.cancel()
            self.status.setText("中断しています…")
            self.cancel_button.setDisabled(True)

    def update_progress(self, explored, found, size):
        self.status.setText(
            f"{size}×{size}：{explored:,}状態／{found:,}件"
        )

    def search_finished(self, outcome):
        self.outcome = outcome
        for index, candidate in enumerate(outcome.results, start=1):
            modes = "・".join(
                _mode_name(match.mode)
                for match in candidate.numberings
            )
            item = QListWidgetItem(
                f"{candidate.size}×{candidate.size}　候補{index}　{modes}"
            )
            item.setData(Qt.ItemDataRole.UserRole, index - 1)
            self.result_list.addItem(item)

        suffix = ""
        if outcome.cancelled:
            suffix = "（中断）"
        elif outcome.truncated:
            suffix = "（件数上限に到達）"
        self.status.setText(
            f"{len(outcome.results):,}件"
            f"／{outcome.stats.explored_states:,}状態 {suffix}"
        )
        if self.result_list.count():
            self.result_list.setCurrentRow(0)

    def search_failed(self, message):
        QMessageBox.critical(self, "盤面探索エラー", message)
        self.status.setText("探索に失敗しました")

    def search_thread_finished(self):
        if self.worker is not None:
            self.worker.deleteLater()
        if self.thread is not None:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.start_button.setEnabled(True)
        self.cancel_button.setDisabled(True)
        if self.close_after_finish:
            self.accept()

    def result_selected(self, item, _previous=None):
        if item is None or self.outcome is None:
            self.preview.set_candidate(None)
            self.apply_button.setDisabled(True)
            return
        candidate = self.outcome.results[
            item.data(Qt.ItemDataRole.UserRole)
        ]
        self.preview.set_candidate(candidate)
        self.apply_mode.clear()
        for match in candidate.numberings:
            self.apply_mode.addItem(_mode_name(match.mode), match.mode)
        self.apply_button.setEnabled(True)

    def apply_selected(self):
        item = self.result_list.currentItem()
        if item is None or self.outcome is None:
            return
        candidate = self.outcome.results[
            item.data(Qt.ItemDataRole.UserRole)
        ]
        self.on_apply(candidate, self.apply_mode.currentData())
        self.accept()

    def closeEvent(self, event):
        if self.worker is None:
            event.accept()
            return
        self.close_after_finish = True
        self.cancel_search()
        event.ignore()

    def reject(self):
        if self.worker is None:
            return super().reject()
        self.close_after_finish = True
        self.cancel_search()


def _format_pattern(pattern):
    return " ".join(
        "黒" if value is None else str(value)
        for value in pattern
    )


def _mode_name(mode):
    if mode == NUMBERING_TOP_PRIORITY:
        return "上優先"
    return "左優先"
