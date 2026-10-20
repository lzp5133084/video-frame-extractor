# -*- coding: utf-8 -*-
"""视频处理页：选择视频 → 5档压缩 → 阈值单帧提取 → PPT/GIF"""
import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
                             QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QMessageBox, QProgressBar, QPushButton, QScrollArea,
                             QSpinBox, QVBoxLayout, QWidget)

from core import api, database
from . import theme


class WorkThread(QThread):
    progress = pyqtSignal(float, str)   # percent, stage
    done = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, video_path, preset_index, threshold, want_ppt, want_gif,
                 gif_ms, gif_w):
        super().__init__()
        self.cancel_flag = [False]
        self.args = (video_path, preset_index, threshold, want_ppt, want_gif,
                     gif_ms, gif_w)

    def run(self):
        try:
            video_path, pidx, th, wp, wg, gms, gw = self.args
            self.progress.emit(2, "正在压缩视频…")

            def cb(pct, stage=""):
                self.progress.emit(pct, stage or "处理中")

            r = api.process_video(
                video_path, preset_index=pidx, threshold=th,
                make_ppt_flag=wp, make_gif_flag=wg,
                gif_duration_ms=gms, gif_width=gw,
                progress_cb=cb, cancel_flag=self.cancel_flag,
            )
            self.progress.emit(100, "完成")
            self.done.emit(r)
        except InterruptedError:
            self.failed.emit("任务已取消")
        except Exception as e:
            self.failed.emit(str(e))

    def cancel(self):
        self.cancel_flag[0] = True


