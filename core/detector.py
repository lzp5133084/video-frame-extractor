# -*- coding: utf-8 -*-
"""静止画面检测 + 阈值单帧提取模块

算法借鉴两个已验证的开源项目精华：
- larry-xue/video-slide-extractor：块级帧差（抗光标/摄像头气泡干扰）
- antonkulaga/video2slides：SSIM 二次去重思想 + 角落遮罩
"""
import os
import time

import cv2
import numpy as np


def _block_mask(w, h, bs, ignore_corners, corner_ratio):
    """块级遮罩权重：忽略四角区域（摄像头气泡一般位于角落）"""
    gw, gh = w // bs, h // bs
    mask = np.ones((gh, gw), dtype=np.float32)
    if ignore_corners and corner_ratio > 0:
        cx, cy = int(gw * corner_ratio), int(gh * corner_ratio)
        mask[:cy, :cx] = 0          # 左上
        mask[:cy, -cx:] = 0         # 右上
        mask[-cy:, :cx] = 0         # 左下
        mask[-cy:, -cx:] = 0        # 右下
    return mask


def detect_keyframes(video_path: str, out_dir: str, threshold: float = 0.06,
                     block_size: int = 8, block_delta: int = 14,
                     sample_fps: float = 2.0, min_gap_sec: float = 1.0,
                     ignore_corners: bool = True, corner_ratio: float = 0.15,
                     image_format: str = "jpg", quality: int = 92,
                     progress_cb=None, cancel_flag=None):
    """在视频上检测画面变化点并提取单帧。

    threshold: 变化块占比阈值(0~1)，越大越严格、保留帧越少（军哥自定义核心参数）
    返回 dict(frames=[{path,tSec,changed_ratio}], total_sampled, duration)
    """
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, int(round(fps / max(sample_fps, 0.1))))
    min_gap_frames = int(min_gap_sec * fps)

    # 预读一帧确定检测分辨率
    ok, first = cap.read()
    if not ok:
        raise RuntimeError("视频解码失败：无法读取首帧")
    det_w = 320
    det_h = max(1, int(first.shape[0] * det_w / first.shape[1]))
    mask = _block_mask(det_w, det_h, block_size, ignore_corners, corner_ratio)

    prev_small = None
    kept = []            # [(frame_index, changed_ratio)]
    last_kept_idx = -10 ** 9
    sampled = 0
    idx = 0
    first_kept = False

    while True:
        if idx == 0:
            ok, frame = True, first
        else:
            ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            sampled += 1
            small = cv2.resize(frame, (det_w, det_h), interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)

            changed_ratio = 0.0
            if prev_small is not None:
                diff = cv2.absdiff(gray, prev_small)
                # 块级统计：每块平均差
                bh, bw = det_h // block_size * block_size, det_w // block_size * block_size
                diff = diff[:bh, :bw]
                blocks = diff.reshape(bh // block_size, block_size,
                                      bw // block_size, block_size).mean(axis=(1, 3))
                changed = (blocks > block_delta).astype(np.float32) * mask
                denom = max(mask.sum(), 1.0)
                changed_ratio = float(changed.sum() / denom)

            is_key = (not first_kept) or (changed_ratio > threshold)
            if is_key and (idx - last_kept_idx) >= min_gap_frames:
                kept.append((idx, changed_ratio, time.strftime("")))
                last_kept_idx = idx
                first_kept = True
                prev_small = gray  # 与"最近保留帧"比较（开源方案同款逻辑）
            if prev_small is None:
                prev_small = gray
        if progress_cb and total_frames > 0 and idx % (step * 10) == 0:
            progress_cb(min(99.0, idx / total_frames * 100.0))
        if cancel_flag and cancel_flag[0]:
            cap.release()
            raise InterruptedError("已取消")
        idx += 1
    cap.release()

    # 二次高清提取：seek 到每个停留段中段，取最清晰一帧
    results = []
    n = len(kept)
    for i, (fi, ratio, _) in enumerate(kept):
        start_t = fi / fps
        # 段中点 = 与下一保留点(或结尾)的中间，保证取到"停留完成"的干净帧
        next_fi = kept[i + 1][0] if i + 1 < n else total_frames - 1
        mid_t = (fi + max(next_fi - int(min_gap_frames * 0.5), fi + 1)) / 2.0 / fps
        mid_t = min(mid_t, (total_frames - 1) / fps) if total_frames else start_t
        best = _grab_best_frame(video_path, start_t, mid_t)
        if best is None:
            continue
        t_sec = round(mid_t, 3)
        fname = f"frame_{len(results)+1:03d}.{image_format}"
        fpath = os.path.join(out_dir, fname)
        # cv2.imwrite 不支持中文路径，改用 imencode + 二进制写入
        params = ([cv2.IMWRITE_JPEG_QUALITY, quality] if image_format == "jpg"
                  else [])
        ok_enc, buf = cv2.imencode(f".{image_format}", best, params)
        if not ok_enc:
            continue
        with open(fpath, "wb") as f:
            f.write(buf.tobytes())
        results.append({"path": fpath, "tSec": t_sec, "changed_ratio": round(ratio, 4)})
        if progress_cb:
            progress_cb(99.0 * (i + 1) / max(n, 1))
    if progress_cb:
        progress_cb(100.0)
    return {"frames": results, "total_sampled": sampled,
            "duration": round(total_frames / fps, 2) if fps else 0}


def _grab_best_frame(video_path: str, t_start: float, t_mid: float):
    """在 [t_start, t_mid] 取拉普拉斯方差最高（最清晰）的一帧"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    best_frame, best_score = None, -1.0
    f0, f1 = int(t_start * fps), max(int(t_start * fps) + 1, int(t_mid * fps))
    span = f1 - f0
    probes = [f0 + span * p // 4 for p in range(1, 5)] if span > 4 else [f0]
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(f0, 10 ** 9))
    ok, frame = cap.read()
    for target in probes:
        cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if score > best_score:
            best_score, best_frame = score, frame
    cap.release()
    return best_frame
