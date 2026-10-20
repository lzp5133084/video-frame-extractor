# -*- coding: utf-8 -*-
"""视频压缩模块：5档可自定义，基于 ffmpeg，带进度回调"""
import json
import os
import re
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESET_PATH = os.path.join(BASE_DIR, "config", "presets.json")

DEFAULT_PRESETS = {
    "presets": [
        {"name": "极速档", "crf": 32, "height": 480, "preset": "veryfast", "desc": "最小体积，检测最快"},
        {"name": "快速档", "crf": 28, "height": 720, "preset": "faster", "desc": "体积小速度快"},
        {"name": "均衡档", "crf": 25, "height": 720, "preset": "medium", "desc": "速度画质平衡"},
        {"name": "高清档", "crf": 23, "height": 1080, "preset": "medium", "desc": "高画质提取"},
        {"name": "原画档", "crf": 18, "height": 0, "preset": "slow", "desc": "保持原分辨率"},
    ],
    "detect": {
        "threshold": 0.06, "block_size": 8, "block_delta": 14,
        "sample_fps": 2, "min_gap_sec": 1.0,
        "ignore_corners": True, "corner_ratio": 0.15,
    },
}


def load_config() -> dict:
    try:
        with open(PRESET_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not cfg.get("presets"):
            raise ValueError
        return cfg
    except Exception:
        return json.loads(json.dumps(DEFAULT_PRESETS))


def save_config(cfg: dict):
    os.makedirs(os.path.dirname(PRESET_PATH), exist_ok=True)
    with open(PRESET_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def find_ffmpeg() -> str:
    return "ffmpeg"  # 依赖 PATH


def probe_video(path: str) -> dict:
    """ffprobe 获取时长/宽高/帧率"""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,r_frame_rate:format=duration",
           "-of", "json", path]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    import json as _j
    info = _j.loads(out.stdout or "{}")
    st = (info.get("streams") or [{}])[0]
    dur = float(info.get("format", {}).get("duration") or 0)
    num, den = (st.get("r_frame_rate") or "25/1").split("/")
    fps = float(num) / float(den or 1)
    return {"duration": dur, "width": int(st.get("width") or 0),
            "height": int(st.get("height") or 0), "fps": fps}


def compress_video(src: str, dst: str, crf: int, height: int, preset: str,
                   progress_cb=None, cancel_flag=None) -> str:
    """压缩视频。height=0 表示保持原分辨率。返回输出路径。
    progress_cb(percent: float) 用于UI进度；cancel_flag 为可变list，置[True]取消。
    """
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    info = probe_video(src)
    total = info["duration"] or 0

    cmd = ["ffmpeg", "-y", "-i", src, "-c:v", "libx264", "-crf", str(crf),
           "-preset", preset, "-an"]
    if height and info["height"] > height:
        cmd += ["-vf", f"scale=-2:{height}"]
    cmd += ["-movflags", "+faststart", dst]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="ignore",
                            creationflags=subprocess.CREATE_NO_WINDOW)
    time_re = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")
    for line in proc.stdout:
        if cancel_flag and cancel_flag[0]:
            proc.kill()
            raise InterruptedError("已取消")
        m = time_re.search(line)
        if m and total > 0 and progress_cb:
            t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
            progress_cb(min(99.0, t / total * 100.0))
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 压缩失败（code {proc.returncode}）")
    if progress_cb:
        progress_cb(100.0)
    return dst
