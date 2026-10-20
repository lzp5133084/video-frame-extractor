# -*- coding: utf-8 -*-
"""登录/注册窗口（多用户，规则8）"""
import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QWidget)

from core import database
from . import theme


class LoginWindow(QWidget):
    login_ok = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{theme.APP_NAME} - 用户登录")
        self.resize(460, 560)
        self._build()
        self._reg_mode = False

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 36, 40, 32)
        lay.setSpacing(14)

        # LOGO 区
        logo = QLabel("⬡")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"font-size:52px; color:{theme.GOLD}; background:transparent;")
        title = QLabel(theme.APP_NAME)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel(f"多人模式 · 由 {theme.AUTHOR} 打造")
        sub.setObjectName("subtitleLabel")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(10)

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(26, 24, 26, 24)
        cl.setSpacing(12)

        self.ed_user = QLineEdit()
        self.ed_user.setPlaceholderText("用户名")
        self.ed_pwd = QLineEdit()
        self.ed_pwd.setPlaceholderText("密码")
        self.ed_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.ed_pwd2 = QLineEdit()
        self.ed_pwd2.setPlaceholderText("确认密码（注册模式）")
        self.ed_pwd2.setEchoMode(QLineEdit.EchoMode.Password)
        self.ed_pwd2.setVisible(False)

        self.btn_ok = QPushButton("登 录")
        self.btn_ok.setObjectName("goldBtn")
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.clicked.connect(self._submit)
        self.btn_switch = QPushButton("没有账号？立即注册 →")
        self.btn_switch.setFlat(True)
        self.btn_switch.setStyleSheet(
            f"background:transparent; color:{theme.CYAN}; border:none;")
        self.btn_switch.clicked.connect(self._switch_mode)

        for w in (self.ed_user, self.ed_pwd, self.ed_pwd2, self.btn_ok):
            cl.addWidget(w)
        cl.addWidget(self.btn_switch)
        lay.addWidget(card)

        # 初始管理员提示
        tip = QLabel("首次使用默认管理员：admin / admin123")
        tip.setObjectName("hintLabel")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(tip)
        foot = QLabel(f"作者：{theme.AUTHOR}　微信：{theme.WECHAT}")
        foot.setObjectName("hintLabel")
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(foot)

        self.ed_user.setFocus()

    def _switch_mode(self):
        self._reg_mode = not self._reg_mode
        self.ed_pwd2.setVisible(self._reg_mode)
        self.btn_ok.setText("注 册" if self._reg_mode else "登 录")
        self.btn_switch.setText("已有账号？返回登录 →" if self._reg_mode
                                else "没有账号？立即注册 →")

    def _submit(self):
        u, p = self.ed_user.text().strip(), self.ed_pwd.text()
        if not u or not p:
            self._msg("请输入用户名和密码")
            return
        if self._reg_mode:
            if p != self.ed_pwd2.text():
                self._msg("两次密码不一致")
                return
            r = database.add_user(u, p)
            if r != "ok":
                self._msg(r)
                return
        user = database.verify_user(u, p)
        if not user:
            self._msg("用户名或密码错误")
            return
        self.login_ok.emit(user)

    def _msg(self, text):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "提示", text)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._submit()
