# -*- coding: utf-8 -*-
"""2027 黑金科技风主题（深空黑 + 鎏金 + 青蓝光效）"""

APP_NAME = "视频单帧提取工具"
APP_VERSION = "v1.0.0"
AUTHOR = "军哥懂保"
WECHAT = "xunijiayuan"

# 主色板
BG_DEEP = "#0b0e14"      # 深空黑
BG_CARD = "#131826"      # 卡片
BG_CARD2 = "#1a2136"     # 卡片亮
GOLD = "#e8c268"         # 鎏金
GOLD_DIM = "#b39248"
CYAN = "#39d0d8"         # 科技青
TEXT = "#e6e9f2"
TEXT_DIM = "#8b93a8"
DANGER = "#ff6b6b"
OK = "#4ade80"

QSS = f"""
QWidget {{
    background: {BG_DEEP};
    color: {TEXT};
    font-family: "Microsoft YaHei UI";
    font-size: 13px;
}}
QFrame#card {{
    background: {BG_CARD};
    border: 1px solid #232b42;
    border-radius: 14px;
}}
QLabel#titleLabel {{
    font-size: 21px; font-weight: 700; color: {GOLD};
}}
QLabel#subtitleLabel {{ color: {TEXT_DIM}; font-size: 12px; }}
QLabel#goldLabel {{ color: {GOLD}; font-weight: 600; }}
QLabel#statusLabel {{ color: {CYAN}; }}
QLabel#hintLabel {{ color: {TEXT_DIM}; }}

QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2a3350, stop:1 #1d2440);
    border: 1px solid #35406b; border-radius: 9px;
    padding: 8px 18px; color: {TEXT};
}}
QPushButton:hover {{ border-color: {GOLD}; color: {GOLD}; }}
QPushButton:disabled {{ color: #555f78; border-color: #262d47; }}

QPushButton#goldBtn {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #f0d489, stop:1 #c9a24f);
    color: #1a1408; font-weight: 700; border: none;
}}
QPushButton#goldBtn:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ffe6a3, stop:1 #d9b45f); }}
QPushButton#goldBtn:disabled {{ background: #4a4433; color: #7a705a; }}

QPushButton#dangerBtn {{
    background: transparent; border: 1px solid {DANGER}; color: {DANGER};
}}
QPushButton#dangerBtn:hover {{ background: rgba(255,107,107,0.12); }}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: #0f1420; border: 1px solid #2a3350; border-radius: 8px;
    padding: 7px 10px; color: {TEXT}; selection-background-color: #35406b;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {GOLD};
}}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{
    image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
    border-top: 6px solid {GOLD}; margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {BG_CARD2}; border: 1px solid #35406b;
    selection-background-color: #2a3350; selection-color: {GOLD};
}}

QSlider::groove:horizontal {{
    height: 6px; background: #232b42; border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {CYAN}, stop:1 {GOLD});
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 16px; height: 16px; margin: -6px 0; border-radius: 8px;
    background: {GOLD}; border: 2px solid #0b0e14;
}}

QProgressBar {{
    background: #0f1420; border: 1px solid #2a3350; border-radius: 9px;
    height: 18px; text-align: center; color: {GOLD}; font-weight: 600;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {CYAN}, stop:1 {GOLD});
    border-radius: 8px;
}}

QTableWidget {{
    background: {BG_CARD}; border: 1px solid #232b42; border-radius: 10px;
    gridline-color: #1d2440; alternate-background-color: #161c2e;
}}
QTableWidget::item {{ padding: 6px; }}
QTableWidget::item:selected {{ background: #2a3350; color: {GOLD}; }}
QHeaderView::section {{
    background: #1a2136; color: {GOLD}; font-weight: 600;
    border: none; border-bottom: 1px solid #35406b; padding: 8px;
}}

QListWidget#navList {{
    background: transparent; border: none; font-size: 14px;
}}
QListWidget#navList::item {{
    color: {TEXT_DIM}; padding: 12px 18px; border-radius: 10px; margin: 3px 8px;
}}
QListWidget#navList::item:selected {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 rgba(232,194,104,0.16), stop:1 rgba(57,208,216,0.10));
    color: {GOLD}; border-left: 3px solid {GOLD};
}}
QListWidget#navList::item:hover {{ color: {TEXT}; background: #161c2e; }}

QStatusBar {{ background: {BG_CARD}; color: {TEXT_DIM}; border-top: 1px solid #232b42; }}
QStatusBar QLabel {{ color: {TEXT_DIM}; }}
QStatusBar QLabel#authorLabel {{ color: {GOLD}; font-weight: 600; }}

QScrollBar:vertical {{ background: transparent; width: 9px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #2a3350; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {GOLD_DIM}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; }}
QScrollBar::handle:horizontal {{ background: #2a3350; border-radius: 4px; }}

QMessageBox {{ background: {BG_CARD}; }}
QMessageBox QLabel {{ color: {TEXT}; font-size: 14px; }}
QToolTip {{ background: {BG_CARD2}; color: {GOLD}; border: 1px solid {GOLD}; }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid #35406b; background: #0f1420;
}}
QCheckBox::indicator:checked {{ background: {GOLD}; border-color: {GOLD}; }}

QGroupBox {{
    border: 1px solid #232b42; border-radius: 10px; margin-top: 14px;
    color: {TEXT_DIM}; font-weight: 600;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; color: {GOLD}; }}
"""
