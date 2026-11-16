# 短剧扒剧本 · 深度还原 Skill（short-drama-teardown）

**版本：V4.0.1** ｜ 上一版：V4.0（2026-11-16 修复版，详见 `CHANGELOG.md`）

把爆款短剧从成片视频逆向还原成剧本，四步出四件交付物：

1. 《扒剧逐字稿》——逐句时间码 + 1:1 绑定画面 + 说话人/OS 属性
2. 《深度还原剧本》——标准影视级剧本（场号 / △动作调度 / 对白 / OS-VO）
3. 《骨架分析卡》——节拍表 / 卡点矩阵 / 钩子盘点 / 可迁移 vs 不可迁移
4. 《离线单页 HTML 报告 + CSV》——单文件、零依赖、可打印可转 PDF（V4.0.1 界面精修：渐变 Hero、悬浮胶囊目录 + 阅读进度、章节编号徽标、人物头像列、OS 徽章、Toast 反馈、回到顶部）

> 产物仅供拆解学习与结构研究；台词含原作内容，**不可照搬商用**。

## 一、三条命令跑通全流程

```bash
# 0) 环境自检（三条 selftest 必须全 OK）
python scripts/batch_prep.py --selftest
python scripts/srt_to_script.py --selftest
python scripts/export_html.py --selftest

# 1) 字幕 -> L1 逐字稿（默认不合并，防吞句）
python scripts/srt_to_script.py ep01.srt --merge 0 --gap-warn 3.5 --glossary "付寒周=傅寒州" --out ep01_L1.md

# 2) 逐句台词中点 1:1 抽帧（通道 B 命门；有 ❌ 就重抽，别凭记忆补）
python scripts/batch_prep.py --bind-frames ep01.mp4 ep01.srt --out-dir ./line_frames
#    单独重抽某一句的画面
python scripts/batch_prep.py --grab-frame ep01.mp4 --time 12.5 --out f_12.5.jpg

# 3) 汇总 JSON -> 离线单页 HTML 报告
python scripts/export_html.py --write-example --out data.json   # 先拿标准样例
python scripts/export_html.py data.json --out 侯门嫁状元_EP03_剧本还原报告.html
```

## 二、文件清单

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 总控：进场双通道门禁、三把铁锁、四段式交付、工具链、抽样规则、版权红线 |
| `README.md` | 本文件：快速开始 / 文件清单 / 边界 / 常见坑 |
| `CHANGELOG.md` | V2.2 → V4.0 → V4.0.1 变更与修复逐条记录 |
| `CHECKLIST.md` | 交付前自检清单（发布与交付都按它过一遍） |
| `scripts/srt_to_script.py` | SRT/VTT/BCC/剪映草稿 JSON → L1 逐字稿（去重/断层预警/正字纠偏/OS 初标） |
| `scripts/batch_prep.py` | 批量抽 16k 音轨 / 逐句中点 1:1 抽帧 / 裁 4fps 字幕带 |
| `scripts/export_html.py` | 结构化 JSON → 离线单页 HTML 报告；含字段体检与 `--write-example` |
| `references/teardown-script-template.md` | 《扒剧逐字稿》权威模板（含人物锁定表、正字表、人工听打补录） |
| `references/script-restoration-template.md` | 《深度还原剧本》权威模板（含五条交付纪律） |
| `references/skeleton-card-template.md` | 《骨架分析卡》权威模板 |
| `references/data-schema.json` | HTML 报告的 **JSON 字段契约**（唯一权威口径） |

## 三、怎么选通道（先判这一刀，再动手）

- **通道 A（发链接）**：有 URL 或剧名+链接。先抓页面标题/简介建预备角色名册，优先 `yt-dlp --write-subs` 只拉字幕；无字幕则下载转通道 B。
- **通道 B（直接发视频）**：裸片无字无名。必须走三把铁锁：同人归并建唯一人物卡 → 称谓反向锁名 → 逐句中点 1:1 绑画面。
- **兜底（人工听打）**：无音轨/方言过重，按逐字稿模板第三节补录，时间码取整 0.5s。
- **不在本包范围**：只给剧名让助手去互联网找片的「找剧」活；二创改写与商用成稿。

## 四、常见坑（都是踩过的）

| 现象 | 原因 | 处理 |
|---|---|---|
| HTML 报告四块全白 | JSON 字段名写错，脚本直取不到 | 跑 `--write-example` 拿样例，或对照 `references/data-schema.json`；出稿前脚本会打 `⚠️ 字段体检` |
| 抽帧表里有 ❌ | 该句时间码超出片长 / ffmpeg 异常 | `--grab-frame` 定点重抽；脚本退出码 3 就是提醒这事 |
| 一句被拆成两句 / 两句被合成一句 | ASR 碎句或 `--merge` 用大了 | 默认 `--merge 0`；确需合并用 `--merge 1.0`，脚本会做三重校验并给被并句打 `⤵` 留痕 |
| 时间码比原片早 1 秒 | 旧版毫秒取整溢出（V4.0 已修） | 升级到 V4.0.1 |
| 打印/PDF 黑底黑字 | 旧版 print 样式未重置深色变量（V4.0 已修） | 升级到 V4.0.1；报告默认浅色，`--theme dark` 只是屏显 |
| 复制按钮点了没反应 | 浏览器拒绝 clipboard（file:// 等） | V4.0.1 已加 `execCommand` 降级 + 提示 |

## 五、版本口径

包内所有文件的版本串统一为 **V4.0.1**。若在文件里看到 V3.x / V4.0 字样，那是历史变更描述（`CHANGELOG.md` 里的记录），不是现行口径。

## English (short)

**short-drama-teardown V4.0.1** turns a finished short-drama episode into four assets: a per-line transcript bound 1:1 to video frames, a production screenplay, a skeleton card, and an offline single-page HTML report.

Quick start: run the three `--selftest` scripts, convert subtitles with `srt_to_script.py`, bind frames with `batch_prep.py --bind-frames`, then render the report with `export_html.py data.json --out report.html` (use `--write-example` to get a canonical JSON). Field contract: `references/data-schema.json`.

The three identity locks (same-person merge, address-term naming, per-line frame binding) require a **vision-capable model** — see the vision gate in `SKILL.md` §一·0.

