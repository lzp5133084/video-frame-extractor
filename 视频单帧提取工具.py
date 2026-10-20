# -*- coding: utf-8 -*-
"""视频单帧提取工具 - 主入口
作者：军哥懂保  微信：xunijiayuan

功能：视频快速压缩（5档可自定义）→ 静止画面检测（阈值自定义）→
      单帧提取 → 生成 PPT / 动态 GIF
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from ui import theme
from ui.login import LoginWindow
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(theme.QSS)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setApplicationName(theme.APP_NAME)

    win_holder = {}

    def on_login(user: dict):
        win_holder["main"] = MainWindow(user)
        win_holder["main"].show()
        login.close()

    login = LoginWindow()
    login.login_ok.connect(on_login)
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
