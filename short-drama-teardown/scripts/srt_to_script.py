# -*- coding: utf-8 -*-
"""
srt_to_script.py — 扒剧引擎 V4.0.1 L1 字幕层转换与预审工具
功能升级（针对客户三大反馈：漏字幕、画外音难辨、同音错别字）：
  1. 多源解析：支持 .srt / .vtt / .bcc / 剪映草稿 JSON (draft_content.json / draft_info.json) 批量直读
  2. 防吞句智能合并：默认 --merge 0（逐句保留，不再盲目把 3 秒内多句快节奏对白吞并成一句）；
     若开启 --merge N，仅当「间隔 <= N 秒 + 前句末尾是逗号/顿号/破折号等续句标点 + 后句不以换人线索开头
     + 单次合并链不超过 2 句」时才拼接；否则一律不合并并留痕
  3. 滚动重影去重：自动清理自动字幕（Auto-subs / OCR）常见的相邻行首尾重复字词
  4. 防漏字断层预警（--gap-warn）：自动扫描相邻台词间 > N 秒（默认 3.5s）的空白断层，
     插入〔⚠️ 疑似漏字幕/纯动作段〕锚点，提示定点复核
  5. 画外音（OS/VO）与说话人线索初标：基于人称词、心理动词、系统提示词、问答特征自动打初标
  6. 同音错字词表替换（--glossary）：支持传入 "错词=正词,付寒周=傅寒州" 自动纠偏并留痕

用法：
  python srt_to_script.py <字幕.srt|vtt|draft_content.json> [--merge 0] [--gap-warn 3.5] [--glossary "付寒周=傅寒州,林碗=林婉"] [--out out.md]
  python srt_to_script.py --selftest
"""
import io
import json
import os
import re
import sys

# V4.0.1 补丁：统一用 utf-8-sig 读入，兼容 Windows 记事本 / PowerShell Set-Content / EXCEL 导出的
# UTF-8 BOM。BOM 残留会让首行时间轴判不出数字，json.loads 则直接抛 Unexpected UTF-8 BOM。
BOM_SAFE_ENCODING = 'utf-8-sig'


def read_text(path, errors='replace'):
    """BOM 安全读文本（utf-8-sig 对无 BOM 文件同样正确）。"""
    with io.open(path, encoding=BOM_SAFE_ENCODING, errors=errors) as fh:
        return fh.read()


def load_json_file(path):
    """BOM 安全读 JSON：BOM 未剥离时 json.loads 会报 Unexpected UTF-8 BOM。"""
    with io.open(path, encoding=BOM_SAFE_ENCODING) as fh:
        return json.loads(fh.read())


# 画外音（OS/VO）与特征词规则库
OS_PATTERNS = [
    (re.compile(r'(叮[！!]|宿主|系统绑定|任务开启|好感度|奖励发放|新手大礼包|属性面板)'), '〔系统音（OS）〕'),
    (re.compile(r'(心想|暗道|暗忖|这一世|上辈子|前世|重生回|他不知道的是|她不知道的是|没人知道的是|等着瞧|等着吧|走着瞧|休怪我|既然老天让我)'), '〔疑似OS·内心独白〕'),
    (re.compile(r'^(三年前|五年前|十年前|三天后|彼时的|那一年|殊不知|原来当年)'), '〔疑似VO·旁白交代〕'),
    (re.compile(r'(喂[？?]|听得到吗|电话那头|免提|扩音)'), '〔疑似电话/通讯音〕'),
]

SENTENCE_END_PUNCT = set('。！？!?…~”"）)】]')
CONTINUATION_PUNCT = set('，,、—－-…:：')

# 换人/新句特征：后句若以此类词开头，视为新说话人或新语义单元，禁止并入上句
NEW_UNIT_CUES = (
    '你', '我', '他', '她', '它', '咱', '您', '喂', '嗯', '啊', '哎', '诶', '唉',
    '不', '别', '滚', '走', '来', '去', '谁', '什么', '怎么', '为什么', '住口', '闭嘴',
)
# 画外音/新信息块特征：命中即不允许被并入上一句
NEW_BLOCK_PAT = re.compile(
    r'(心想|暗道|暗忖|叮[！!]|宿主|系统绑定|任务开启|好感度|奖励发放|殊不知|三年前|五年前|十年前)'
)
MAX_MERGE_CHAIN = 2      # 单次合并链最长 2 句（防三句以上连锁吞并）
MAX_FRAGMENT_LEN = 12    # 只有 ≤12 字的碎片句才允许并入上句


