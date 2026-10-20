# -*- coding: utf-8 -*-
"""关于页：程序大小、上次修改时间、作者信息（规则4）+ 程序自检（规则10）"""
import os
import time

from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)

from . import theme

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _dir_size(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def _fmt_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


class AboutPage(QWidget):
    def __init__(self, main_win=None):
        super().__init__()
        self.main_win = main_win
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 14)
        lay.setSpacing(12)

        t = QLabel("关于本程序")
        t.setObjectName("titleLabel")
        lay.addWidget(t)

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setSpacing(10)

        big = QLabel(f"⬡  {theme.APP_NAME} {theme.APP_VERSION}")
        big.setObjectName("goldLabel")
        big.setStyleSheet("font-size:22px;")
        cl.addWidget(big)

        main_py = os.path.join(BASE_DIR, "视频单帧提取工具.py")
        try:
            mtime = time.strftime("%Y-%m-%d %H:%M:%S",
                                  time.localtime(os.path.getmtime(main_py)))
        except OSError:
            mtime = "未知"
        size = _dir_size(BASE_DIR)

        rows = [
            ("程序大小", _fmt_size(size) + "（不含运行时缓存）"),
            ("上次修改", mtime),
            ("作者", f"{theme.AUTHOR}（军哥懂保）"),
            ("微信号", theme.WECHAT),
            ("技术内核", "ffmpeg 7.1 + OpenCV 5 + 块级帧差检测（借鉴 video-slide-extractor / video2slides 开源算法）"),
            ("使用人数", "多人模式（账号隔离历史记录）"),
        ]
        for k, v in rows:
            r = QHBoxLayout()
            klab = QLabel(k)
            klab.setObjectName("hintLabel")
            klab.setFixedWidth(90)
            vlab = QLabel(v)
            vlab.setWordWrap(True)
            r.addWidget(klab)
            r.addWidget(vlab, 1)
            cl.addLayout(r)
        lay.addWidget(card)

        # 程序自检（规则10）
        t2 = QLabel("程序自检")
        t2.setObjectName("goldLabel")
        lay.addWidget(t2)
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setStyleSheet(
            f"background:{theme.BG_CARD}; border:1px solid #232b42; border-radius:10px;"
            f"color:{theme.TEXT}; font-family:Consolas; font-size:12px;")
        lay.addWidget(self.txt, 1)

        btn_check = QPushButton("立即自检")
        btn_check.setObjectName("goldBtn")
        btn_check.clicked.connect(self.run_check)
        lay.addWidget(btn_check)
        self.run_check()

    def run_check(self):
        lines = []
        ok_all = True

        def chk(name, ok, detail=""):
            nonlocal ok_all
            ok_all = ok_all and ok
            lines.append(f"[{'通过' if ok else '异常'}] {name}{('：' + detail) if detail else ''}")

        try:
            import cv2
            chk("OpenCV", True, cv2.__version__)
        except Exception as e:
            chk("OpenCV", False, str(e))
        try:
            from pptx import Presentation
            chk("python-pptx", True)
        except Exception as e:
            chk("python-pptx", False, str(e))
        try:
            from PIL import Image
            chk("Pillow", True, Image.__version__)
        except Exception as e:
            chk("Pillow", False, str(e))
        try:
            import subprocess
            out = subprocess.run(["ffmpeg", "-version"], capture_output=True,
                                 text=True, encoding="utf-8", errors="ignore",
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            chk("ffmpeg", out.returncode == 0,
                (out.stdout or "").splitlines()[0] if out.stdout else "未找到")
        except Exception as e:
            chk("ffmpeg", False, str(e))
        try:
            from core import database
            n = len(database.list_users())
            chk("用户数据库", True, f"{n} 个账号")
        except Exception as e:
            chk("用户数据库", False, str(e))
        try:
            from core import api
            ps = api.get_presets()
            chk("压缩档位配置", len(ps) == 5, f"{len(ps)} 档")
        except Exception as e:
            chk("压缩档位配置", False, str(e))
        try:
            from PyQt6.QtWidgets import QApplication
            chk("PyQt6 界面库", True)
        except Exception as e:
            chk("PyQt6 界面库", False, str(e))

        lines.append("")
        lines.append("总体状态：" + ("全部通过，程序完整可用 ✔" if ok_all else "存在异常项，请查看上表"))
        self.txt.setPlainText("\n".join(lines))
