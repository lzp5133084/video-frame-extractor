# -*- coding: utf-8 -*-
"""预留对外调用接口（规则7）：其他程序可直接 import 本模块调用

用法示例：
    from core import api
    result = api.process_video(
        video_path=r"D:\\课程\\第1课.mp4",
        preset_index=2,           # 压缩档位 0~4
        threshold=0.06,           # 静止判定阈值(0~1)，越大保留帧越少
        make_ppt=True,            # 生成 PPT
        make_gif=True,            # 生成 GIF
    )
    print(result["ppt"], result["gif"], len(result["frames"]))

也可命令行调用（子进程方式）：
    python api.py --video 输入.mp4 --preset 1 --threshold 0.06 --gif
"""
import os
import sys
import time
import uuid

if __package__ in (None, ""):  # 直接作为脚本运行（CLI 调用）
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.compressor import load_config, compress_video, probe_video
    from core.detector import detect_keyframes
    from core.exporter import make_ppt, make_gif
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    from .compressor import load_config, compress_video, probe_video
    from .detector import detect_keyframes
    from .exporter import make_ppt, make_gif
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def get_presets() -> list:
    """获取5档压缩配置（可读后修改再调 save_presets）"""
    return load_config()["presets"]


def save_presets(presets: list):
    """保存自定义压缩档位：[{"name","crf","height","preset","desc"}]"""
    cfg = load_config()
    cfg["presets"] = presets
    from .compressor import save_config
    save_config(cfg)


def process_video(video_path: str, preset_index: int = 2, threshold: float = None,
                  make_ppt_flag: bool = True, make_gif_flag: bool = False,
                  gif_duration_ms: int = 800, gif_width: int = 640,
                  detect_params: dict = None, progress_cb=None,
                  cancel_flag=None, work_dir: str = None) -> dict:
    """一条龙：压缩 → 静止检测 → 单帧提取 → PPT/GIF 导出

    返回: {"video":压缩视频, "dir":帧目录, "frames":[...], "ppt":路径, "gif":路径,
           "duration":时长, "sampled":采样数, "cost":耗时}
    """
    t0 = time.time()
    cfg = load_config()
    presets = cfg["presets"]
    p = presets[max(0, min(preset_index, len(presets) - 1))]
    if threshold is None:
        threshold = cfg["detect"]["threshold"]

    tag = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    root = work_dir or os.path.join(OUTPUT_DIR, tag)
    os.makedirs(root, exist_ok=True)

    name = os.path.splitext(os.path.basename(video_path))[0]

    def wrap_cb(pct, stage, lo, hi):
        if progress_cb:
            progress_cb(lo + (hi - lo) * min(max(pct, 0), 100) / 100.0, stage)

    # 1) 压缩
    comp_path = os.path.join(root, f"{name}_compressed.mp4")
    info = probe_video(video_path)
    need_compress = not (p["crf"] >= 18 and p["height"] == 0
                         and info["width"] <= 1920)
    if need_compress:
        comp_path = compress_video(
            video_path, comp_path, p["crf"], p["height"], p["preset"],
            progress_cb=lambda x: wrap_cb(x, "压缩中", 0, 40),
            cancel_flag=cancel_flag)
    else:
        import shutil
        shutil.copyfile(video_path, comp_path)
        if progress_cb:
            progress_cb(40, "压缩中")

    # 2) 检测 + 单帧提取
    dp = dict(cfg["detect"])
    if detect_params:
        dp.update(detect_params)
    dp.pop("threshold", None)
    frames_dir = os.path.join(root, "frames")
    det = detect_keyframes(comp_path, frames_dir, threshold=threshold,
                           progress_cb=lambda x: wrap_cb(x, "检测提取中", 40, 92),
                           cancel_flag=cancel_flag, **dp)
    if progress_cb:
        progress_cb(94, "导出中")

    # 3) 导出
    ppt_path, gif_path = "", ""
    if make_ppt_flag and det["frames"]:
        ppt_path = make_ppt(det["frames"], os.path.join(root, f"{name}.pptx"))
    if make_gif_flag and det["frames"]:
        gif_path = make_gif(det["frames"], os.path.join(root, f"{name}.gif"),
                            duration_ms=gif_duration_ms, width=gif_width)

    return {"video": comp_path, "dir": frames_dir, "frames": det["frames"],
            "ppt": ppt_path, "gif": gif_path, "duration": det["duration"],
            "sampled": det["total_sampled"],
            "cost": round(time.time() - t0, 1)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="视频单帧提取 - 外部程序调用接口")
    ap.add_argument("--video", required=True, help="输入视频路径")
    ap.add_argument("--preset", type=int, default=2, help="压缩档位 0~4")
    ap.add_argument("--threshold", type=float, default=None, help="静止判定阈值0~1")
    ap.add_argument("--ppt", action="store_true", help="生成PPT")
    ap.add_argument("--gif", action="store_true", help="生成GIF")
    ap.add_argument("--out", default=None, help="输出根目录")
    a = ap.parse_args()
    r = process_video(a.video, a.preset, a.threshold, a.ppt or not a.gif, a.gif,
                      work_dir=a.out)
    import json
    print(json.dumps({k: v for k, v in r.items() if k != "frames"},
                     ensure_ascii=False, indent=2))
    print(f"共提取 {len(r['frames'])} 帧 → {r['dir']}")
