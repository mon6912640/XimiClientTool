@echo off
set CUR=%~dp0
pyinstaller -F LanTool.py --distpath=%CUR%/bin
pause