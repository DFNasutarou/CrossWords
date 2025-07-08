@echo off
pyinstaller --onefile --windowed --name CrossMaker --paths app app\__main__.py
pause