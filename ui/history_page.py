# -*- coding: utf-8 -*-
"""历史记录页：增删查改 + 一键复用参数（规则5）"""
import json
import os

from PyQt6.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)

from core import database
from . import theme


class HistoryPage(QWidget):
    def __init__(self, user: dict, process_page):
        super().__init__()
        self.user = user
        self.process_page = process_page
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 14)
        lay.setSpacing(12)

        head = QHBoxLayout()
        t = QLabel("历史记录")
        t.setObjectName("titleLabel")
        self.lbl_scope = QLabel("")
        self.lbl_scope.setObjectName("hintLabel")
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh)
        head.addWidget(t)
        head.addStretch(1)
        head.addWidget(self.lbl_scope)
        head.addWidget(btn_refresh)
        lay.addLayout(head)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "用户", "视频", "档位", "阈值", "帧数", "耗时s", "时间"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        lay.addWidget(self.table, 1)

        row = QHBoxLayout()
        btn_reuse = QPushButton("一键复用参数到处理页")
        btn_reuse.setObjectName("goldBtn")
        btn_reuse.clicked.connect(self._reuse)
        btn_detail = QPushButton("查看详情")
        btn_detail.clicked.connect(self._detail)
        btn_open = QPushButton("打开输出目录")
        btn_open.clicked.connect(self._open_dir)
        btn_del = QPushButton("删除记录")
        btn_del.setObjectName("dangerBtn")
        btn_del.clicked.connect(self._delete)
        row.addWidget(btn_reuse)
        row.addWidget(btn_detail)
        row.addWidget(btn_open)
        row.addStretch(1)
        row.addWidget(btn_del)
        lay.addLayout(row)

    def refresh(self):
        rows = database.list_history(None if self.user["role"] == "admin"
                                     else self.user["id"])
        self.lbl_scope.setText("范围：全部用户" if self.user["role"] == "admin"
                               else "范围：仅本人")
        self.table.setRowCount(len(rows))
        for i, h in enumerate(rows):
            vals = [str(h["id"]), h.get("username") or "-", h["video_name"],
                    h["preset_name"], str(h["threshold"]), str(h["frame_count"]),
                    str(h["cost_sec"]), h["created_at"]]
            for j, v in enumerate(vals):
                self.table.setItem(i, j, QTableWidgetItem(v))
        self.rows = rows

    def _sel(self):
        r = self.table.currentRow()
        if r < 0 or r >= len(self.rows):
            return None
        return self.rows[r]

    def _reuse(self):
        h = self._sel()
        if not h:
            QMessageBox.information(self, "提示", "请先选中一条记录")
            return
        self.process_page.apply_history(h)
        QMessageBox.information(self, "完成",
                                "已将参数填回处理页，可直接开始处理")

    def _detail(self):
        h = self._sel()
        if not h:
            return
        try:
            p = json.loads(h.get("params_json") or "{}")
        except Exception:
            p = {}
        info = (f"记录 #{h['id']}\n\n用户：{h.get('username','-')}\n"
                f"视频：{h['video_path']}\n压缩档位：{h['preset_name']}\n"
                f"静止阈值：{h['threshold']}\n提取帧数：{h['frame_count']}\n"
                f"耗时：{h['cost_sec']}s\n时间：{h['created_at']}\n\n"
                f"参数详情：{json.dumps(p, ensure_ascii=False, indent=2)}")
        QMessageBox.information(self, f"记录详情 #{h['id']}", info)

    def _open_dir(self):
        h = self._sel()
        if h and h.get("out_dir") and os.path.isdir(h["out_dir"]):
            os.startfile(h["out_dir"])
        else:
            QMessageBox.information(self, "提示", "输出目录不存在或已清理")

    def _delete(self):
        h = self._sel()
        if not h:
            return
        if QMessageBox.question(self, "确认", f"确定删除记录 #{h['id']}？") == \
                QMessageBox.StandardButton.Yes:
            database.delete_history(h["id"])
            self.refresh()
