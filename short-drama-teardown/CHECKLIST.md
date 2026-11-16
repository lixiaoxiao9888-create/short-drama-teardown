# CHECKLIST · V4.0.1 发布与交付自检

两条用法：**A. 发包前**（改完代码要发版时过一遍）；**B. 每次交付前**（给客户出报告前过一遍）。

## A. 发包前（发布自检）

- [ ] `python scripts/srt_to_script.py --selftest` → `selftest OK`
- [ ] `python scripts/batch_prep.py --selftest` → `selftest OK (ffmpeg available: True)`
- [ ] `python scripts/export_html.py --selftest` → `selftest OK`
- [ ] 版本串全包一致：`grep -rn "4\.0\.1" .` 至少命中 SKILL.md / README / CHANGELOG / 三个脚本 / 三份模板；`grep -rn "V3\.\|4\.0\.0"` 只应命中 CHANGELOG 里的历史描述
- [ ] `references/data-schema.json` 能被 `json.load` 解析（`python -c "import json;json.load(open('references/data-schema.json',encoding='utf-8'))"`）
- [ ] SKILL.md 的 `file_names` 与实际文件名逐条对得上（新增/删除文件后必须同步）
- [ ] 端到端冒烟：`--write-example` → 改内容 → `export_html.py` 出 HTML → 浏览器打得开、四块都有内容
- [ ] 坏数据回归：`{"transcript":[],"script_scenes":[]}` 必须 exit 4 且不出文件
- [ ] 打印回归：浏览器打印预览里 `△` 动作行是浅底黑字，不是黑底黑字
- [ ] CHANGELOG 本次改动逐条写清（P0/P1/P2 分级）
- [ ] README 的「常见坑」表同步本次改动

## B. 每次交付前（出报告自检）

**进场与人物**
- [ ] 已显式声明进场通道（通道 A / 通道 B），裸视频未跳过三把铁锁
- [ ] 《唯一人物视觉与称谓锁定表》已建，同人形态（瞳色/本体/战损）已归并，未出现「灰衣女子」类代称
- [ ] 全篇角色名严格取自锁定表，无临时改名

**逐字稿**
- [ ] 抽帧索引表无 `❌ 未抽到帧`；若有，已 `--grab-frame` 重抽并复核
- [ ] 断句与碎句：`--merge 0` 跑过；需合并处有 `⤵` 留痕，无跨说话人吞并
- [ ] 时间断层（≥3.5s）逐条核过，是打斗/空镜还是漏句，已在 `△` 动作行写清
- [ ] 同音正字表已应用，纠偏留痕（`原字幕：xx`）
- [ ] OS / VO / 画外 四维判定逐个落到位；闭嘴特写才算 OS，独处张嘴自语按对白

**剧本与骨架**
- [ ] 场头齐（场号 / 日夜内外 / 起止秒 / 人物）
- [ ] 每条 `△` 都有可见动作或调度，不留空场
- [ ] 骨架卡「本集性质」三档标签正确，抽样集未被当成结论依据
- [ ] 「结论只认头部全量」：抽样与头部冲突时已注明

**HTML 报告**
- [ ] 出稿时字段体检无 `⚠️`，或逐条确认可接受
- [ ] 四块内容都有数据（人物 / 剧本 / 骨架 / 逐字稿）
- [ ] CSV 导出中文不乱码（带 BOM）
- [ ] 一键复制整集剧本可用（不可用时应有明确提示，不静默）
- [ ] 顶部版权声明在：「拆解学习用途 · 骨架与结构可迁移 · 原作台词不可照搬」
- [ ] 文件命名：`剧名_集号_剧本还原报告.html`，与交付说明一致
