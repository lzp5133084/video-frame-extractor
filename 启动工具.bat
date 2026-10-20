@echo off
chcp 65001 >nul
title 视频单帧提取工具 - 军哥懂保
cd /d "%~dp0"
start "" "runtime\py312\pythonw.exe" "视频单帧提取工具.py"
