@echo off
set CUR=%~dp0
pyinstaller -F ResTool.py --distpath=%CUR%/bin
pause