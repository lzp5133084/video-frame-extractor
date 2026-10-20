# -*- coding: utf-8 -*-
"""用户管理页（管理员：增删查改；普通用户：改自己密码）"""
from PyQt6.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from core import database
from . import theme


class UsersPage(QWidget):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 14)
        lay.setSpacing(12)

        head = QHBoxLayout()
        t = QLabel("用户管理")
        t.setObjectName("titleLabel")
        self.lbl_tip = QLabel("")
        self.lbl_tip.setObjectName("hintLabel")
        head.addWidget(t)
        head.addStretch(1)
        head.addWidget(self.lbl_tip)
        lay.addLayout(head)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "用户名", "角色", "创建时间", "最后登录"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table, 1)

        if self.user["role"] == "admin":
            ops = QHBoxLayout()
            self.ed_name = QLineEdit(); self.ed_name.setPlaceholderText("新用户名")
            self.ed_pwd = QLineEdit(); self.ed_pwd.setPlaceholderText("初始密码")
            btn_add = QPushButton("添加用户")
            btn_add.setObjectName("goldBtn")
            btn_add.clicked.connect(self._add)
            btn_role = QPushButton("切换为管理员/普通")
            btn_role.clicked.connect(self._toggle_role)
            btn_reset = QPushButton("重置密码")
            btn_reset.clicked.connect(self._reset_pwd)
            btn_del = QPushButton("删除用户")
            btn_del.setObjectName("dangerBtn")
            btn_del.clicked.connect(self._delete)
            for w in (self.ed_name, self.ed_pwd, btn_add, btn_role, btn_reset, btn_del):
                ops.addWidget(w)
            lay.addLayout(ops)

        me = QHBoxLayout()
        self.ed_newpwd = QLineEdit(); self.ed_newpwd.setPlaceholderText("修改本人密码：输入新密码")
        self.ed_newpwd.setEchoMode(QLineEdit.EchoMode.Password)
        btn_me = QPushButton("确认修改本人密码")
        btn_me.clicked.connect(self._change_me)
        me.addWidget(self.ed_newpwd, 1)
        me.addWidget(btn_me)
        lay.addLayout(me)

    def refresh(self):
        rows = database.list_users()
        self.table.setRowCount(len(rows))
        for i, u in enumerate(rows):
            for j, v in enumerate([str(u["id"]), u["username"], u["role"],
                                   u["created_at"], u["last_login"] or "-"]):
                self.table.setItem(i, j, QTableWidgetItem(v))
        self.rows = rows
        self.lbl_tip.setText("管理员可增删查改全部用户" if self.user["role"] == "admin"
                             else "普通用户仅可修改本人密码")

    def _sel_uid(self):
        r = self.table.currentRow()
        return self.rows[r]["id"] if 0 <= r < len(self.rows) else None

    def _add(self):
        r = database.add_user(self.ed_name.text().strip(), self.ed_pwd.text())
        if r != "ok":
            QMessageBox.warning(self, "提示", r)
        self.ed_name.clear(); self.ed_pwd.clear()
        self.refresh()

    def _toggle_role(self):
        uid = self._sel_uid()
        if uid is None:
            return
        row = next((u for u in self.rows if u["id"] == uid), None)
        database.change_role(uid, "user" if row["role"] == "admin" else "admin")
        self.refresh()

    def _reset_pwd(self):
        uid = self._sel_uid()
        if uid is None:
            return
        r = database.reset_password(uid, "123456")
        if r == "ok":
            QMessageBox.information(self, "完成", "密码已重置为 123456")
        self.refresh()

    def _delete(self):
        uid = self._sel_uid()
        if uid is None:
            return
        r = database.delete_user(uid)
        if r != "ok":
            QMessageBox.warning(self, "提示", r)
        self.refresh()

    def _change_me(self):
        if not self.ed_newpwd.text():
            QMessageBox.information(self, "提示", "请先输入新密码")
            return
        from PyQt6.QtWidgets import QInputDialog
        old_pwd, ok = QInputDialog.getText(self, "验证", "请输入原密码：",
                                           QLineEdit.EchoMode.Password)
        if not ok:
            return
        r = database.change_own_password(self.user["id"], old_pwd,
                                         self.ed_newpwd.text())
        if r == "ok":
            QMessageBox.information(self, "完成", "密码修改成功")
            self.ed_newpwd.clear()
        else:
            QMessageBox.warning(self, "失败", r)
