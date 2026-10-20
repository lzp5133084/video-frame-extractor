# 视频单帧提取工具 Video Frame Extractor

> 把课程录屏 / 手机操作视频里大量静止的无效画面去掉，只保留变化的关键单帧，一键生成 **PPT** 或 **动态 GIF**。
>
> 作者：军哥懂保 ｜ 微信：xunijiayuan ｜ 生态站点：[ecojia.cn](https://ecojia.cn)

## 功能特性

- **5 档视频压缩**（极速/快速/均衡/高清/原画），每档 CRF、分辨率、编码速度均可在界面自定义（ffmpeg 驱动）
- **静止画面检测**：块级帧差算法（借鉴开源项目 video-slide-extractor 的检测思想 + video2slides 的去重/遮罩思路），抗光标与摄像头气泡干扰
- **阈值自定义**（0.01~1.00）：越小保留帧越多，越大只保留明显切换画面；附经验值参考
- **单帧提取**：每个变化点自动取停留段中"最清晰一帧"（拉普拉斯方差优选）
- **输出**：16:9 PPTX（python-pptx）+ 循环动态 GIF（Pillow）+ 单帧图片
- **多人使用**：本地账号注册/登录，历史记录按用户隔离（SQLite），管理员可增删查改用户
- **操作记忆**：历史记录一键复用参数到处理页
- **预留对外接口**：可被其他程序 import 或命令行调用
- **程序自检**：7 项核心组件一键自检
- 2027 黑金科技风 UI（PyQt6）

## 环境要求

- Windows 10/11
- ffmpeg / ffprobe 在 PATH 中（[winget install Gyan.FFmpeg](https://ffmpeg.org/download.html)）
- Python 3.10+（或直接使用仓库外自备的嵌入式运行时）

## 快速开始

```bash
pip install -r requirements.txt
python 视频单帧提取工具.py
```

或直接双击 `启动工具.bat`。

首次登录默认管理员：`admin / admin123`（请立即修改密码）。

## 对外接口（供其他程序调用）

```python
from core import api

r = api.process_video(
    video_path=r"D:\课程\第1课.mp4",
    preset_index=2,        # 压缩档位 0~4
    threshold=0.06,        # 静止判定阈值
    make_ppt_flag=True,    # 生成 PPT
    make_gif_flag=True,    # 生成 GIF
)
print(r["ppt"], r["gif"], len(r["frames"]))
```

命令行方式：

```bash
python core/api.py --video 输入.mp4 --preset 1 --threshold 0.06 --ppt --gif
```

档位配置读写：`api.get_presets()` / `api.save_presets()`（config/presets.json）。

## 项目结构

```
├── 视频单帧提取工具.py     # 主入口（GUI）
├── 启动工具.bat            # 一键启动
├── 无头自检.py             # 登录→主窗口全链路自检
├── core/
│   ├── api.py              # 对外接口（一条龙 + CLI）
│   ├── compressor.py       # 5档压缩
│   ├── detector.py         # 静止检测 + 单帧提取
│   ├── exporter.py         # PPT / GIF 导出
│   └── database.py         # 多用户 + 历史记录（SQLite）
├── ui/                     # PyQt6 界面（2027 黑金科技风）
├── config/presets.json     # 压缩档位与检测默认参数
└── requirements.txt
```

## 算法说明

1. 压缩：ffmpeg libx264，按档位 CRF + 限高缩放
2. 检测：以 320px 宽采样帧做 8×8 块级帧差，变化块占比超过阈值即判定为新画面；四角遮罩可过滤角落摄像头气泡；与"最近保留帧"比较避免缓慢渐变漏检
3. 提取：在停留段内按拉普拉斯方差选最清晰帧，JPEG/PNG 保存（中文路径安全写入）
4. 导出：python-pptx 全幅铺排；Pillow 合成循环 GIF

## 许可与生态

本工具属于 [数字生态家园 ecojia.cn](https://ecojia.cn) 工具矩阵成员（T20），统一账号体系逐步接入中。
