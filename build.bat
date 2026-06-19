@echo off
@REM pyinstaller --clean --noconfirm tools_v3.spec
pyinstaller --exclude-module PyQt5 --onefile --noconsole --icon=icon.ico tools_v3.py