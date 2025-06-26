"""
cd 'C:/workspace/github/nasu/CrossWords'
python -m app
"""

from .lib.formlib import formlib
from .lib.formlib.layouts import Row, Column, Table
from .lib.formlib.widgets import CellMaker, InstructionBar, ClueEditor, TextInputMaker

def main():
    app = formlib.Application(Column())
    make_tree_data(app)
    app.run()
    
def make_tree_data(app):
    app.add([], InstructionBar('最終指示をここに表示', font_size=30, size=[800, 120]))
    app.add([], Row())
    app.add([1], CellMaker(5, 80))
    app.add([1], Column())
    app.add([1, 1], Column())
    app.add([1, 1, 0], InstructionBar('タテのカギ'))
    app.add([1, 1, 0], TextInputMaker(''), size = -1)
    app.add([1, 1], Column())
    app.add([1, 1, 1], InstructionBar('ヨコのカギ'))


