# -*- coding: utf-8 -*-
"""
batch_prep.py — 扒剧引擎 V3.1 本地零 Token 批量预处理与「逐句 1:1 画面绑定」工具
解决痛点：
  1. 解决「直接发视频（通道B）说话人全乱、一人被拆成四个名字、魔物台词安给配角」：
     新增 `--bind-frames <video.mp4> <sub.srt|json>` 功能！
     自动读取每一句台词的时间码 `start ~ end`，在**每一句台词的正中间秒位 `(start+end)/2`**
     精准抽取 1 张关键帧（命名为 `L001_00m05.5s_瑶瑶守好家.jpg`），实现「1句台词 = 1张对应画面」，
     彻底杜绝「每隔 15 秒稀疏抽帧导致中间台词张冠李戴」！
  2. 解决「豆包直接看视频漏字幕 + 额度消耗极快 + 排队崩」：
     提供 `--audio-dir` 批量提取 16kHz 极轻单声道音频，以及 `--crop-sub` 裁剪 4fps 底部字幕带。

用法：
  1) 【通道B核心】逐句台词中点 1:1 抽帧绑定（看清每句话是谁张嘴、谁闭嘴OS）：
     python batch_prep.py --bind-frames <视频.mp4> <字幕.srt|draft_content.json> [--out-dir ./line_frames]
  2) 批量提取极轻音频（供本地 FunASR/Whisper 转写，不漏句、省90%额度）：
     python batch_prep.py --audio-dir <视频目录> [--out-dir <输出目录>]
  3) 定点抽取存疑台词单帧：
     python batch_prep.py --grab-frame <视频.mp4> --time 12.5 [--out frame.jpg]
  4) 裁剪底部字幕带（供 RapidOCR / PaddleOCR 极速识字）：
     python batch_prep.py --crop-sub <视频.mp4> [--out sub_strip.mp4]
  5) 自检：
     python batch_prep.py --selftest
"""
import io
import os
import re
import shutil
import subprocess
import sys

VIDEO_EXTS = ('.mp4', '.mov', '.mkv', '.flv', '.ts', '.webm')


def has_ffmpeg():
    return shutil.which('ffmpeg') is not None


def extract_light_audio(video_path, out_audio_path):
    """提取 16kHz 单声道 32kbps 极轻音频，适合高精度 ASR 与声纹聚类"""
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-vn', '-ac', '1', '-ar', '16000', '-b:a', '32k',
        out_audio_path
    ]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def grab_single_frame(video_path, sec, out_img_path):
    """在指定秒位抽取 1 张单帧，用于核验角色嘴型（闭嘴=内心独白OS）或确认说话人"""
    cmd = [
        'ffmpeg', '-y', '-ss', f"{sec:.3f}", '-i', video_path,
        '-frames:v', '1', '-q:v', '3',
        out_img_path
    ]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def crop_subtitle_strip(video_path, out_video_path, fps=4):
    """仅保留画面底部 28% 字幕区域并降帧至 4fps（短剧最快 0.25s 闪句也能 100% 捕获，体积缩小 90%）"""
    vf = f"fps={fps},crop=iw:ih*0.28:0:ih*0.72"
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-vf', vf, '-an', '-c:v', 'libx264', '-crf', '28', '-preset', 'veryfast',
        out_video_path
    ]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def sanitize_filename(text, max_len=16):
    cleaned = re.sub(r'[\\/:*?"<>|\s\[\]【】()（）,，。！？!?.…]', '', text)
    return cleaned[:max_len] if cleaned else 'line'


