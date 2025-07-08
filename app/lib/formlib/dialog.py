# formlib.py
from PyQt5.QtWidgets import (
    QInputDialog,
)

PICTURE_FOLDER_NNAME = "picture"
DATA_FILE_NAME = "data.json"


class Dialog:
    @staticmethod
    def getText(parent=None, title="", message=""):
        name, ok = QInputDialog.getText(
            parent,
            title,
            message,
        )
        return name, ok
