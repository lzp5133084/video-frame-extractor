# -*- coding: utf-8 -*-
"""无头自检：模拟登录成功后创建主窗口（admin 与普通用户两种角色）"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from ui import theme
from ui.main_window import MainWindow
from core import database

app = QApplication(sys.argv)
app.setStyleSheet(theme.QSS)

for u, p in [("admin", "admin123"), ("test_plain", "t123456")]:
    if not database.verify_user(u, p):
        database.add_user(u, p)
        user = database.verify_user(u, p)
    else:
        user = database.verify_user(u, p)
    win = MainWindow(user)  # 曾在 AboutPage 崩溃
    win.close()
    print(f"[OK] {u}({user['role']}) 主窗口创建成功")

print("登录后主窗口流程全部通过")
