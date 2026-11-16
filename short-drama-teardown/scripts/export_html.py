# -*- coding: utf-8 -*-
"""
export_html.py — 短剧扒剧本 · 深度还原 Skill V4.0.1 离线单页 HTML 文档 & CSV 导出器
功能：
  1. 读取结构化 JSON，一键生成【100% 离线可用、单文件零外部依赖】的单页连续滚动 HTML 剧本还原报告（无需分页切换，从上到下流畅阅读、打印或导出 PDF）。
  2. 顶部自带悬浮目录锚点（点击平滑跳转各模块）、明暗主题切换、一键复制整集剧本、一键导出逐字稿/台词 CSV 表格。
  3. 包含四大核心模块（同页顺序展开）：
     - 一、《全集唯一出场人物视觉与称谓锁定表》
     - 二、《深度还原剧本》（场次、△动作与神态调度、对白、OS/VO 清晰高亮，支持一键复制整集剧本）
     - 三、《骨架分析卡》（结构公式、节拍表、钩子/OS爽点盘点、可迁移 vs 不可迁移）
     - 四、《L1+L2 逐句 1:1 画面绑定逐字稿》
  4. ★V4.0.1 新增：`--write-example` 直接吐出符合本脚本字段的示例 JSON（字段口径唯一权威 = references/data-schema.json）；
     生成前先做字段体检，缺关键字段会明确报警而不是产出一份四块空白的报告；打印/PDF 强制浅色，不再黑底黑字。
  5. JSON/data.json 字段定义见 references/data-schema.json（脚本内 selftest 的 demo 与之一致）。

用法：
  python export_html.py <teardown_data.json> [--out script_report.html] [--theme light|dark]
  python export_html.py --write-example  [--out example_data.json]
  python export_html.py --selftest
"""
import html
import io
import json
import os
import sys

# V4.0.1 补丁：utf-8-sig 读入，兼容 Windows 记事本 / PowerShell 写出的 UTF-8 BOM。
# BOM 未剥离时 json.loads 直接抛 Unexpected UTF-8 BOM，整个出稿流程当场死掉。
BOM_SAFE_ENCODING = "utf-8-sig"


