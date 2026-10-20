# -*- coding: utf-8 -*-
"""输出模块：帧序列 → PPTX / 动态 GIF"""
import os

from PIL import Image


def make_ppt(frames: list, out_pptx: str, keep_aspect: bool = True,
             bg_rgb=(18, 18, 24)) -> str:
    """把关键帧生成为 PPTX（16:9，每帧一页）。
    frames: [{path, tSec, ...}]
    """
    from pptx import Presentation
    from pptx.util import Emu

    prs = Presentation()
    slide_w, slide_h = prs.slide_width, prs.slide_height  # 默认16:9
    blank = prs.slide_layouts[6]

    for fr in frames:
        slide = prs.slides.add_slide(blank)
        img = Image.open(fr["path"])
        iw, ih = img.size
        scale = min(slide_w / iw, slide_h / ih) if keep_aspect else None
        if keep_aspect:
            w, h = int(iw * scale), int(ih * scale)
            left, top = (slide_w - w) // 2, (slide_h - h) // 2
        else:
            left, top, w, h = 0, 0, slide_w, slide_h
        slide.shapes.add_picture(fr["path"], left, top, width=w, height=h)

    os.makedirs(os.path.dirname(out_pptx) or ".", exist_ok=True)
    prs.save(out_pptx)
    return out_pptx


def make_gif(frames: list, out_gif: str, duration_ms: int = 800,
             width: int = 640) -> str:
    """把关键帧合成动态 GIF（按帧顺序循环播放）"""
    imgs = []
    for fr in frames:
        im = Image.open(fr["path"]).convert("RGB")
        if im.width > width:
            h = int(im.height * width / im.width)
            im = im.resize((width, h), Image.LANCZOS)
        imgs.append(im)
    if not imgs:
        raise RuntimeError("没有可写入 GIF 的帧")
    os.makedirs(os.path.dirname(out_gif) or ".", exist_ok=True)
    imgs[0].save(out_gif, save_all=True, append_images=imgs[1:],
                 duration=duration_ms, loop=0, optimize=True)
    return out_gif
