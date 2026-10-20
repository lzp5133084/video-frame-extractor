# -*- coding: utf-8 -*-
"""核心能力包：压缩 / 检测 / 导出 / 数据库 / 对外API"""
from . import database  # noqa: F401  (导入即初始化数据库)
from .compressor import compress_video, probe_video, load_config, save_config
from .detector import detect_keyframes
from .exporter import make_ppt, make_gif