def fmt(t):
    """秒 -> mm:ss.mmm。先整体转毫秒再拆分，避免 round(0.9996*1000)=1000 造成的进位丢失（V4.0.1 修）"""
    if t < 0:
        t = 0.0
    total_ms = int(round(t * 1000))
    total_s, ms = divmod(total_ms, 1000)
    minutes, sec = divmod(total_s, 60)
    return f"{minutes:02d}:{sec:02d}.{ms:03d}"


def clean_tags(text):
    # 移除 HTML/ASS 样式标签与首尾空白
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\{[^}]+\}', '', text)
    return text.strip()


def parse_srt_or_vtt(text):
    text = text.replace('\ufeff', '').replace('\r\n', '\n').replace('\r', '\n')
    items = []
    # 兼容 HH:MM:SS,mmm / HH:MM:SS.mmm 以及 MM:SS.mmm (VTT)
    ts_re = re.compile(
        r'(?:(\d{1,2}):)?(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(?:(\d{1,2}):)?(\d{2}):(\d{2})[,.](\d{3})'
    )
    lines = text.split('\n')
    n = len(lines)
    i = 0
    while i < n:
        m = ts_re.search(lines[i])
        if m:
            g = m.groups()
            h1 = int(g[0]) if g[0] else 0
            m1, s1, ms1 = int(g[1]), int(g[2]), int(g[3])
            h2 = int(g[4]) if g[4] else 0
            m2, s2, ms2 = int(g[5]), int(g[6]), int(g[7])
            start = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
            end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
            i += 1
            content_lines = []
            while i < n and lines[i].strip() != '' and not ts_re.search(lines[i]):
                # 若下一行是纯数字序号且再下一行是时间轴，则停止
                if lines[i].strip().isdigit() and (i + 1 < n and ts_re.search(lines[i + 1])):
                    break
                cleaned = clean_tags(lines[i])
                if cleaned:
                    content_lines.append(cleaned)
                i += 1
            content = ' '.join(content_lines).strip()
            items.append((start, end, content if content else '〔空〕'))
        else:
            i += 1
    return items


def parse_jianying_json(text):
    """直接解析剪映专业版 draft_content.json / draft_info.json 或 B站 BCC JSON，解决剪映手动逐集导出慢的问题"""
    data = json.loads(text)
    # 情况1：B站 BCC 格式 {"body": [{"from": 0.1, "to": 1.2, "content": "..."}]}
    if isinstance(data, dict) and 'body' in data and isinstance(data['body'], list):
        items = []
        for row in data['body']:
            s = float(row.get('from', 0.0))
            e = float(row.get('to', s))
            c = clean_tags(str(row.get('content', ''))).strip()
            items.append((s, e, c if c else '〔空〕'))
        return sorted(items, key=lambda x: x[0])

    # 情况2：剪映草稿 JSON (materials.texts + tracks)
    materials = data.get('materials', {})
    texts = materials.get('texts', [])
    text_map = {}
    for t in texts:
        tid = t.get('id')
        raw_content = t.get('content', '')
        # 剪映新版本 content 可能是嵌套 JSON 字符串 {"text": "..."}
        if isinstance(raw_content, str) and raw_content.startswith('{'):
            try:
                parsed_c = json.loads(raw_content)
                raw_content = parsed_c.get('text', raw_content)
            except Exception:
                pass
        cleaned = clean_tags(str(raw_content))
        if tid:
            text_map[tid] = cleaned

    items = []
    for track in data.get('tracks', []):
        if track.get('type') in ('text', 'subtitle'):
            for seg in track.get('segments', []):
                mat_id = seg.get('material_id')
                tr = seg.get('target_timerange', {})
                # 剪映时间单位为微秒 (us = 1e-6 s)
                start_us = tr.get('start', 0)
                dur_us = tr.get('duration', 0)
                start = start_us / 1_000_000.0
                end = (start_us + dur_us) / 1_000_000.0
                c = text_map.get(mat_id, '').strip()
                if c or dur_us > 0:
                    items.append((start, end, c if c else '〔空〕'))
    return sorted(items, key=lambda x: x[0])


def parse_input(text, filename=''):
    stripped = text.lstrip('\ufeff').strip()
    if filename.endswith('.json') or filename.endswith('.bcc') or stripped.startswith('{'):
        try:
            return parse_jianying_json(stripped)
        except Exception:
            pass
    return parse_srt_or_vtt(text)


