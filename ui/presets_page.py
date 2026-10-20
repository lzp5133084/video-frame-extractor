# -*- coding: utf-8 -*-
"""压缩档位自定义（5档 增删查改）+ 检测默认参数"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QDoubleSpinBox, QHBoxLayout, QMessageBox,
                             QPushButton, QSpinBox, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QHeaderView,
                             QLabel, QLineEdit, QWidget)

from core import api
from . import theme


class PresetsPage(QDialog):
    def __init__(self, parent=None, standalone=False):
        super().__init__(parent)
        self._embedded = not standalone  # 嵌入主窗口形态
        self.setWindowTitle("压缩档位自定义")
        self.resize(760, 460)
        if standalone:
            self.setWindowFlag(Qt.WindowType.Window)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        tip = QLabel("每档可自定义名称 / CRF画质(越小越清晰) / 限制高度(0=原画) / 编码速度，保存后立即生效")
        tip.setObjectName("hintLabel")
        lay.addWidget(tip)

        self.table = QTableWidget(5, 5)
        self.table.setHorizontalHeaderLabels(["档位名称", "CRF 画质", "限制高度p", "编码速度", "说明"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.table, 1)
        self._load()

        row = QHBoxLayout()
        btn_save = QPushButton("保存配置")
        btn_save.setObjectName("goldBtn")
        btn_save.clicked.connect(self._save)
        btn_reset = QPushButton("恢复默认")
        btn_reset.clicked.connect(self._reset)
        row.addStretch(1)
        row.addWidget(btn_reset)
        row.addWidget(btn_save)
        lay.addLayout(row)

        # 检测默认阈值
        det = api.load_config()["detect"]
        dr = QHBoxLayout()
        dr.addWidget(QLabel("默认静止阈值"))
        self.spn_def_th = QDoubleSpinBox()
        self.spn_def_th.setRange(0.01, 1.0)
        self.spn_def_th.setSingleStep(0.01)
        self.spn_def_th.setDecimals(2)
        self.spn_def_th.setValue(det["threshold"])
        dr.addWidget(self.spn_def_th)
        dr.addWidget(QLabel("采样帧率"))
        self.spn_fps = QDoubleSpinBox()
        self.spn_fps.setRange(0.5, 10)
        self.spn_fps.setSingleStep(0.5)
        self.spn_fps.setValue(det["sample_fps"])
        dr.addWidget(self.spn_fps)
        dr.addWidget(QLabel("帧/秒"))
        dr.addStretch(1)
        lay.addLayout(dr)

    def _load(self):
        presets = api.get_presets()
        self.table.setRowCount(max(len(presets), 5))
        for i, p in enumerate(presets):
            self.table.setItem(i, 0, QTableWidgetItem(p["name"]))
            sp = QSpinBox(); sp.setRange(0, 51); sp.setValue(p["crf"])
            self.table.setCellWidget(i, 1, sp)
            sp2 = QSpinBox(); sp2.setRange(0, 4320); sp2.setValue(p["height"])
            self.table.setCellWidget(i, 2, sp2)
            cb = QLineEdit(p["preset"])
            self.table.setCellWidget(i, 3, cb)
            self.table.setItem(i, 4, QTableWidgetItem(p.get("desc", "")))

    def _collect(self):
        out = []
        for i in range(self.table.rowCount()):
            name_item = self.table.item(i, 0)
            sp1 = self.table.cellWidget(i, 1)
            sp2 = self.table.cellWidget(i, 2)
            ed = self.table.cellWidget(i, 3)
            d_item = self.table.item(i, 4)
            if not name_item or not name_item.text().strip():
                continue
            out.append({"name": name_item.text().strip(),
                        "crf": sp1.value(), "height": sp2.value(),
                        "preset": (ed.text().strip() or "medium"),
                        "desc": d_item.text().strip() if d_item else ""})
        return out

    def _save(self):
        presets = self._collect()
        if len(presets) != 5:
            QMessageBox.warning(self, "提示", "请保持 5 个档位（名称不能为空）")
            return
        cfg = api.load_config()
        cfg["presets"] = presets
        cfg["detect"]["threshold"] = self.spn_def_th.value()
        cfg["detect"]["sample_fps"] = self.spn_fps.value()
        api.save_presets(presets)
        from core.compressor import save_config
        save_config(cfg)
        QMessageBox.information(self, "完成", "档位配置已保存，处理页下拉已生效")
        if not self._embedded:
            self.accept()

    def _reset(self):
        from core.compressor import DEFAULT_PRESETS, save_config
        save_config(DEFAULT_PRESETS)
        self._load()