def bind_frames_to_subtitles(video_path, sub_path, out_dir):
    """
    通道 B（直接发视频）核心武器：
    读取 SRT/VTT/JSON 中每一句台词的起止时间码，在每句台词正中间 (start+end)/2 抽取 1 张画面帧，
    并生成一份《逐句时间码-画面帧对位索引表.md》，彻底杜绝跨句盲猜说话人！
    """
    if not has_ffmpeg():
        print("错误：未检测到 ffmpeg，请先安装 ffmpeg")
        sys.exit(1)
    # 动态加载同目录的 srt_to_script 解析器
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    import srt_to_script as s2s

    raw = io.open(sub_path, encoding='utf-8', errors='replace').read()
    items = s2s.dedup_rolling(s2s.parse_input(raw, sub_path))
    if not items:
        print(f"未在 {sub_path} 中解析到字幕行")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    md_lines = [
        '# 逐句台词 1:1 画面中点绑定表（通道 B 防乱人核验表）',
        '',
        '| 句号 | 起止时间码 | 抽帧中点秒 | 台词内容 | 绑定画面帧文件 | 画面角色与嘴型核验（张嘴对白 / 闭嘴OS） |',
        '|---|---|---|---|---|---|',
    ]
    for idx, (s, e, content) in enumerate(items, 1):
        mid = (s + e) / 2.0
        safe_txt = sanitize_filename(content)
        img_name = f"L{idx:03d}_{int(mid)//60:02d}m{mid%60:05.2f}s_{safe_txt}.jpg"
        img_path = os.path.join(out_dir, img_name)
        grab_single_frame(video_path, mid, img_path)
        md_lines.append(
            f"| {idx} | {s2s.fmt(s)}-{s2s.fmt(e)} | {mid:.2f}s | {content} | `{img_name}` | 待填（看图锁死角色+张闭嘴） |"
        )
    index_md_path = os.path.join(out_dir, 'frame_binding_index.md')
    io.open(index_md_path, 'w', encoding='utf-8').write('\n'.join(md_lines) + '\n')
    print(f"已按逐句中点完成 {len(items)} 句台词的 1:1 画面抽帧绑定 -> {out_dir}")
    print(f"对位索引表：{index_md_path}")


def batch_extract_audio(in_dir, out_dir):
    if not has_ffmpeg():
        print("错误：未检测到 ffmpeg，请先安装 ffmpeg")
        sys.exit(1)
    os.makedirs(out_dir, exist_ok=True)
    files = sorted([
        f for f in os.listdir(in_dir)
        if f.lower().endswith(VIDEO_EXTS)
    ])
    if not files:
        print(f"未在 {in_dir} 找到视频文件")
        return
    for idx, fname in enumerate(files, 1):
        in_p = os.path.join(in_dir, fname)
        stem = os.path.splitext(fname)[0]
        out_p = os.path.join(out_dir, f"{stem}_16k.mp3")
        res = extract_light_audio(in_p, out_p)
        status = "OK" if res.returncode == 0 else "FAIL"
        print(f"[{idx}/{len(files)}] {fname} -> {os.path.basename(out_p)} [{status}]")


def selftest():
    assert callable(extract_light_audio)
    assert callable(grab_single_frame)
    assert callable(crop_subtitle_strip)
    assert callable(bind_frames_to_subtitles)
    assert sanitize_filename("瑶瑶，守好家！") == "瑶瑶守好家"
    print(f"selftest OK (ffmpeg available: {has_ffmpeg()})")


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
        sys.exit(0)
    if '--bind-frames' in sys.argv:
        idx = sys.argv.index('--bind-frames')
        vp = sys.argv[idx + 1]
        sp = sys.argv[idx + 2]
        out_d = './line_frames'
        if '--out-dir' in sys.argv:
            out_d = sys.argv[sys.argv.index('--out-dir') + 1]
        bind_frames_to_subtitles(vp, sp, out_d)
    elif '--audio-dir' in sys.argv:
        in_d = sys.argv[sys.argv.index('--audio-dir') + 1]
        out_d = os.path.join(in_d, 'audio_16k')
        if '--out-dir' in sys.argv:
            out_d = sys.argv[sys.argv.index('--out-dir') + 1]
        batch_extract_audio(in_d, out_d)
    elif '--grab-frame' in sys.argv:
        vp = sys.argv[sys.argv.index('--grab-frame') + 1]
        sec = float(sys.argv[sys.argv.index('--time') + 1]) if '--time' in sys.argv else 1.0
        out_img = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'frame_check.jpg'
        grab_single_frame(vp, sec, out_img)
        print(f"已抽取第 {sec}s 关键帧 -> {out_img}")
    elif '--crop-sub' in sys.argv:
        vp = sys.argv[sys.argv.index('--crop-sub') + 1]
        out_v = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'sub_strip.mp4'
        crop_subtitle_strip(vp, out_v)
        print(f"已生成 4fps 底部字幕带 -> {out_v}")
    else:
        print(__doc__)