class ProcessPage(QWidget):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.video_path = ""
        self.thread = None
        self.result = None
        self.setAcceptDrops(True)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 14)
        lay.setSpacing(12)

        head = QHBoxLayout()
        t = QLabel("视频处理")
        t.setObjectName("titleLabel")
        self.lbl_file = QLabel("未选择视频（支持拖入 mp4/avi/mov/mkv/flv）")
        self.lbl_file.setObjectName("hintLabel")
        btn_pick = QPushButton("选择视频")
        btn_pick.clicked.connect(self._pick)
        head.addWidget(t)
        head.addStretch(1)
        head.addWidget(self.lbl_file)
        head.addWidget(btn_pick)
        lay.addLayout(head)

        # 参数卡
        card = QFrame()
        card.setObjectName("card")
        g = QGridLayout(card)
        g.setContentsMargins(20, 16, 20, 16)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(12)

        g.addWidget(QLabel("压缩档位（可自定义）"), 0, 0)
        self.cmb_preset = QComboBox()
        self._reload_presets()
        g.addWidget(self.cmb_preset, 0, 1)
        btn_cfg = QPushButton("自定义档位…")
        btn_cfg.clicked.connect(self._open_presets)
        g.addWidget(btn_cfg, 0, 2)

        g.addWidget(QLabel("静止判定阈值"), 1, 0)
        th_box = QHBoxLayout()
        self.spn_th = QDoubleSpinBox()
        self.spn_th.setRange(0.01, 1.0)
        self.spn_th.setSingleStep(0.01)
        self.spn_th.setDecimals(2)
        self.spn_th.setValue(api.load_config()["detect"]["threshold"])
        self.lbl_th_hint = QLabel("越小保留帧越多；越大只保留明显切换的画面")
        self.lbl_th_hint.setObjectName("hintLabel")
        th_box.addWidget(self.spn_th)
        th_box.addWidget(self.lbl_th_hint, 1)
        g.addLayout(th_box, 1, 1, 1, 2)

        g.addWidget(QLabel("输出内容"), 2, 0)
        out_box = QHBoxLayout()
        self.chk_ppt = QCheckBox("生成 PPT（推荐）")
        self.chk_ppt.setChecked(True)
        self.chk_gif = QCheckBox("生成动态 GIF")
        self.chk_frames = QCheckBox("保留单帧图片")
        self.chk_frames.setChecked(True)
        for w in (self.chk_ppt, self.chk_gif, self.chk_frames):
            out_box.addWidget(w)
        out_box.addStretch(1)
        g.addLayout(out_box, 2, 1, 1, 2)

        gif_lab = QLabel("GIF 参数")
        g.addWidget(gif_lab, 3, 0)
        gif_box = QHBoxLayout()
        gif_box.addWidget(QLabel("每帧"))
        self.spn_ms = QSpinBox()
        self.spn_ms.setRange(100, 5000)
        self.spn_ms.setValue(800)
        self.spn_ms.setSuffix(" ms")
        gif_box.addWidget(self.spn_ms)
        gif_box.addWidget(QLabel("宽度"))
        self.spn_w = QSpinBox()
        self.spn_w.setRange(160, 1920)
        self.spn_w.setValue(640)
        gif_box.addWidget(self.spn_w)
        gif_box.addStretch(1)
        g.addLayout(gif_box, 3, 1, 1, 2)
        lay.addWidget(card)

        # 进度与操作
        self.bar = QProgressBar()
        self.bar.setValue(0)
        self.lbl_stage = QLabel("待就绪")
        self.lbl_stage.setObjectName("statusLabel")
        self.btn_run = QPushButton("开始处理")
        self.btn_run.setObjectName("goldBtn")
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.clicked.connect(self._run)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("dangerBtn")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_open = QPushButton("打开输出目录")
        self.btn_open.clicked.connect(self._open_out)
        self.btn_open.setVisible(False)

        row = QHBoxLayout()
        row.addWidget(self.lbl_stage, 1)
        row.addWidget(self.btn_open)
        row.addWidget(self.btn_cancel)
        row.addWidget(self.btn_run)
        lay.addWidget(self.bar)
        lay.addLayout(row)

        # 预览区
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        self.preview_lay = QVBoxLayout(inner)
        self.preview_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.preview_lay.setSpacing(10)
        self.scroll.setWidget(inner)
        lay.addWidget(self.scroll, 1)

    # ---------------- 基本交互 ----------------
    def _reload_presets(self):
        self.cmb_preset.clear()
        for p in api.get_presets():
            self.cmb_preset.addItem(f"{p['name']}｜CRF {p['crf']}｜{p['height'] or '原画'}p｜{p['desc']}")

    def _pick(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "", "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm);;所有文件 (*.*)")
        if f:
            self.set_video(f)

    def set_video(self, path: str):
        self.video_path = path
        self.lbl_file.setText(os.path.basename(path))
        self.lbl_file.setStyleSheet(f"color:{theme.GOLD};")

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        urls = e.mimeData().urls()
        if urls:
            self.set_video(urls[0].toLocalFile())

    def _open_presets(self):
        from .presets_page import PresetsPage
        dlg = PresetsPage(self, standalone=True)
        dlg.exec()
        self._reload_presets()

    # ---------------- 运行 ----------------
    def _run(self):
        if not self.video_path or not os.path.isfile(self.video_path):
            QMessageBox.warning(self, "提示", "请先选择或拖入视频文件")
            return
        self._clear_preview()
        self.btn_run.setEnabled(False)
        self.btn_cancel.setVisible(True)
        self.bar.setValue(0)

        self.thread = WorkThread(
            self.video_path, self.cmb_preset.currentIndex(),
            self.spn_th.value(), self.chk_ppt.isChecked(), self.chk_gif.isChecked(),
            self.spn_ms.value(), self.spn_w.value())
        self.thread.progress.connect(self._on_prog)
        self.thread.done.connect(self._on_done)
        self.thread.failed.connect(self._on_fail)
        self.thread.start()

    def _cancel(self):
        if self.thread:
            self.thread.cancel()

    def _on_prog(self, pct, stage):
        self.bar.setValue(int(pct))
        self.lbl_stage.setText(stage)

    def _on_fail(self, msg):
        self.btn_run.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.lbl_stage.setText(f"失败：{msg}")
        self.lbl_stage.setStyleSheet(f"color:{theme.DANGER};")

    def _on_done(self, r: dict):
        self.btn_run.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.result = r
        self.btn_open.setVisible(True)
        import time as _t
        cost = r.get("cost", 0)
        self.lbl_stage.setText(f"完成 ✔ 共提取 {len(r['frames'])} 帧｜耗时 {cost}s")
        self.lbl_stage.setStyleSheet(f"color:{theme.OK};")
        # 写入历史
        database.add_history(
            self.user["id"], os.path.basename(self.video_path), self.video_path,
            self.cmb_preset.currentText().split("｜")[0], self.spn_th.value(),
            len(r["frames"]), r.get("ppt", ""), r.get("gif", ""), r.get("dir", ""),
            r.get("cost", 0), {"preset_index": self.cmb_preset.currentIndex(),
                               "threshold": self.spn_th.value(),
                               "gif_ms": self.spn_ms.value(),
                               "gif_w": self.spn_w.value(),
                               "ppt": self.chk_ppt.isChecked(),
                               "gif": self.chk_gif.isChecked()})
        self._show_preview(r)

    def _show_preview(self, r: dict):
        head = QHBoxLayout()
        info = QLabel(f"采样 {r.get('sampled',0)} 帧｜视频时长 {r.get('duration',0)}s")
        info.setObjectName("hintLabel")
        head.addWidget(info)
        head.addStretch(1)
        if r.get("ppt"):
            b = QPushButton("打开 PPT")
            b.clicked.connect(lambda: os.startfile(r["ppt"]))
            head.addWidget(b)
        if r.get("gif"):
            b = QPushButton("打开 GIF")
            b.clicked.connect(lambda: os.startfile(r["gif"]))
            head.addWidget(b)
        wrap = QWidget()
        wrap.setLayout(head)
        self.preview_lay.addWidget(wrap)

        grid = QGridLayout()
        grid.setSpacing(10)
        for i, fr in enumerate(r["frames"][:60]):
            card = QFrame()
            card.setObjectName("card")
            cv = QVBoxLayout(card)
            img = QLabel()
            pm = QPixmap(fr["path"])
            if not pm.isNull():
                img.setPixmap(pm.scaledToWidth(240, Qt.TransformationMode.SmoothTransformation))
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cap = QLabel(f"#{i+1}  {fr['tSec']}s")
            cap.setObjectName("hintLabel")
            cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cv.addWidget(img)
            cv.addWidget(cap)
            grid.addWidget(card, i // 4, i % 4)
        holder = QWidget()
        holder.setLayout(grid)
        self.preview_lay.addWidget(holder)

    def _clear_preview(self):
        while self.preview_lay.count():
            it = self.preview_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def _open_out(self):
        if self.result:
            os.startfile(self.result["dir"])

    def apply_history(self, h: dict):
        """历史记录一键复用（规则5）"""
        import json
        try:
            p = json.loads(h.get("params_json") or "{}")
        except Exception:
            p = {}
        if h.get("video_path") and os.path.isfile(h["video_path"]):
            self.set_video(h["video_path"])
        self.spn_th.setValue(float(h.get("threshold") or 0.06))
        if "preset_index" in p:
            self.cmb_preset.setCurrentIndex(min(int(p["preset_index"]), self.cmb_preset.count() - 1))
        self.chk_ppt.setChecked(bool(p.get("ppt", True)))
        self.chk_gif.setChecked(bool(p.get("gif", False)))
        self.spn_ms.setValue(int(p.get("gif_ms", 800)))
        self.spn_w.setValue(int(p.get("gif_w", 640)))