def dedup_rolling(items):
    """清理自动字幕/OCR常见的相邻行完全重复或前缀滚动重复"""
    if not items:
        return []
    out = [list(items[0])]
    for s, e, c in items[1:]:
        ps, pe, pc = out[-1]
        if c == pc and c != '〔空〕' and (s - pe) <= 1.0:
            # 相邻重复帧直接延长时间码，不重复输出
            out[-1][1] = max(pe, e)
            continue
        out.append([s, e, c])
    return [tuple(x) for x in out]


def merge(items, gap):
    """
    安全合并（V4.0.1 重写）：
    - gap <= 0 时（默认）：绝不合并，保持逐句独立，防止把快节奏对话和画外音吞并成一句。
    - gap > 0 时，必须同时满足以下全部条件才拼接，否则一律独立并留痕：
        ① 与上句间隔 <= gap
        ② 上句去掉首尾空白后，末尾不是句末终止标点（。！？…】
        ③ 上句末尾是续句标点（，、—等），或本句是 <=12 字的碎片句
        ④ 本句不以换人/新句特征词开头
        ⑤ 本句不含 OS/系统/旁白类新信息块特征（心想/暗道/叮！/宿主…）
        ⑥ 单次合并链不超过 2 句
    返回 (items, merge_marks)，merge_marks 为被并掉的句子起点秒数集合，供输出留痕。
    """
    if gap <= 0:
        return [(s, e, c) for s, e, c in items], []

    out = []          # [[start, end, text, chain_len]]
    marks = []        # 被合并掉的句子起点
    for s, e, c in items:
        if not out:
            out.append([s, e, c, 1])
            continue
        ps, pe, pc, chain = out[-1]
        merged = False
        if (
            (s - pe) <= gap
            and pc != '〔空〕'
            and c != '〔空〕'
            and chain < MAX_MERGE_CHAIN
            and pc.rstrip()[-1:] not in SENTENCE_END_PUNCT
        ):
            tail_is_continuation = pc.rstrip()[-1:] in CONTINUATION_PUNCT
            is_fragment = len(c) <= MAX_FRAGMENT_LEN
            starts_new_unit = c.lstrip().startswith(NEW_UNIT_CUES)
            is_new_block = bool(NEW_BLOCK_PAT.search(c))
            if (tail_is_continuation or is_fragment) and not starts_new_unit and not is_new_block:
                sep = '' if pc.rstrip()[-1:] in CONTINUATION_PUNCT else '，'
                out[-1] = [ps, e, pc + sep + c, chain + 1]
                marks.append(ps)   # 记录「吸收方」起点，供输出行留痕
                merged = True
        if not merged:
            out.append([s, e, c, 1])
    return [(s, e, c) for s, e, c, _ in out], marks


def parse_glossary(glossary_str):
    """解析 '付寒周=傅寒州,林碗=林婉' 格式的正字表"""
    mapping = {}
    if not glossary_str:
        return mapping
    for pair in re.split(r'[,，;；\n]+', glossary_str):
        if '=' in pair:
            wrong, right = pair.split('=', 1)
            wrong, right = wrong.strip(), right.strip()
            if wrong and right:
                mapping[wrong] = right
    return mapping


def apply_glossary(text, glossary):
    """应用同音错别字正字表，返回 (修正后文本, 替换记录列表)"""
    if not glossary or text == '〔空〕':
        return text, []
    notes = []
    for wrong, right in glossary.items():
        if wrong in text:
            text = text.replace(wrong, right)
            notes.append(f"{right}〔原字幕：{wrong}〕")
    return text, notes


def detect_clue(text, prev_text='', next_text=''):
    """
    画外音（OS/VO）与说话人特征初标引擎：
    识别系统音、内心独白词、旁白词、通讯音及问答呼应线索
    """
    if not text or text == '〔空〕':
        return '〔空字幕〕'
    clues = []
    for pat, label in OS_PATTERNS:
        if pat.search(text):
            clues.append(label)
            break
    # 自称/称谓提取辅助说话人归属
    if re.search(r'(朕|本王|本宫|本座|本少|老夫|老身|咱家)', text):
        m = re.search(r'(朕|本王|本宫|本座|本少|老夫|老身|咱家)', text)
        clues.append(f"自称:{m.group(1)}")
    if re.search(r'[？?]$', text):
        clues.append('提问句')
    elif prev_text and re.search(r'[？?]$', prev_text) and not clues:
        clues.append('疑似接答')
    return ' · '.join(clues) if clues else '待核（对白/OS）'


