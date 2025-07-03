# formlib.py
import os
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QAction,
    QGridLayout,
    QVBoxLayout,
    QBoxLayout,
    QApplication,
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QInputDialog,
)
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt

from .jsonio import JsonFileBuilder

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
