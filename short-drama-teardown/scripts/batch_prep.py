# -*- coding: utf-8 -*-
"""
batch_prep.py — 扒剧引擎 V4.0.1 本地零 Token 批量预处理与「逐句 1:1 画面绑定」工具
解决痛点：
  1. 解决「直接发视频（通道B）说话人全乱、一人被拆成四个名字、魔物台词安给配角」：
     新增 `--bind-frames <video.mp4> <sub.srt|json>` 功能！
     自动读取每一句台词的时间码 `start ~ end`，在**每一句台词的正中间秒位 `(start+end)/2`**
     精准抽取 1 张关键帧（命名为 `L001_00m05.50s_瑶瑶守好家.jpg`），实现「1句台词 = 1张对应画面」，
     彻底杜绝「每隔 15 秒稀疏抽帧导致中间台词张冠李戴」！
     ★V4.0.1：抽帧失败不再静默——索引表标注「❌ 未抽到帧」，并在结尾汇总失败句号、以退出码 3 报警。
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


def mid_sec_tag(mid):
    """中点秒 -> '00m05.50s'，避免 mid=59.999 被格式化成 00m60.00s"""
    total = int(round(mid * 100))
    minutes, rest = divmod(total, 6000)
    return f"{minutes:02d}m{rest / 100.0:05.2f}s"


def bind_frames_to_subtitles(video_path, sub_path, out_dir):
    """
    通道 B（直接发视频）核心武器：
    读取 SRT/VTT/JSON 中每一句台词的起止时间码，在每句台词正中间 (start+end)/2 抽取 1 张画面帧，
    并生成一份《逐句时间码-画面帧对位索引表.md》，彻底杜绝跨句盲猜说话人！
    V4.0.1：逐帧核验 ffmpeg 返回码与文件是否真的落盘，失败即在索引表打 ❌ 并汇总报警。
    """
    if not has_ffmpeg():
        print("错误：未检测到 ffmpeg，请先安装 ffmpeg")
        sys.exit(1)
    # 动态加载同目录的 srt_to_script 解析器
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    import srt_to_script as s2s

    with io.open(sub_path, encoding='utf-8-sig', errors='replace') as fh:
        raw = fh.read()
    items = s2s.dedup_rolling(s2s.parse_input(raw, sub_path))
    if not items:
        print(f"未在 {sub_path} 中解析到字幕行")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    md_lines = [
        '# 逐句台词 1:1 画面中点绑定表（通道 B 防乱人核验表）',
        '',
        '> 生成器：batch_prep.py V4.0.1 · 「未抽到帧」的句子严禁凭记忆补画面，须 `--grab-frame` 定点重抽后再核。',
        '',
        '| 句号 | 起止时间码 | 抽帧中点秒 | 台词内容 | 绑定画面帧文件 | 画面角色与嘴型核验（张嘴对白 / 闭嘴OS） |',
        '|---|---|---|---|---|---|',
    ]
    failed = []
    for idx, (s, e, content) in enumerate(items, 1):
        mid = (s + e) / 2.0
        safe_txt = sanitize_filename(content)
        img_name = f"L{idx:03d}_{mid_sec_tag(mid)}_{safe_txt}.jpg"
        img_path = os.path.join(out_dir, img_name)
        res = grab_single_frame(video_path, mid, img_path)
        ok = (res.returncode == 0) and os.path.exists(img_path) and os.path.getsize(img_path) > 0
        if not ok:
            failed.append(idx)
            frame_cell = f'`{img_name}`', '❌ 未抽到帧（该秒超出片长 / ffmpeg 报错，须定点重抽）'
        else:
            frame_cell = f'`{img_name}`', '待填（看图锁死角色+张闭嘴）'
        md_lines.append(
            f"| {idx} | {s2s.fmt(s)}-{s2s.fmt(e)} | {mid:.2f}s | {content} | {frame_cell[0]} | {frame_cell[1]} |"
        )
    index_md_path = os.path.join(out_dir, 'frame_binding_index.md')
    with io.open(index_md_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(md_lines) + '\n')
    print(f"已按逐句中点完成 {len(items)} 句台词的 1:1 画面抽帧绑定 -> {out_dir}")
    print(f"对位索引表：{index_md_path}")
    if failed:
        print(f"⚠️ 有 {len(failed)} 句未抽到帧：句号 {failed}（多为台词时间码超出片长或 ffmpeg 异常）")
        print("   请用 `--grab-frame <视频> --time <秒> --out <文件名>` 定点重抽，或核对该句时间码是否落在片长内。")
        sys.exit(3)


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
        if res.returncode == 0:
            print(f"[{idx}/{len(files)}] {fname} -> {os.path.basename(out_p)} [OK]")
        else:
            tail = (res.stderr or b'').decode('utf-8', 'replace').strip().splitlines()
            reason = tail[-1] if tail else 'ffmpeg 返回非 0'
            print(f"[{idx}/{len(files)}] {fname} -> {os.path.basename(out_p)} [FAIL] {reason}")
            print("   常见原因：该视频无音轨 / 文件损坏。无音轨的片子请改用平台字幕或剪映草稿直读。")


def selftest():
    assert callable(extract_light_audio)
    assert callable(grab_single_frame)
    assert callable(crop_subtitle_strip)
    assert callable(bind_frames_to_subtitles)
    assert sanitize_filename("瑶瑶，守好家！") == "瑶瑶守好家"
    # V4.0.1：中点秒标签不得出现 60.00s
    assert mid_sec_tag(5.5) == '00m05.50s', mid_sec_tag(5.5)
    assert mid_sec_tag(59.999) == '01m00.00s', mid_sec_tag(59.999)
    assert mid_sec_tag(65.0) == '01m05.00s', mid_sec_tag(65.0)
    # V4.0.1 补丁回归：带 UTF-8 BOM 的字幕文件不得把首句读成乱码/丢句
    import tempfile
    _sd = os.path.dirname(os.path.abspath(__file__))
    if _sd not in sys.path:
        sys.path.insert(0, _sd)
    import srt_to_script as _s2s
    _bom = os.path.join(tempfile.gettempdir(), 'bp_bom_selftest.srt')
    with io.open(_bom, 'w', encoding='utf-8-sig') as _fh:
        _fh.write('1\n00:00:01,000 --> 00:00:02,000\n测试台词\n')
    try:
        _items = _s2s.parse_input(_s2s.read_text(_bom), _bom)
        assert len(_items) == 1 and _items[0][2] == '测试台词', _items
    finally:
        os.remove(_bom)
    print(f"selftest OK (ffmpeg available: {has_ffmpeg()})")


def opt_val(argv, name, default=None, required=True):
    """取 --name 后面的取值；缺值直接报错退出，避免 IndexError 糊一脸（V4.0.1）"""
    if name not in argv:
        if required:
            print(f"错误：缺少参数 {name}")
            sys.exit(2)
        return default
    i = argv.index(name)
    if i + 1 >= len(argv) or argv[i + 1].startswith('--'):
        print(f"错误：参数 {name} 缺少数值/路径")
        sys.exit(2)
    return argv[i + 1]


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
        sys.exit(0)
    if '--bind-frames' in sys.argv:
        idx = sys.argv.index('--bind-frames')
        if idx + 2 >= len(sys.argv):
            print("用法：python batch_prep.py --bind-frames <视频.mp4> <字幕.srt|json> [--out-dir ./line_frames]")
            sys.exit(2)
        vp, sp = sys.argv[idx + 1], sys.argv[idx + 2]
        out_d = opt_val(sys.argv, '--out-dir', './line_frames', required=False)
        bind_frames_to_subtitles(vp, sp, out_d)
    elif '--audio-dir' in sys.argv:
        in_d = opt_val(sys.argv, '--audio-dir')
        out_d = opt_val(sys.argv, '--out-dir', os.path.join(in_d, 'audio_16k'), required=False)
        batch_extract_audio(in_d, out_d)
    elif '--grab-frame' in sys.argv:
        vp = opt_val(sys.argv, '--grab-frame')
        sec = float(opt_val(sys.argv, '--time', '1.0', required=False))
        out_img = opt_val(sys.argv, '--out', 'frame_check.jpg', required=False)
        res = grab_single_frame(vp, sec, out_img)
        if res.returncode != 0 or not os.path.exists(out_img):
            print(f"❌ 抽帧失败：第 {sec}s 可能超出片长或视频不可读")
            sys.exit(3)
        print(f"已抽取第 {sec}s 关键帧 -> {out_img}")
    elif '--crop-sub' in sys.argv:
        vp = opt_val(sys.argv, '--crop-sub')
        out_v = opt_val(sys.argv, '--out', 'sub_strip.mp4', required=False)
        res = crop_subtitle_strip(vp, out_v)
        if res.returncode != 0 or not os.path.exists(out_v):
            print("❌ 字幕带裁剪失败，请检查视频是否可读")
            sys.exit(3)
        print(f"已生成 4fps 底部字幕带 -> {out_v}")
    else:
        print(__doc__)
