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


HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-CN" data-theme="__DEFAULT_THEME__">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="generator" content="short-drama-teardown · export_html.py V4.0.1" />
<meta name="color-scheme" content="light dark" />
<title>__PAGE_TITLE__</title>
<style>
  /* ============ 设计令牌 ============ */
  :root {
    --bg: #0a0e14;
    --bg-2: #0d1320;
    --surface: #121a26;
    --surface-2: #182433;
    --surface-3: #1e2c3d;
    --border: #24334a;
    --border-soft: #1c2740;
    --text: #e9eef7;
    --text-muted: #93a2b8;
    --accent: #8b8cff;
    --accent-2: #38bdf8;
    --accent-soft: rgba(139, 140, 255, 0.16);
    --green: #34d399;
    --amber: #fbbf24;
    --purple: #c084fc;
    --shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 18px 44px -20px rgba(0, 0, 0, 0.75);
    --shadow-soft: 0 1px 2px rgba(0, 0, 0, 0.25);
    --radius: 18px;
    --radius-sm: 12px;
    --radius-xs: 8px;
    --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  [data-theme="light"] {
    --bg: #f3f5f9;
    --bg-2: #eceff5;
    --surface: #ffffff;
    --surface-2: #f6f8fb;
    --surface-3: #eef2f7;
    --border: #e2e8f0;
    --border-soft: #edf1f6;
    --text: #0f1724;
    --text-muted: #5d6b7e;
    --accent: #4f46e5;
    --accent-2: #0ea5e9;
    --accent-soft: rgba(79, 70, 229, 0.10);
    --green: #0b8a5b;
    --amber: #a25a06;
    --purple: #7c3aed;
    --shadow: 0 1px 2px rgba(16, 24, 40, 0.05), 0 18px 40px -22px rgba(16, 24, 40, 0.28);
    --shadow-soft: 0 1px 2px rgba(16, 24, 40, 0.05);
  }

  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    font-family: var(--sans);
    background:
      radial-gradient(1100px 520px at 12% -8%, var(--accent-soft), transparent 62%),
      radial-gradient(900px 460px at 92% -4%, rgba(56, 189, 248, 0.10), transparent 58%),
      var(--bg);
    background-attachment: fixed;
    color: var(--text);
    line-height: 1.72;
    -webkit-font-smoothing: antialiased;
    font-feature-settings: "palt" 1;
  }
  ::selection { background: var(--accent-soft); color: var(--text); }

  .container { max-width: 1180px; margin: 0 auto; padding: 28px 22px 96px; }

  /* ============ 顶部主视觉 ============ */
  .hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(160deg, var(--surface) 0%, var(--surface-2) 100%);
    border: 1px solid var(--border);
    border-radius: calc(var(--radius) + 4px);
    box-shadow: var(--shadow);
    padding: 30px 32px 26px;
    margin-bottom: 18px;
  }
  .hero::before {
    content: "";
    position: absolute; inset: -40% 55% 40% -10%;
    background: radial-gradient(closest-side, var(--accent-soft), transparent 72%);
    pointer-events: none;
  }
  .hero::after {
    content: "";
    position: absolute; right: -6%; top: -55%;
    width: 340px; height: 340px; border-radius: 50%;
    background: radial-gradient(closest-side, rgba(56, 189, 248, 0.14), transparent 70%);
    pointer-events: none;
  }
  .hero-main { position: relative; display: flex; flex-wrap: wrap; gap: 22px; justify-content: space-between; align-items: flex-start; }
  .eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 11.5px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--accent); margin-bottom: 10px;
  }
  .eyebrow::before { content: ""; width: 22px; height: 2px; border-radius: 2px; background: linear-gradient(90deg, var(--accent), var(--accent-2)); }
  .title-wrap h1 {
    margin: 0 0 6px;
    font-size: clamp(22px, 2.5vw, 31px);
    line-height: 1.24;
    font-weight: 800;
    letter-spacing: -0.02em;
  }
  .subtitle { margin: 0 0 14px; color: var(--text-muted); font-size: 13.5px; }

  .meta-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .meta-chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 11px; border-radius: 999px;
    background: var(--surface-3); border: 1px solid var(--border-soft);
    font-size: 12.5px; color: var(--text-muted); white-space: nowrap;
  }
  .meta-chip b { color: var(--text); font-weight: 700; }
  .badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 11px; border-radius: 999px;
    font-size: 12px; font-weight: 700; letter-spacing: 0.01em;
    background: var(--accent-soft); color: var(--accent);
    border: 1px solid transparent;
  }
  .badge.warn { background: rgba(251, 191, 36, 0.14); color: var(--amber); }
  .badge.ok { background: rgba(52, 211, 153, 0.14); color: var(--green); }
  .badge.os { background: rgba(192, 132, 252, 0.16); color: var(--purple); }

  .header-actions { display: flex; gap: 9px; flex-wrap: wrap; position: relative; }
  .btn {
    cursor: pointer; border: 1px solid var(--border);
    background: var(--surface-3); color: var(--text);
    padding: 9px 15px; border-radius: 11px;
    font-size: 13px; font-weight: 600; font-family: inherit;
    transition: transform 0.12s ease, border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
    display: inline-flex; align-items: center; gap: 7px;
  }
  .btn:hover { border-color: var(--accent); background: var(--surface); box-shadow: var(--shadow-soft); transform: translateY(-1px); }
  .btn:active { transform: translateY(0); }
  .btn.primary {
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    color: #fff; border-color: transparent;
    box-shadow: 0 10px 24px -14px var(--accent);
  }
  .btn.primary:hover { color: #fff; filter: brightness(1.06); }
  .btn.copied { background: var(--green); color: #04231a; border-color: transparent; }

  .copyright-note {
    position: relative;
    margin-top: 18px; padding-top: 14px;
    border-top: 1px dashed var(--border);
    font-size: 12px; color: var(--amber); line-height: 1.6;
  }

  /* ============ 悬浮导航 ============ */
  .nav-shell { position: sticky; top: 12px; z-index: 40; margin-bottom: 20px; }
  .toc-bar {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    padding: 9px 12px;
    background: var(--surface);
    background: color-mix(in srgb, var(--surface) 84%, transparent);
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(12px) saturate(1.4);
    -webkit-backdrop-filter: blur(12px) saturate(1.4);
  }
  .toc-label { font-size: 11.5px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-muted); margin: 0 6px 0 4px; }
  .toc-link {
    text-decoration: none; color: var(--text-muted);
    padding: 7px 13px; border-radius: 999px;
    font-size: 13px; font-weight: 600; white-space: nowrap;
    border: 1px solid transparent;
    transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
  }
  .toc-link:hover { color: var(--text); background: var(--surface-3); }
  .toc-link.active { color: var(--accent); background: var(--accent-soft); border-color: color-mix(in srgb, var(--accent) 26%, transparent); }
  .nav-progress {
    height: 2px; margin: 6px 2px 0; border-radius: 2px; overflow: hidden;
    background: transparent;
  }
  .nav-progress span {
    display: block; height: 100%; width: 0%;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    transition: width 0.1s linear;
  }

  /* ============ 卡片与章节 ============ */
  .section-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 26px 28px;
    margin-bottom: 22px;
    box-shadow: var(--shadow);
    scroll-margin-top: 96px;
  }
  .section-head {
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;
    padding-bottom: 14px; margin-bottom: 18px;
    border-bottom: 1px solid var(--border-soft);
  }
  .section-title { display: flex; align-items: center; gap: 12px; }
  .section-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 30px; height: 30px; border-radius: 10px;
    background: linear-gradient(135deg, var(--accent-soft), transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--border));
    color: var(--accent); font-size: 13px; font-weight: 800; font-family: var(--mono);
  }
  .section-head h2 { margin: 0; font-size: 17.5px; font-weight: 750; letter-spacing: -0.01em; }
  .section-desc { width: 100%; margin: -4px 0 0 42px; font-size: 12.5px; color: var(--text-muted); }

  /* ============ 表格 ============ */
  .table-wrap {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
  }
  table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13.5px; }
  thead th {
    position: sticky; top: 0; z-index: 2;
    background: var(--surface-2);
    font-weight: 700; font-size: 12.5px; letter-spacing: 0.02em;
    color: var(--text-muted);
    padding: 12px 14px; text-align: left; white-space: nowrap;
    border-bottom: 1px solid var(--border);
  }
  tbody td { padding: 13px 14px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--border-soft); }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr { transition: background 0.12s ease; }
  tbody tr:nth-child(even) { background: color-mix(in srgb, var(--surface-2) 55%, transparent); }
  tbody tr:hover { background: var(--accent-soft); }
  .cell-name { font-weight: 750; white-space: nowrap; }
  .timecode {
    font-family: var(--mono); font-size: 12px;
    white-space: nowrap; color: var(--text-muted);
    letter-spacing: -0.02em;
  }
  .idx { font-family: var(--mono); font-size: 12px; color: var(--text-muted); }

  /* ============ 人物卡（表格首列头像） ============ */
  .person { display: flex; align-items: center; gap: 10px; min-width: 150px; }
  .avatar {
    flex: 0 0 32px; width: 32px; height: 32px; border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 800;
    background: linear-gradient(135deg, var(--accent-soft), transparent);
    border: 1px solid color-mix(in srgb, var(--accent) 28%, var(--border));
    color: var(--accent);
  }

  /* ============ 剧本 ============ */
  .scene-block {
    position: relative;
    margin-bottom: 26px; padding: 20px 22px 18px 24px;
    background: var(--surface-2);
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-sm);
  }
  .scene-block::before {
    content: ""; position: absolute; left: 0; top: 16px; bottom: 16px; width: 3px;
    border-radius: 3px;
    background: linear-gradient(180deg, var(--accent), var(--accent-2));
  }
  .scene-block:last-child { margin-bottom: 0; }
  .scene-title {
    display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px;
    font-size: 14.5px; font-weight: 750; color: var(--accent);
    margin-bottom: 14px; letter-spacing: 0.01em;
  }
  .scene-title .scene-tag {
    font-family: var(--mono); font-size: 10.5px; font-weight: 700;
    padding: 2px 7px; border-radius: 6px;
    background: var(--accent-soft); color: var(--accent);
  }
  .action-line {
    display: flex; gap: 9px; align-items: flex-start;
    background: var(--surface-3);
    border-left: 3px solid var(--amber);
    padding: 10px 14px; margin: 11px 0;
    border-radius: 0 var(--radius-xs) var(--radius-xs) 0;
    font-size: 13.5px; color: var(--text-muted);
  }
  .action-line .mark { color: var(--amber); font-weight: 800; flex: 0 0 auto; }
  .dialogue-line {
    margin: 12px 0 12px 2px; font-size: 15px; line-height: 1.75;
    padding-left: 14px; border-left: 2px solid transparent;
  }
  .dialogue-line:hover { border-left-color: var(--border); }
  .speaker {
    font-weight: 750; color: var(--green);
    margin-right: 2px;
  }
  .speaker.os { color: var(--purple); }
  .os-tag {
    display: inline-block; vertical-align: 1px;
    font-family: var(--mono); font-size: 10px; font-weight: 700; letter-spacing: 0.04em;
    padding: 1px 6px; border-radius: 5px; margin-left: 6px;
    background: rgba(192, 132, 252, 0.16); color: var(--purple);
  }
  .stage-dir { font-size: 12.5px; color: var(--text-muted); margin-left: 4px; font-style: normal; }
  .dialogue-text { color: var(--text); }

  /* ============ 骨架卡 ============ */
  .formula-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius-sm);
    padding: 16px 18px;
    font-family: var(--mono); font-size: 13px; line-height: 1.8;
    white-space: pre-wrap; margin-bottom: 18px;
    color: var(--text);
  }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 18px; }
  .sub-box {
    background: var(--surface-2);
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-sm);
    padding: 18px 20px;
  }
  .sub-box h3 {
    margin: 0 0 12px; font-size: 14px; font-weight: 750;
    display: flex; align-items: center; gap: 8px;
  }
  .sub-box p { margin: 10px 0; font-size: 13.5px; }
  .sub-box ul { margin: 8px 0 16px; padding-left: 20px; font-size: 13.5px; }
  .sub-box li { margin: 5px 0; }
  .hook-item {
    padding: 10px 0; border-bottom: 1px dashed var(--border-soft);
    font-size: 13.5px;
  }
  .hook-item:last-child { border-bottom: none; }
  .hook-item .ev { display: block; margin-top: 4px; font-size: 12.5px; color: var(--text-muted); }

  /* ============ 逐字稿 ============ */
  .os-speaker { color: var(--purple); }
  .frame-note { font-size: 12.5px; color: var(--text-muted); }

  /* ============ 浮动控件 ============ */
  .fab-top {
    position: fixed; right: 26px; bottom: 26px; z-index: 50;
    width: 44px; height: 44px; border-radius: 14px;
    display: inline-flex; align-items: center; justify-content: center;
    border: 1px solid var(--border); background: var(--surface);
    color: var(--text-muted); box-shadow: var(--shadow); cursor: pointer;
    opacity: 0; transform: translateY(10px); pointer-events: none;
    transition: opacity 0.18s ease, transform 0.18s ease, color 0.15s ease;
    font-size: 16px;
  }
  .fab-top.show { opacity: 1; transform: none; pointer-events: auto; }
  .fab-top:hover { color: var(--accent); border-color: var(--accent); }

  .toast {
    position: fixed; left: 50%; bottom: 28px; z-index: 60;
    transform: translate(-50%, 14px);
    background: var(--surface); color: var(--text);
    border: 1px solid var(--border); border-radius: 999px;
    padding: 10px 18px; font-size: 13px; font-weight: 600;
    box-shadow: var(--shadow); opacity: 0; pointer-events: none;
    transition: opacity 0.18s ease, transform 0.18s ease;
  }
  .toast.show { opacity: 1; transform: translate(-50%, 0); }

  /* ============ 响应式 ============ */
  @media (max-width: 720px) {
    .container { padding: 16px 12px 84px; }
    .hero { padding: 22px 18px; }
    .section-card { padding: 20px 16px; }
    .section-desc { margin-left: 0; }
    .toc-label { display: none; }
    .toc-bar { gap: 6px; padding: 8px; }
    .toc-link { padding: 6px 10px; font-size: 12px; }
    .header-actions { width: 100%; }
    .btn { flex: 1 1 auto; justify-content: center; }
    .dialogue-line { font-size: 14px; }
  }

  @media (prefers-reduced-motion: reduce) {
    html { scroll-behavior: auto; }
    * { transition: none !important; animation: none !important; }
  }

  @media print {
    /* 打印/转 PDF 强制浅色全套变量，避免 dark 主题下「深底 + 继承#000」的黑底黑字 */
    :root, [data-theme="dark"], [data-theme="light"] {
      --bg: #ffffff;
      --surface: #ffffff;
      --surface-2: #f5f7f9;
      --surface-3: #f5f7f9;
      --border: #c9d1d9;
      --border-soft: #dde3ea;
      --text: #111111;
      --text-muted: #4a4a4a;
      --accent: #0b4f9e;
      --accent-2: #0b4f9e;
      --accent-soft: rgba(11, 79, 158, 0.08);
      --green: #0f6b2d;
      --amber: #7a5200;
      --purple: #5b2fc0;
      --shadow: none;
      --shadow-soft: none;
    }
    @page { margin: 14mm 12mm; }
    body {
      background: #fff !important; color: #111 !important;
      background-image: none !important;
    }
    .nav-shell, .header-actions, .btn, .fab-top, .toast { display: none !important; }
    .container { max-width: none; padding: 0; }
    .hero { border: none; padding: 0 0 10px; margin-bottom: 12px; background: #fff !important; }
    .hero::before, .hero::after { display: none !important; }
    .section-card, .scene-block, .sub-box, .formula-box {
      box-shadow: none !important; break-inside: avoid;
    }
    .section-card { border: 1px solid #c9d1d9; padding: 14px 16px; margin-bottom: 14px; }
    .table-wrap { border-color: #c9d1d9 !important; overflow: visible !important; }
    table, th, td { border-color: #c9d1d9 !important; }
    thead th { position: static; background: #f5f7f9 !important; color: #111 !important; }
    tbody tr, tbody tr:nth-child(even), tbody tr:hover { background: #fff !important; }
    th, tr, td { background: #fff !important; color: #111 !important; }
    tr:hover td { background: #fff !important; }
    .action-line { background: #f5f7f9 !important; color: #111 !important; border-left-color: #7a5200 !important; }
    .formula-box, .sub-box { background: #f5f7f9 !important; color: #111 !important; }
    .speaker { color: #0f6b2d !important; }
    .speaker.os { color: #5b2fc0 !important; }
    .scene-title { color: #0b4f9e !important; }
    .scene-block::before { background: #0b4f9e !important; }
    .copyright-note { color: #7a5200 !important; }
    .badge { border: 1px solid #c9d1d9 !important; background: #f5f7f9 !important; color: #111 !important; }
    a { color: #111 !important; text-decoration: none; }
  }
</style>
</head>
<body>
<div class="container">

  <header class="hero">
    <div class="hero-main">
      <div class="title-wrap">
        <div class="eyebrow">Script Teardown Report</div>
        <h1 id="drama-title"></h1>
        <p class="subtitle" id="drama-subtitle"></p>
        <div class="meta-row" id="drama-meta"></div>
      </div>
      <div class="header-actions">
        <button class="btn" type="button" onclick="toggleTheme()" title="切换明暗主题">🌓 明暗切换</button>
        <button class="btn" type="button" onclick="exportCSV()" title="导出逐字稿 CSV">📥 导出 CSV</button>
        <button class="btn primary" type="button" onclick="copyScript(this)" title="复制整集剧本">📋 复制整集剧本</button>
      </div>
    </div>
    <div class="copyright-note">⚠️ 拆解学习用途 · 骨架与结构可迁移 · 原作台词与专有设定不可照搬商用 · 生成器 export_html.py V4.0.1</div>
  </header>

  <div class="nav-shell">
    <nav class="toc-bar" aria-label="章节导航">
      <span class="toc-label">快速定位</span>
      <a class="toc-link" href="#sec-chars" data-target="sec-chars">👤 一、人物锁定</a>
      <a class="toc-link" href="#sec-script" data-target="sec-script">📜 二、还原剧本</a>
      <a class="toc-link" href="#sec-skeleton" data-target="sec-skeleton">🧩 三、骨架分析</a>
      <a class="toc-link" href="#sec-transcript" data-target="sec-transcript">📝 四、逐字逐句</a>
    </nav>
    <div class="nav-progress"><span id="nav-progress-bar"></span></div>
  </div>

  <!-- 一、唯一人物锁定表 -->
  <section id="sec-chars" class="section-card">
    <div class="section-head">
      <div class="section-title">
        <span class="section-num">01</span>
        <h2>全集唯一出场人物视觉与称谓锁定表</h2>
      </div>
      <span class="badge ok" id="chars-count"></span>
      <div class="section-desc">同一张脸换瞳色 / 显本体 / 战损，一律归并为同一角色；全篇只用唯一标准名。</div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>唯一标准角色名</th>
            <th>外貌与服装基线</th>
            <th>同人形态归并（禁拆新角）</th>
            <th>台词称谓证据</th>
            <th>声线特征</th>
          </tr>
        </thead>
        <tbody id="chars-tbody"></tbody>
      </table>
    </div>
  </section>

  <!-- 二、深度还原剧本 -->
  <section id="sec-script" class="section-card">
    <div class="section-head">
      <div class="section-title">
        <span class="section-num">02</span>
        <h2>深度还原剧本</h2>
      </div>
      <button class="btn" type="button" onclick="copyScript(this)">📋 复制整集剧本</button>
      <div class="section-desc">场号 · 日夜内外 · 人物站位 · △ 动作与神态调度 · 对白与 OS/VO 分色标注。</div>
    </div>
    <div id="script-container"></div>
  </section>

  <!-- 三、骨架分析卡 -->
  <section id="sec-skeleton" class="section-card">
    <div class="section-head">
      <div class="section-title">
        <span class="section-num">03</span>
        <h2>骨架分析卡</h2>
      </div>
      <div class="section-desc">结构公式 · 集粒度节拍表 · 钩子与 OS 信息差盘点 · 可迁移与不可迁移。</div>
    </div>
    <div class="formula-box" id="skeleton-formula"></div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>集 / 段</th>
            <th>钩子（秒位 + 手段）</th>
            <th>冲突升级</th>
            <th>反转 / 爽点（含 OS）</th>
            <th>断章钩</th>
            <th>强度</th>
          </tr>
        </thead>
        <tbody id="beats-tbody"></tbody>
      </table>
    </div>
    <div class="grid-2">
      <div class="sub-box">
        <h3>🎣 钩子与画外音（OS / VO）盘点</h3>
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
      <div class="section-title">
        <span class="section-num">04</span>
        <h2>L1+L2 逐句 1:1 画面绑定逐字稿</h2>
      </div>
      <span class="badge" id="transcript-count"></span>
      <div class="section-desc">每句台词按时间码中点绑定该秒画面帧，张嘴 = 现场对白，闭嘴 = OS / 画外。</div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>句号</th>
            <th>时间码</th>
            <th>台词（正字校对后）</th>
            <th>唯一说话人 &amp; 属性</th>
            <th>该秒画面实录与嘴型核验</th>
          </tr>
        </thead>
        <tbody id="transcript-tbody"></tbody>
      </table>
    </div>
  </section>

</div>

<button class="fab-top" id="fab-top" type="button" title="回到顶部" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</button>
<div class="toast" id="toast"></div>

<script>
const DATA = __JSON_DATA__;

/* ---------- 工具 ---------- */
function esc(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => t.classList.remove('show'), 1800);
}

function copyText(text, btn) {
  const done = () => {
    if (btn) {
      const old = btn.innerHTML;
      btn.classList.add('copied');
      btn.innerHTML = '✅ 已复制';
      setTimeout(() => { btn.classList.remove('copied'); btn.innerHTML = old; }, 1400);
    }
    showToast('已复制到剪贴板');
  };
  const fallback = () => {
    // clipboard API 在 file:// / 非安全上下文 / 部分浏览器会被拒，退回 execCommand
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
    alert('当前浏览器阻止了自动复制：请手动全选剧本区内容复制。');
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

/* ---------- 头部 ---------- */
function initHeader() {
  const m = DATA.meta || {};
  const title = m.title || '未命名短剧';
  const ep = m.episode || 'EP01';
  document.getElementById('drama-title').textContent = title + ' · ' + ep;
  document.getElementById('drama-subtitle').textContent = '剧本深度还原报告 · 逐字稿 / 还原剧本 / 骨架分析 / 画面绑定';

  const scenes = DATA.script_scenes || [];
  const chars = DATA.characters || [];
  const trans = DATA.transcript || [];
  document.title = title + ' · ' + ep + ' — 剧本深度还原报告';

  const pills = [];
  if (m.channel) pills.push('<span class="badge">' + esc(m.channel) + '</span>');
  if (m.duration) pills.push('<span class="meta-chip">⏱️ 总时长 <b>' + esc(m.duration) + '</b></span>');
  pills.push('<span class="meta-chip">🎭 场次 <b>' + scenes.length + '</b></span>');
  pills.push('<span class="meta-chip">👤 人物 <b>' + chars.length + '</b></span>');
  pills.push('<span class="meta-chip">💬 台词 <b>' + trans.length + '</b> 句</span>');
  if (m.date) pills.push('<span class="meta-chip">📅 ' + esc(m.date) + '</span>');
  document.getElementById('drama-meta').innerHTML = pills.join('');

  const cc = document.getElementById('chars-count');
  if (cc) cc.textContent = '已锁定 ' + chars.length + ' 人';
  const tc = document.getElementById('transcript-count');
  if (tc) tc.textContent = '共 ' + trans.length + ' 句';
}

/* ---------- CSV ---------- */
function exportCSV() {
  const headers = ['句号', '时间码', '台词', '唯一说话人及属性', '画面实录与嘴型核验'];
  const rows = (DATA.transcript || []).map(t => [t.index, t.timecode, t.text, t.speaker, t.frame_note]
    .map(v => '"' + String(v || '').replace(/"/g, '""') + '"').join(','));
  const csv = '\uFEFF' + headers.join(',') + '\n' + rows.join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = ((DATA.meta && DATA.meta.title) || 'script_teardown') + '_transcript.csv';
  a.click();
  URL.revokeObjectURL(url);
  showToast('CSV 已导出');
}

/* ---------- 剧本 ---------- */
function renderScript() {
  const scenes = DATA.script_scenes || [];
  const box = document.getElementById('script-container');
  if (!scenes.length) {
    box.innerHTML = '<p style="color:var(--text-muted);">暂无剧本内容。</p>';
    return;
  }
  box.innerHTML = scenes.map((sc, i) => {
    const blocks = (sc.blocks || []).map(b => {
      if (b.type === 'action') {
        return '<div class="action-line"><span class="mark">△</span><span>' + esc(b.text) + '</span></div>';
      }
      const spk = b.speaker || '';
      const isOS = spk.indexOf('OS') >= 0 || spk.indexOf('VO') >= 0 || spk.indexOf('画外') >= 0;
      const tag = isOS ? '<span class="os-tag">OS</span>' : '';
      const dir = b.direction ? '<span class="stage-dir">（' + esc(b.direction) + '）</span>' : '';
      return '<div class="dialogue-line"><span class="speaker' + (isOS ? ' os' : '') + '">' +
        esc(spk) + '</span>' + tag + dir + '：<span class="dialogue-text">' + esc(b.text) + '</span></div>';
    }).join('');
    return '<div class="scene-block"><div class="scene-title"><span class="scene-tag">SCENE ' +
      String(i + 1).padStart(2, '0') + '</span><span>' + esc(sc.header) + '</span></div>' + blocks + '</div>';
  }).join('');
}

function copyScript(btn) {
  const txt = (DATA.script_scenes || []).map(sc => {
    const lines = [sc.header];
    (sc.blocks || []).forEach(b => {
      if (b.type === 'action') lines.push('△ ' + b.text);
      else lines.push((b.speaker || '') + (b.direction ? '（' + b.direction + '）' : '') + '：' + b.text);
    });
    return lines.join('\n');
  }).join('\n\n');
  if (!txt.trim()) { showToast('暂无可复制的剧本内容'); return; }
  copyText(txt, btn);
}

/* ---------- 骨架 ---------- */
function renderSkeleton() {
  const sk = DATA.skeleton || {};
  document.getElementById('skeleton-formula').textContent = sk.formula || '暂无结构公式';

  const beats = sk.beats || [];
  const tb = document.getElementById('beats-tbody');
  tb.innerHTML = beats.length ? beats.map((b, i) => (
    '<tr><td class="cell-name">' + esc(b.unit) + '</td>' +
    '<td>' + esc(b.hook) + '</td>' +
    '<td>' + esc(b.escalation) + '</td>' +
    '<td>' + esc(b.twist) + '</td>' +
    '<td>' + esc(b.cliffhanger) + '</td>' +
    '<td><span class="badge">' + esc(b.intensity) + '</span></td></tr>'
  )).join('') : '<tr><td colspan="6" style="color:var(--text-muted);">暂无节拍数据</td></tr>';

  const hooks = sk.hooks || [];
  document.getElementById('hooks-list').innerHTML = hooks.length ? hooks.map(h => (
    '<div class="hook-item"><b>' + esc(h.type) + '</b>：' + esc(h.method) +
    '<span class="ev">原样证据：' + esc(h.evidence) + '</span></div>'
  )).join('') : '<p style="color:var(--text-muted);">暂无</p>';

  const tr = sk.transferable || [];
  const nt = sk.non_transferable || [];
  document.getElementById('transfer-list').innerHTML =
    '<p><span class="badge ok">可迁移骨架</span></p>' +
    '<ul>' + tr.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul>' +
    '<p><span class="badge warn">不可迁移表达</span></p>' +
    '<ul>' + nt.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul>';
}

/* ---------- 人物 + 逐字稿 ---------- */
function initialOf(name) {
  const clean = String(name || '?').replace(/[（(].*?[)）]/g, '').trim();
  return clean ? clean.charAt(0) : '?';
}

function renderCharactersAndTranscript() {
  const chars = DATA.characters || [];
  document.getElementById('chars-tbody').innerHTML = chars.length ? chars.map(c => (
    '<tr>' +
    '<td><div class="person"><span class="avatar">' + esc(initialOf(c.name)) + '</span>' +
    '<span class="cell-name">' + esc(c.name) + '</span></div></td>' +
    '<td>' + esc(c.appearance) + '</td>' +
    '<td>' + esc(c.variants) + '</td>' +
    '<td>' + esc(c.evidence) + '</td>' +
    '<td>' + esc(c.voice) + '</td></tr>'
  )).join('') : '<tr><td colspan="5" style="color:var(--text-muted);">暂无人物档案</td></tr>';

  const trans = DATA.transcript || [];
  document.getElementById('transcript-tbody').innerHTML = trans.length ? trans.map(t => {
    const spk = t.speaker || '';
    const isOS = spk.indexOf('OS') >= 0 || spk.indexOf('VO') >= 0 || spk.indexOf('画外') >= 0;
    const tag = isOS ? '<span class="os-tag">OS</span>' : '';
    return '<tr>' +
      '<td class="idx">' + esc(t.index) + '</td>' +
      '<td class="timecode">' + esc(t.timecode) + '</td>' +
      '<td>' + esc(t.text) + '</td>' +
      '<td><b class="' + (isOS ? 'os-speaker' : '') + '">' + esc(spk) + '</b>' + tag + '</td>' +
      '<td class="frame-note">' + esc(t.frame_note) + '</td></tr>';
  }).join('') : '<tr><td colspan="5" style="color:var(--text-muted);">暂无逐句数据</td></tr>';
}

/* ---------- 交互：滚动进度 / 目录高亮 / 回顶 ---------- */
function initScrollUI() {
  const bar = document.getElementById('nav-progress-bar');
  const fab = document.getElementById('fab-top');
  const links = Array.prototype.slice.call(document.querySelectorAll('.toc-link'));
  const sections = links.map(l => document.getElementById(l.getAttribute('data-target'))).filter(Boolean);

  function onScroll() {
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    const pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
    if (bar) bar.style.width = pct.toFixed(2) + '%';
    if (fab) fab.classList.toggle('show', doc.scrollTop > 420);

    let current = null;
    const probe = window.scrollY + 140;
    sections.forEach(sec => { if (sec.offsetTop <= probe) current = sec.id; });
    links.forEach(l => l.classList.toggle('active', l.getAttribute('data-target') === current));
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();
}

initHeader();
renderScript();
renderSkeleton();
renderCharactersAndTranscript();
initScrollUI();
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