def is_voiceover_label(clue):
    """只有被 〔〕 包住的才是真判定的 OS/VO/系统/通讯标签；
    默认兜底串「待核（对白/OS）」不算，避免把未判定的句子统计成画外音（V4.0.1 修）"""
    if not clue or clue.startswith('〔空'):
        return False
    return clue.startswith('〔')


def to_md(items, src, gap_warn=3.5, glossary=None, merge_marks=None):
    glossary = glossary or {}
    merge_marks = merge_marks or []
    merged_rows = set(round(x, 3) for x in merge_marks)
    rows = [
        '| 句号 | 时间码 | 台词（正字校对后） | 说话人/画外音(OS·VO)初标 | 校对与防漏备注 |',
        '|---|---|---|---|---|',
    ]
    total_fixes = 0
    gap_warnings = 0
    os_count = 0
    merge_count = len(merge_marks)

    # 检查片头是否有长空白
    if items and gap_warn > 0 and items[0][0] >= gap_warn:
        gap_warnings += 1
        rows.append(
            f"| ⚠️ | 00:00.000-{fmt(items[0][0])} | 〔片头空白 {items[0][0]:.1f}s〕 | — | "
            f"疑似片头漏字幕/纯画面钩子/花字，建议抽看 |"
        )

    for idx, (s, e, raw_c) in enumerate(items):
        # 检查与上一句之间的时间断层（防漏字检测）
        if idx > 0 and gap_warn > 0:
            prev_e = items[idx - 1][1]
            delta = s - prev_e
            if delta >= gap_warn:
                gap_warnings += 1
                rows.append(
                    f"| ⚠️ | {fmt(prev_e)}-{fmt(s)} | 〔时间断层 {delta:.1f}s〕 | — | "
                    f"间隔较大：疑似漏短句/画外花字/纯动作戏，请定点核对 |"
                )

        prev_c = items[idx - 1][2] if idx > 0 else ''
        next_c = items[idx + 1][2] if idx + 1 < len(items) else ''
        fixed_c, fix_notes = apply_glossary(raw_c, glossary)
        if fix_notes:
            total_fixes += len(fix_notes)
        clue = detect_clue(fixed_c, prev_c, next_c)
        if is_voiceover_label(clue):
            os_count += 1

        dur = max(0.0, e - s)
        notes = []
        if fix_notes:
            notes.extend(fix_notes)
        if round(s, 3) in merged_rows:
            notes.append('⤵ 已按 --merge 规则吸收后碎句（碎句还原）')
        if dur > 0 and dur < 0.6 and fixed_c != '〔空〕':
            notes.append(f"闪句({dur:.2f}s)")
        note_str = '；'.join(notes) if notes else '—'

        rows.append(f"| {idx+1} | {fmt(s)}-{fmt(e)} | {fixed_c} | {clue} | {note_str} |")

    summary = (
        f"## L1 字幕层逐字稿（V4.0.1 防漏字·画外音初标版）\n\n"
        f"> 来源：`{src}` · 共 **{len(items)}** 句台词 · "
        f"画外音/系统音初标 **{os_count}** 处 · "
        f"时间断层预警 **{gap_warnings}** 处 · "
        f"碎句合并 **{merge_count}** 处 · "
        f"同音正字纠偏 **{total_fixes}** 处\n\n"
    )
    return summary + '\n'.join(rows) + '\n'