def load_json_file(path):
    """BOM 安全读 JSON（utf-8-sig 对无 BOM 文件同样正确）。"""
    with io.open(path, encoding=BOM_SAFE_ENCODING) as fh:
        return json.loads(fh.read())


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="__DEFAULT_THEME__">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>__PAGE_TITLE__</title>
<style>
  :root {
    --bg: #0d1117;
    --surface: #161b22;
    --surface-2: #1f2630;
    --border: #30363d;
    --text: #e6edf3;
    --text-muted: #8b949e;
    --accent: #58a6ff;
    --accent-soft: rgba(88, 166, 255, 0.14);
    --green: #3fb950;
    --amber: #d29922;
    --purple: #bc8cff;
    --shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    --radius: 10px;
  }
  [data-theme="light"] {
    --bg: #f6f8fa;
    --surface: #ffffff;
    --surface-2: #f0f3f6;
    --border: #d0d7de;
    --text: #1f2328;
    --text-muted: #656d76;
    --accent: #0969da;
    --accent-soft: rgba(9, 105, 218, 0.1);
    --green: #1a7f37;
    --amber: #9a6700;
    --purple: #8250df;
    --shadow: 0 4px 16px rgba(31, 35, 40, 0.08);
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.65;
  }
  .container { max-width: 1200px; margin: 0 auto; padding: 20px 24px 80px; }
  .header {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    box-shadow: var(--shadow);
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 14px;
  }
  .title-wrap h1 { margin: 0 0 8px; font-size: 22px; font-weight: 700; }
  .meta-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 13px; color: var(--text-muted); }
  .badge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;
    background: var(--accent-soft); color: var(--accent);
  }
  .badge.warn { background: rgba(210, 153, 34, 0.14); color: var(--amber); }
  .badge.ok { background: rgba(63, 185, 80, 0.14); color: var(--green); }
  .header-actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .btn {
    cursor: pointer; border: 1px solid var(--border); background: var(--surface-2);
    color: var(--text); padding: 7px 14px; border-radius: 8px; font-size: 13px; font-weight: 500;
    transition: all 0.15s ease; display: inline-flex; align-items: center; gap: 6px;
  }
  .btn:hover { border-color: var(--accent); color: var(--accent); }
  .btn.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
  .btn.primary:hover { opacity: 0.9; color: #fff; }
  .btn.copied { background: var(--green); color: #fff; border-color: var(--green); }

  .toc-bar {
    position: sticky; top: 0; z-index: 20;
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 10px 16px; margin-bottom: 18px; box-shadow: var(--shadow);
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  }
  .toc-bar span { font-size: 12.5px; color: var(--text-muted); font-weight: 600; margin-right: 4px; }
  .toc-link {
    text-decoration: none; color: var(--text); background: var(--surface-2);
    border: 1px solid var(--border); padding: 5px 12px; border-radius: 999px; font-size: 13px; font-weight: 500;
  }
  .toc-link:hover { border-color: var(--accent); color: var(--accent); }

  .section-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 22px 24px; margin-bottom: 22px; box-shadow: var(--shadow);
    scroll-margin-top: 66px;
  }
  .section-head {
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px;
    border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 16px;
  }
  .section-head h2 { margin: 0; font-size: 18px; font-weight: 700; }

  .table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th, td { padding: 11px 13px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { background: var(--surface-2); font-weight: 600; color: var(--text); white-space: nowrap; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(88, 166, 255, 0.04); }
  .timecode { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12.5px; white-space: nowrap; color: var(--text-muted); }

  .scene-block { margin-bottom: 22px; padding-bottom: 18px; border-bottom: 1px dashed var(--border); }
  .scene-block:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
  .scene-title { font-size: 16px; font-weight: 700; color: var(--accent); margin-bottom: 10px; }
  .action-line {
    background: var(--surface-2); border-left: 3px solid var(--amber);
    padding: 9px 13px; border-radius: 0 6px 6px 0; margin: 10px 0; font-size: 13.5px;
  }
  .dialogue-line { margin: 10px 0 10px 12px; font-size: 14.5px; }
  .speaker { font-weight: 700; color: var(--green); }
  .speaker.os { color: var(--purple); }
  .stage-dir { font-size: 13px; color: var(--text-muted); margin-left: 4px; }
  .formula-box {
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
    padding: 14px 16px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13.5px;
    white-space: pre-wrap; margin-bottom: 16px;
  }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 16px; }
  .sub-box { background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
  .sub-box h3 { margin: 0 0 10px; font-size: 15px; }
  .copyright-note { font-size: 12px; color: var(--amber); margin-top: 6px; }

  @media print {
    /* V4.0.1：打印/转 PDF 强制浅色全套变量，避免 dark 主题下「深底 + 继承#000」的黑底黑字 */
    :root, [data-theme="dark"], [data-theme="light"] {
      --bg: #ffffff;
      --surface: #ffffff;
      --surface-2: #f5f7f9;
      --border: #c9d1d9;
      --text: #111111;
      --text-muted: #4a4a4a;
      --accent: #0b4f9e;
      --accent-soft: rgba(11, 79, 158, 0.08);
      --green: #0f6b2d;
      --amber: #7a5200;
      --purple: #5b2fc0;
      --shadow: none;
    }
    .toc-bar, .header-actions, .btn { display: none !important; }
    body { background: #fff; color: #111; }
    .section-card, .header { box-shadow: none; border-color: #c9d1d9; break-inside: avoid; }
    .table-wrap, table, th, td { border-color: #c9d1d9 !important; }
    th, tr, td { background: #fff !important; color: #111 !important; }
    tr:hover td { background: #fff !important; }
    .action-line { background: #f5f7f9 !important; color: #111 !important; border-left-color: #7a5200 !important; }
    .formula-box, .sub-box { background: #f5f7f9 !important; color: #111 !important; }
    .speaker { color: #0f6b2d !important; }
    .speaker.os { color: #5b2fc0 !important; }
    .scene-title { color: #0b4f9e !important; }
    .copyright-note { color: #7a5200 !important; }
    a { color: #111 !important; text-decoration: none; }
  }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="title-wrap">
      <h1 id="drama-title"></h1>
      <div class="meta-row" id="drama-meta"></div>
      <div class="copyright-note">⚠️ 拆解学习用途 · 骨架与结构可迁移 · 原作台词与专有设定不可照搬商用 · 生成器 export_html.py V4.0.1</div>
    </div>
    <div class="header-actions">
      <button class="btn" onclick="toggleTheme()">🌓 明暗切换</button>
      <button class="btn" onclick="exportCSV()">📥 导出逐字稿 CSV</button>
      <button class="btn primary" onclick="copyScript(this)">📋 一键复制整集剧本</button>
    </div>
  </div>

  <nav class="toc-bar">
    <span>快速定位：</span>
    <a class="toc-link" href="#sec-chars">👤 一、唯一人物锁定</a>
    <a class="toc-link" href="#sec-script">📜 二、深度还原剧本</a>
    <a class="toc-link" href="#sec-skeleton">🧩 三、骨架分析卡</a>
    <a class="toc-link" href="#sec-transcript">📝 四、逐句绑定逐字稿</a>
  </nav>

  <!-- 一、唯一人物锁定表 -->
  <section id="sec-chars" class="section-card">
    <div class="section-head">
      <h2>👤 一、《全集唯一出场人物视觉与称谓锁定表》</h2>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>唯一标准角色名</th><th>外貌与服装基线</th><th>同人形态归并（禁拆新角）</th><th>台词称谓证据</th><th>声线特征</th></tr></thead>
        <tbody id="chars-tbody"></tbody>
      </table>
    </div>
  </section>

  <!-- 二、深度还原剧本 -->
  <section id="sec-script" class="section-card">
    <div class="section-head">
      <h2>📜 二、《深度还原剧本》</h2>
      <button class="btn" onclick="copyScript(this)">📋 复制整集剧本</button>
    </div>
    <div id="script-container"></div>
  </section>

  <!-- 三、骨架分析卡 -->
  <section id="sec-skeleton" class="section-card">
    <div class="section-head">
      <h2>🧩 三、《骨架分析卡》</h2>
    </div>
    <div class="formula-box" id="skeleton-formula"></div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>集/段</th><th>钩子（秒位+手段）</th><th>冲突升级</th><th>反转/爽点（含OS）</th><th>断章钩</th><th>强度</th></tr></thead>
        <tbody id="beats-tbody"></tbody>
      </table>
    </div>
    <div class="grid-2">
      <div class="sub-box">
        <h3>🎣 钩子与画外音（OS/VO）盘点</h3>
        <div id="hooks-list"></div>
      </div>
      <div class="sub-box">
        <h3>⚖️ 可迁移 vs 不可迁移</h3>
        <div id="transfer-list"></div>
      </div>
    </div>
  </section>

  <!-- 四、逐句绑定逐字稿 -->
  <section id="sec-transcript" class="section-card">
    <div class="section-head">
      <h2>📝 四、《L1+L2 逐句 1:1 画面绑定逐字稿》</h2>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>句号</th><th>时间码</th><th>台词（正字校对后）</th><th>唯一说话人 &amp; 属性</th><th>该秒画面实录与嘴型核验</th></tr></thead>
        <tbody id="transcript-tbody"></tbody>
      </table>
    </div>
  </section>
</div>

<script>
const DATA = __JSON_DATA__;

function esc(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function copyText(text, btn) {
  const done = () => {
    const old = btn.innerHTML;
    btn.classList.add('copied');
    btn.innerHTML = '✅ 已复制';
    setTimeout(() => { btn.classList.remove('copied'); btn.innerHTML = old; }, 1400);
  };
  const fallback = () => {
    // V4.0.1：clipboard API 在 file:// / 非安全上下文 / 部分浏览器会被拒，退回 execCommand
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.top = '-1000px';
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      if (ok) { done(); return; }
    } catch (e) {}
    alert('当前浏览器阻止了自动复制：请手动全选下方剧本区内容复制。');
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done).catch(fallback);
  } else {
    fallback();
  }
}

function toggleTheme() {
  const htmlEl = document.documentElement;
  htmlEl.setAttribute('data-theme', htmlEl.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}

function initHeader() {
  const m = DATA.meta || {};
  document.getElementById('drama-title').textContent = `${m.title || '未命名短剧'} · ${m.episode || 'EP01'} 剧本深度还原报告`;
  const pills = [];
  if (m.channel) pills.push(`<span class="badge">${esc(m.channel)}</span>`);
  if (m.duration) pills.push(`<span>⏱️ 总时长：<b>${esc(m.duration)}</b></span>`);
  pills.push(`<span>🎭 场次数：<b>${(DATA.script_scenes || []).length}</b> 场</span>`);
  pills.push(`<span>👤 锁定人物：<b>${(DATA.characters || []).length}</b> 人</span>`);
  pills.push(`<span>💬 总句数：<b>${(DATA.transcript || []).length}</b> 句</span>`);
  if (m.date) pills.push(`<span>📅 ${esc(m.date)}</span>`);
  document.getElementById('drama-meta').innerHTML = pills.join('');
}

function exportCSV() {
  const headers = ['句号', '时间码', '台词', '唯一说话人及属性', '画面实录与嘴型核验'];
  const rows = (DATA.transcript || []).map(t => [
    t.index, t.timecode, t.text, t.speaker, t.frame_note
  ].map(v => '"' + String(v || '').replace(/"/g, '""') + '"').join(','));
  const csv = '\uFEFF' + headers.join(',') + '\n' + rows.join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${(DATA.meta && DATA.meta.title) || 'script_teardown'}_transcript.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function renderScript() {
  const scenes = DATA.script_scenes || [];
  document.getElementById('script-container').innerHTML = scenes.map(sc => {
    const blocks = (sc.blocks || []).map(b => {
      if (b.type === 'action') return `<div class="action-line">△ ${esc(b.text)}</div>`;
      const isOS = (b.speaker || '').includes('OS') || (b.speaker || '').includes('VO');
      return `<div class="dialogue-line"><span class="speaker ${isOS ? 'os' : ''}">${esc(b.speaker)}</span>${b.direction ? `<span class="stage-dir">（${esc(b.direction)}）</span>` : ''}：${esc(b.text)}</div>`;
    }).join('');
    return `<div class="scene-block"><div class="scene-title">${esc(sc.header)}</div>${blocks}</div>`;
  }).join('');
}

function copyScript(btn) {
  const txt = (DATA.script_scenes || []).map(sc => {
    const lines = [sc.header];
    (sc.blocks || []).forEach(b => {
      if (b.type === 'action') lines.push('△ ' + b.text);
      else lines.push(`${b.speaker}${b.direction ? '（' + b.direction + '）' : ''}：${b.text}`);
    });
    return lines.join('\n');
  }).join('\n\n');
  copyText(txt, btn);
}

function renderSkeleton() {
  const sk = DATA.skeleton || {};
  document.getElementById('skeleton-formula').textContent = sk.formula || '暂无结构公式';
  document.getElementById('beats-tbody').innerHTML = (sk.beats || []).map(b => `
    <tr>
      <td><b>${esc(b.unit)}</b></td>
      <td>${esc(b.hook)}</td>
      <td>${esc(b.escalation)}</td>
      <td>${esc(b.twist)}</td>
      <td>${esc(b.cliffhanger)}</td>
      <td>${esc(b.intensity)}</td>
    </tr>
  `).join('');
  document.getElementById('hooks-list').innerHTML = (sk.hooks || []).map(h => `
    <p><b>${esc(h.type)}</b>：${esc(h.method)}<br/><span style="color:var(--text-muted); font-size:12.5px;">原样证据：${esc(h.evidence)}</span></p>
  `).join('') || '<p style="color:var(--text-muted);">暂无</p>';
  document.getElementById('transfer-list').innerHTML = `
    <p><span class="badge ok">可迁移骨架</span></p>
    <ul>${(sk.transferable || []).map(x => `<li>${esc(x)}</li>`).join('')}</ul>
    <p><span class="badge warn">不可迁移表达</span></p>
    <ul>${(sk.non_transferable || []).map(x => `<li>${esc(x)}</li>`).join('')}</ul>
  `;
}

function renderCharactersAndTranscript() {
  document.getElementById('chars-tbody').innerHTML = (DATA.characters || []).map(c => `
    <tr>
      <td><b>${esc(c.name)}</b></td>
      <td>${esc(c.appearance)}</td>
      <td>${esc(c.variants)}</td>
      <td>${esc(c.evidence)}</td>
      <td>${esc(c.voice)}</td>
    </tr>
  `).join('');
  document.getElementById('transcript-tbody').innerHTML = (DATA.transcript || []).map(t => `
    <tr>
      <td>${esc(t.index)}</td>
      <td class="timecode">${esc(t.timecode)}</td>
      <td>${esc(t.text)}</td>
      <td><b>${esc(t.speaker)}</b></td>
      <td>${esc(t.frame_note)}</td>
    </tr>
  `).join('');
}

initHeader();
renderScript();
renderSkeleton();
renderCharactersAndTranscript();
</script>
</body>
</html>
"""


EXAMPLE_DATA = {
    "meta": {
        "title": "示例短剧",
        "episode": "EP01",
        "channel": "通道 B（直接发视频 · 强视觉锚定）",
        "duration": "00:15",
        "date": "2026-11-16",
    },
    "characters": [
        {
            "name": "涂山瑶（涂山老祖宗）",
            "appearance": "浅灰白汉服，黑长发",
            "variants": "常态黑瞳 / 施法黄金瞳 / 九条白尾",
            "evidence": "00:05 称「瑶瑶」",
            "voice": "清冷御姐音",
        }
    ],
    "transcript": [
        {
            "index": 1,
            "timecode": "00:03.000-00:06.000",
            "text": "瑶瑶，守好家。",
            "speaker": "褐衣长发男（现场对白）",
            "frame_note": "00:04.5 褐衣长发男抱拳张嘴说话",
        }
    ],
    "script_scenes": [
        {
            "header": "第 1 场 · 古树林（日 · 外 · 00:00-00:15）",
            "blocks": [
                {"type": "action", "text": "古树参天，微风拂动落叶。"},
                {"type": "dialogue", "speaker": "褐衣长发男", "direction": "抱拳拱手", "text": "瑶瑶，守好家。"},
                {"type": "dialogue", "speaker": "涂山瑶（OS）", "direction": "嘴唇紧闭，瞳孔微泛金光",
                 "text": "这一世，休想再动我涂山一分。"},
            ],
        }
    ],
    "skeleton": {
        "formula": "1场戏 · 3拍：前3秒氛围建立 → 第4秒同伴托付 → 第10秒女主OS亮底牌",
        "beats": [
            {"unit": "EP01", "hook": "00:00 古树冷调背影", "escalation": "灵源危机交代",
             "twist": "00:10 金瞳OS亮底牌", "cliffhanger": "00:14 树林异动", "intensity": "4/5"}
        ],
        "hooks": [{"type": "OS信息差钩", "method": "闭口金瞳反差", "evidence": "这一世，休想再动我涂山一分。"}],
        "transferable": ["同伴托付后接主角闭口OS反转预期"],
        "non_transferable": ["涂山瑶专有名词与具体台词"],
    },
}

TRANSCRIPT_KEYS = ("index", "timecode", "text", "speaker", "frame_note")
CHARACTER_KEYS = ("name", "appearance", "variants", "evidence", "voice")
BEAT_KEYS = ("unit", "hook", "escalation", "twist", "cliffhanger", "intensity")


def validate_data(data):
    """字段体检（V4.0.1）：返回 (blocking_errors, warnings)。
    blocking 为空才允许出报告；warnings 逐条打印，避免「静默产出四块空白报告」。"""
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["顶层必须是 JSON 对象 {...}"], []

    scenes = data.get("script_scenes") or []
    transcript = data.get("transcript") or []
    if not isinstance(scenes, list):
        errors.append("script_scenes 必须是数组")
        scenes = []
    if not isinstance(transcript, list):
        errors.append("transcript 必须是数组")
        transcript = []
    if not scenes and not transcript:
        errors.append("transcript 与 script_scenes 同时为空——没有任何可渲染内容，拒绝出稿")

    if not isinstance(data.get("meta"), dict):
        warnings.append("缺 meta 对象（title/episode/channel/duration/date），标题将显示「未命名短剧」")
    if not transcript:
        warnings.append("transcript 为空：第四节《逐句 1:1 逐字稿》与 CSV 导出将为空表")
    if not scenes:
        warnings.append("script_scenes 为空：第二节《深度还原剧本》将为空")
    if not data.get("characters"):
        warnings.append("characters 为空：第一节《唯一人物锁定表》将为空")
    sk = data.get("skeleton")
    if not isinstance(sk, dict):
        warnings.append("缺 skeleton 对象：第三节《骨架分析卡》将为空")

    for i, t in enumerate(transcript, 1):
        if not isinstance(t, dict):
            warnings.append(f"transcript 第 {i} 条不是对象")
            continue
        miss = [k for k in TRANSCRIPT_KEYS if k not in t]
        if miss:
            warnings.append(f"transcript 第 {i} 条缺字段 {miss}（HTML 该列会空）")
    for i, c in enumerate(data.get("characters") or [], 1):
        if not isinstance(c, dict):
            warnings.append(f"characters 第 {i} 条不是对象")
            continue
        miss = [k for k in CHARACTER_KEYS if k not in c]
        if miss:
            warnings.append(f"characters 第 {i} 条缺字段 {miss}")
    for i, sc in enumerate(scenes, 1):
        if not isinstance(sc, dict):
            warnings.append(f"script_scenes 第 {i} 场不是对象")
            continue
        if not sc.get("header"):
            warnings.append(f"script_scenes 第 {i} 场缺 header（场号/日夜内外/起止秒）")
        blocks = sc.get("blocks") or []
        if not isinstance(blocks, list):
            warnings.append(f"script_scenes 第 {i} 场 blocks 不是数组")
            continue
        for j, b in enumerate(blocks, 1):
            if not isinstance(b, dict):
                warnings.append(f"第 {i} 场第 {j} 个 block 不是对象")
                continue
            btype = b.get("type", "dialogue")
            if btype not in ("action", "dialogue"):
                warnings.append(f"第 {i} 场第 {j} 个 block 的 type={btype!r} 非法（只认 action/dialogue）")
            if btype == "dialogue":
                miss = [k for k in ("speaker", "text") if not b.get(k)]
                if miss:
                    warnings.append(f"第 {i} 场第 {j} 条对白缺 {miss}")
            elif not b.get("text"):
                warnings.append(f"第 {i} 场第 {j} 条动作缺 text")
    if isinstance(sk, dict):
        if not sk.get("formula"):
            warnings.append("skeleton.formula 为空：结构公式区将显示「暂无结构公式」")
        for i, b in enumerate(sk.get("beats") or [], 1):
            miss = [k for k in BEAT_KEYS if k not in b]
            if miss:
                warnings.append(f"skeleton.beats 第 {i} 条缺字段 {miss}")
    return errors, warnings


def build_html(data: dict, theme: str = "light") -> str:
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    title = f"{meta.get('title', '短剧扒剧本')} · {meta.get('episode', 'EP01')} — 剧本深度还原报告"
    safe_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = HTML_TEMPLATE.replace("__DEFAULT_THEME__", "dark" if theme == "dark" else "light")
    out = out.replace("__PAGE_TITLE__", html.escape(title))
    out = out.replace("__JSON_DATA__", safe_json)
    return out


def selftest():
    demo = EXAMPLE_DATA
    html_out = build_html(demo)
    assert "<!DOCTYPE html>" in html_out
    assert "剧本深度还原报告" in html_out
    assert "涂山瑶（涂山老祖宗）" in html_out
    # V4.0.1：占位符必须全部替换；默认浅色主题；打印块含浅色变量
    for ph in ("__DEFAULT_THEME__", "__PAGE_TITLE__", "__JSON_DATA__"):
        assert ph not in html_out, ph
    assert 'data-theme="light"' in html_out
    assert '<html lang="zh-CN" data-theme="dark">' in build_html(demo, theme="dark")
    assert "--surface-2: #f5f7f9;" in html_out          # 打印强制浅色
    assert ".action-line { background: #f5f7f9 !important;" in html_out
    # 复制按钮必须有降级回退
    assert "execCommand('copy')" in html_out
    # 字段体检
    errs, warns = validate_data(demo)
    assert errs == [] and warns == [], (errs, warns)
    errs2, _ = validate_data({"meta": {"title": "空"}, "transcript": [], "script_scenes": []})
    assert errs2, "空内容必须被拦下"
    _, warns3 = validate_data({"meta": {}, "characters": [{"name": "甲"}],
                               "transcript": [{"index": 1}],
                               "script_scenes": [{"blocks": [{"type": "dialogue"}]}]})
    assert any("缺字段" in w for w in warns3), warns3
    # </script> 注入必须转义
    evil = {"meta": {"title": "x"}, "transcript": [{"index": 1, "text": "</script><b>x</b>"}],
            "script_scenes": [{"header": "s", "blocks": []}]}
    assert "</script><b>x</b>" not in build_html(evil)
    # V4.0.1 补丁回归：带 UTF-8 BOM 的 data.json 必须能读（Windows 手写 JSON 常见坑）
    import tempfile
    bom_path = os.path.join(tempfile.gettempdir(), "export_html_bom_selftest.json")
    with io.open(bom_path, "w", encoding="utf-8-sig") as fh:
        fh.write(json.dumps(EXAMPLE_DATA, ensure_ascii=False))
    try:
        assert load_json_file(bom_path)["meta"]["title"] == EXAMPLE_DATA["meta"]["title"]
    finally:
        os.remove(bom_path)
    print("selftest OK (HTML length:", len(html_out), "chars)")


VALUE_OPTS = ("--out", "--theme")


def split_argv(argv):
    positional, opts = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in VALUE_OPTS:
            if i + 1 >= len(argv):
                print(f"错误：参数 {a} 缺少数值/路径")
                sys.exit(2)
            opts[a] = argv[i + 1]
            i += 2
        elif a.startswith("--"):
            opts[a] = True
            i += 1
        else:
            positional.append(a)
            i += 1
    return positional, opts


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)

    argv = sys.argv[1:]
    if "--write-example" in argv:
        args, opts = split_argv([a for a in argv if a != "--write-example"])
        outp = opts.get("--out") or "example_data.json"
        with io.open(outp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(EXAMPLE_DATA, ensure_ascii=False, indent=2))
        print(f"已写出示例 data JSON -> {outp}")
        print("字段口径权威定义见 references/data-schema.json；改内容后重跑本脚本即可出报告。")
        sys.exit(0)

    args, opts = split_argv(argv)
    if not args:
        print(__doc__)
        sys.exit(2)
    in_json = args[0]
    out_html = opts.get("--out") or "script_report.html"
    theme = opts.get("--theme") or "light"
    if theme not in ("light", "dark"):
        print("错误：--theme 只接受 light 或 dark")
        sys.exit(2)
    if not os.path.exists(in_json):
        print(f"错误：找不到输入文件 {in_json}")
        sys.exit(2)
    try:
        data = load_json_file(in_json)
    except Exception as exc:
        print(f"错误：JSON 解析失败 -> {exc}")
        sys.exit(2)

    errors, warnings = validate_data(data)
    for w in warnings:
        print(f"⚠️  字段体检：{w}")
    if errors:
        print("❌ 数据结构不合格，已停止出稿：")
        for e in errors:
            print(f"   - {e}")
        print("   先跑 `python export_html.py --write-example` 拿一份标准样例，再按 references/data-schema.json 填字段。")
        sys.exit(4)

    html_str = build_html(data, theme=theme)
    with io.open(out_html, "w", encoding="utf-8") as fh:
        fh.write(html_str)
    print(f"已生成离线单页 HTML 剧本还原报告 -> {out_html}（主题 {theme}）")
    if warnings:
        print(f"提示：共 {len(warnings)} 条字段体检提醒，报告里对应模块可能为空。")
