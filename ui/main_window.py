# -*- coding: utf-8 -*-
"""主窗口：左侧导航 + 多页面（2027 黑金科技风）"""
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QMainWindow, QPushButton,
                             QStackedWidget, QVBoxLayout, QWidget)

from core import database
from . import theme


class MainWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"{theme.APP_NAME} {theme.APP_VERSION} - {user['username']}")
        self.resize(1180, 760)
        self.setMinimumSize(QSize(980, 640))
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 侧边导航
        side = QFrame()
        side.setFixedWidth(212)
        side.setStyleSheet(
            f"background:{theme.BG_CARD}; border-right:1px solid #232b42;")
        sl = QVBoxLayout(side)
        sl.setContentsMargins(10, 20, 10, 12)
        sl.setSpacing(6)

        logo = QLabel("⬡ 单帧提取")
        logo.setObjectName("titleLabel")
        logo.setStyleSheet(f"font-size:19px; color:{theme.GOLD}; background:transparent;")
        sl.addWidget(logo)
        sl.addSpacing(10)

        self.nav = QListWidget()
        self.nav.setObjectName("navList")
        items = ["🎬 视频处理", "🕘 历史记录"]
        if self.user["role"] == "admin":
            items.append("👥 用户管理")
        items.append("⚙ 压缩档位")
        items.append("ℹ 关于·自检")
        for it in items:
            self.nav.addItem(QListWidgetItem(it))
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._switch)
        sl.addWidget(self.nav, 1)

        user_card = QLabel(f"👤 {self.user['username']}（{self.user['role']}）")
        user_card.setObjectName("hintLabel")
        btn_logout = QPushButton("退出登录")
        btn_logout.clicked.connect(self._logout)
        sl.addWidget(user_card)
        sl.addWidget(btn_logout)
        root.addWidget(side)

        # 页面栈
        self.stack = QStackedWidget()
        from .process_page import ProcessPage
        from .history_page import HistoryPage
        from .presets_page import PresetsPage
        from .about_page import AboutPage

        self.page_process = ProcessPage(self.user)
        self.page_history = HistoryPage(self.user, self.page_process)
        self.stack.addWidget(self.page_process)          # 0
        self.stack.addWidget(self.page_history)          # 1
        if self.user["role"] == "admin":
            from .users_page import UsersPage
            self.page_users = UsersPage(self.user)
            self.stack.addWidget(self.page_users)        # 2
        self.page_presets = PresetsPage(standalone=False)  # 页面形态复用
        self.stack.addWidget(self.page_presets)
        self.page_about = AboutPage(self)
        self.stack.addWidget(self.page_about)
        root.addWidget(self.stack, 1)

        # 状态栏：作者信息（规则4）
        sb = self.statusBar()
        lbl_author = QLabel(f"作者：{theme.AUTHOR}　微信：{theme.WECHAT}")
        lbl_author.setObjectName("authorLabel")
        sb.addPermanentWidget(lbl_author)
        sb.showMessage(f"{theme.APP_NAME} {theme.APP_VERSION}｜多人模式已就绪")

    def _switch(self, idx):
        # admin 多一个用户管理页，导航与栈天然对齐
        self.stack.setCurrentIndex(idx)
        if self.nav.item(idx) and "历史" in self.nav.item(idx).text():
            self.page_history.refresh()
        if self.nav.item(idx) and "用户" in self.nav.item(idx).text():
            self.page_users.refresh()
        if self.nav.item(idx) and "关于" in self.nav.item(idx).text():
            self.page_about.run_check()

    def _logout(self):
        from .login import LoginWindow
        self.login_win = LoginWindow()
        self.login_win.login_ok.connect(self._relogin)
        self.login_win.show()
        self.close()

    def _relogin(self, user: dict):
        self.new_win = MainWindow(user)
        self.new_win.show()