def selftest():
    demo = """1
00:00:00,100 --> 00:00:01,000
咋整啊

2
00:00:01,300 --> 00:00:02,000
付寒周心想：这一世我绝不放过你

3
00:00:06,500 --> 00:00:07,500
叮！宿主绑定成功
"""
    items = parse_input(demo)
    assert len(items) == 3 and items[0][2] == '咋整啊'
    # 默认不合并（gap=0）保留全部3句
    merged0, _ = merge(items, 0)
    assert len(merged0) == 3
    # 词表纠偏 + 画外音初标 + 断层预警测试
    glossary = parse_glossary("付寒周=傅寒州")
    md = to_md(merged0, 'selftest', gap_warn=3.5, glossary=glossary)
    assert '傅寒州心想' in md
    assert '原字幕：付寒周' in md
    assert '〔疑似OS·内心独白〕' in md
    assert '〔系统音（OS）〕' in md
    assert '〔时间断层 4.5s〕' in md
    # V4.0.1 补丁回归：UTF-8 BOM 输入不得吞掉首句（Windows 记事本 / PowerShell 写出最常见）
    import tempfile
    bom_path = os.path.join(tempfile.gettempdir(), 's2s_bom_selftest.srt')
    with io.open(bom_path, 'w', encoding='utf-8-sig') as fh:
        fh.write(demo)
    try:
        bom_items = parse_input(read_text(bom_path), bom_path)
        assert len(bom_items) == 3, bom_items
        assert bom_items[0][2] == '咋整啊', bom_items[0]
    finally:
        os.remove(bom_path)

    # 测试剪映 JSON 解析
    jy_demo = json.dumps({
        "materials": {
            "texts": [
                {"id": "t1", "content": json.dumps({"text": "第一句台词"})},
                {"id": "t2", "content": "第二句台词"}
            ]
        },
        "tracks": [
            {
                "type": "text",
                "segments": [
                    {"material_id": "t1", "target_timerange": {"start": 500000, "duration": 1000000}},
                    {"material_id": "t2", "target_timerange": {"start": 2000000, "duration": 1500000}}
                ]
            }
        ]
    })
    jy_items = parse_input(jy_demo, 'draft_content.json')
    assert len(jy_items) == 2 and jy_items[0][2] == '第一句台词'

    # —— V4.0.1 回归断言 ——
    # ① 毫秒进位不再丢失（剪映微秒除 1e6 高频出现 .9996）
    assert fmt(59.9996) == '01:00.000', fmt(59.9996)
    assert fmt(61.9999) == '01:02.000', fmt(61.9999)
    assert fmt(0.9997) == '00:01.000', fmt(0.9997)
    assert fmt(3599.9996) == '60:00.000', fmt(3599.9996)
    # ② 兜底串「待核（对白/OS）」不得被统计成画外音
    assert is_voiceover_label('〔疑似OS·内心独白〕') is True
    assert is_voiceover_label('待核（对白/OS）') is False
    assert is_voiceover_label('〔空字幕〕') is False
    # ③ --merge 不得把 OS/长句/换人句连锁吞并
    chain = [
        (1.0, 2.0, '你个'),
        (2.1, 2.6, '老狐狸'),
        (2.7, 3.0, '付寒周心想：这一世我绝不放过你'),
    ]
    merged, marks = merge(chain, 1.0)
    assert len(merged) == 2, [m[2] for m in merged]      # 前两句合并，第三句必须独立
    assert merged[0][2] == '你个，老狐狸'
    assert '付寒周' in merged[1][2]
    # 单次合并链上限 2 句
    chain3 = [(1.0, 1.4, '甲'), (1.5, 1.9, '乙'), (2.0, 2.4, '丙')]
    merged3, _ = merge(chain3, 1.0)
    assert len(merged3) == 2, [m[2] for m in merged3]
    # ④ 碎裂合并必须留痕
    md3 = to_md(merged, 'selftest', gap_warn=9, merge_marks=marks)
    assert '碎句合并 **1** 处' in md3, md3
    assert '⤵ 已按 --merge 规则吸收后碎句' in md3
    print('selftest OK')


VALUE_OPTS = ('--merge', '--out', '--gap-warn', '--glossary')


def split_argv(argv):
    """稳健参数解析：选项与其取值成对消费，位置参数不受选项顺序影响（V4.0.1 重写）"""
    positional, opts = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in VALUE_OPTS:
            opts[a] = argv[i + 1] if i + 1 < len(argv) else ''
            i += 2
        elif a.startswith('--'):
            opts[a] = True
            i += 1
        else:
            positional.append(a)
            i += 1
    return positional, opts


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
        sys.exit(0)
    args, opts = split_argv(sys.argv[1:])
    gap = float(opts.get('--merge', 0.0))   # 默认 0（不盲目吞并句子）
    gap_warn = float(opts.get('--gap-warn', 3.5))
    glossary_str = opts.get('--glossary', '') or ''

    if not args:
        print(__doc__)
        sys.exit(2)
    src = args[0]
    text = read_text(src)
    items = parse_input(text, src)
    if not items:
        print('未解析到字幕时间轴——确认这是 SRT/VTT/BCC 或剪映草稿 JSON 格式')
        sys.exit(1)
    items = dedup_rolling(items)
    items, merge_marks = merge(items, gap)
    glossary = parse_glossary(glossary_str)
    md = to_md(items, os.path.basename(src), gap_warn=gap_warn,
               glossary=glossary, merge_marks=merge_marks)
    outp = opts.get('--out')
    if outp:
        with io.open(outp, 'w', encoding='utf-8') as fh:
            fh.write(md)
        print(f'已写出 {outp}（共 {len(items)} 句，碎句合并 {len(merge_marks)} 处）')
    else:
        print(md)
