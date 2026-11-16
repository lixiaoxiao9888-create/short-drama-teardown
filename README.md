<div align="center">

# 🔍 扒剧引擎 · Short-Drama Teardown

## **V4.0.1 交付封装版**

> 把爆款短剧，从成片视频逆向还原成逐字稿 → 标准剧本 → 骨架分析卡 → 离线单页 HTML 报告
> 给 AI 助手 / LLM 直接调用的「扒剧」技能包

**中文** | [English](README.en.md)

![Version](https://img.shields.io/badge/版本-V4.0.1-6a5acd)
![Gate](https://img.shields.io/badge/门禁-双通道硬分流-00b4d8)
![Locks](https://img.shields.io/badge/防乱人-三把铁锁-2ec4b6)
![Report](https://img.shields.io/badge/交付-离线单页%20HTML-2b9348)
![Scripts](https://img.shields.io/badge/脚本-3%20个自检通过-ff6b6b)
![License](https://img.shields.io/badge/License-MIT-ffca3a)
![Stars](https://img.shields.io/github/stars/lixiaoxiao9888-create/short-drama-teardown?style=social)

---

### 🎬 生产管线

```
进场门禁（发链接 / 发视频） → 人物唯一化锁定 → 逐句 1:1 绑画面 → 逐字稿 → 还原剧本 → 骨架分析 → 离线 HTML 报告
```

</div>

---

## 🧭 这是什么

一套 **给 AI 助手执行的「扒剧」规则库**（OpenClaw Skill / Agent 技能包）：把一部成片短剧反向拆解为四层可用资产——**逐字稿、标准剧本、骨架分析卡、离线单页 HTML 报告**。

不是简单转写：它先解决「谁在说话、这个人到底是谁」这两个裸视频拆解的头号难题，再谈还原与交付。

核心解决四件事：

1. **不乱人** —— 同一张脸换瞳色 / 显九尾 / 战损，绝不拆成多个角色；台词称谓反向锁定唯一真名；
2. **不乱句** —— 每句台词按时间码中点 1:1 绑定画面，看嘴型开合判定「对白 vs OS」，杜绝隔十几秒稀疏抽帧瞎猜；
3. **不漏字** —— 防漏字双轨提取 + 时间断层预警 + 同音错字三级纠偏；抽帧失败当场报警（退出码 3），不静默糊过去；
4. **能交付** —— 四块成果汇总为一份结构化 JSON（字段契约唯一权威），一键出**离线单页滚动 HTML**：锚点导航、复制整集、导出 CSV、打印/转 PDF 强制浅色。

## 🎯 适用场景

- **爆款短剧拆解 / 拉片**：逐字稿 + 剧本 + 骨架 + HTML 一次交付
- **对标学习**：提炼集粒度节拍表、跨集卡点矩阵、钩子轮换与可迁移公式
- **无字幕裸视频逆向**：直接发 `.mp4/.mov` 也能锁定人物与说话人
- **多集批量**：剪映字幕工程 / 本地 ASR / 声纹聚类三条批量链路
- **IP 改编前研究**：先扒骨架，再决定迁移什么、不迁移什么

## 🔥 核心能力

### 〇、进场双通道门禁锁（开工第一铁律）

| 进场通道 | 识别特征 | 核心风险 | 强制执行锁 |
|---|---|---|---|
| **通道 A：发链接** | 抖音 / 快手 / 红果等 URL 或剧名检索 | 链接失效、需登录、无外挂字幕 | 先抓页面标题 / 简介 / 角色表建立《预设角色名册》；优先 `yt-dlp --write-subs` 只拉字幕，无字幕转通道 B |
| **通道 B：直接发视频** | 用户直接上传 `.mp4/.mov` | **无角色名、说话人易张冠李戴、一人裂变成多人** | **严禁跨句稀疏抽帧猜人**，强制启动「裸视频防乱人三把铁锁」 |

> 未收到素材时，先问清通道再开工：**A. 发链接** 还是 **B. 直接发视频文件**。

### 〇·1 视觉能力门禁（V4.0.1 补）

三把铁锁靠「真看画面」：同人归并看脸与服装，逐句三看看主体 / 嘴唇开合 / 神态。开工前先 `read` 一张帧自检——模型不支持图像输入时，**禁止靠台词语义推测说话人与 OS/VO**，必须切支持 `text+image` 的模型，或转人工看图填列，两者都不通就停住，不出半截稿。

### 一、裸视频防乱人三把铁锁

1. **同人归并锁** —— 先通览全片建《出场人物唯一视觉档案》。同脸同主体服装下，瞳色 / 法相变化、本体特效显露（如九尾）、战损妆造微调，**100% 是同一角色**，严禁拆名；同框多角色必须分别建档。人物卡的视觉锚点必须来自**实际读过的帧**。
2. **称谓反向锁名锁** —— 扫描全集称呼词（直呼其名 / 尊称 / 骂名），结合画面朝向锁定唯一标准名；一旦锁定，全篇统一使用，**禁用「灰衣女子」「金眼女子」等临时外貌代称**。
3. **逐句 1:1 画面嘴型硬绑定锁** —— `batch_prep.py --bind-frames` 在每句台词中点 `(start+end)/2` 抽 1 帧，逐句三看：看画面主体、看嘴唇开合（对白 vs OS）、看声线与混响。抽帧失败的句子在索引表标 `❌ 未抽到帧` 并以退出码 3 报警，严禁凭记忆补画面。

### 二、防漏字双轨提取

- 严禁低帧率稀疏抽帧认字；
- 默认 `--merge 0` 不吞句；开 `--merge N` 时才允许拼接，且必须过「续句标点 / 碎片长度 ≤12 字 / 非换人非 OS」三重校验，单次合并链封顶 2 句，被并句在备注打 `⤵` 留痕；
- `--gap-warn 3.5` 自动预警时间断层，纯动作段用 `△` 如实补写。

### 三、画外音（OS / VO）四维推导引擎

| 维度 | 判定铁律 | 剧本标注 |
|---|---|---|
| 画面嘴型闭嘴 | 角色特写、嘴唇紧闭但响起其声音 | `角色名（OS）` |
| 对话流零回应 | 揭底 / 挑衅台词，对手毫无反应 | `角色名（OS）` |
| 张嘴自语 vs 内心 | 独处时嘴唇明显张合 = 现场自语，不标 OS | 张嘴=`角色名`；闭嘴=`（OS）` |
| 镜头拍听众 / 远景 | 声音在当前时空发生，镜头拍听众或远景 | `角色名（画外）` |

### 四、四段式交付（V4.0 起）

| 阶段 | 产物 | 说明 |
|---|---|---|
| 阶段一 | **《扒剧逐字稿》** | 唯一人物视觉与称谓锁定表 + 逐句时间码 / 1:1 画面帧 / 说话人 / OS·VO 属性 |
| 阶段二 | **《深度还原剧本》** | 标准影视级短剧剧本：场号、日夜内外、站位、`△` 动作神态、对白与 OS 区分、同音净稿 |
| 阶段三 | **《骨架分析卡》** | 集粒度节拍表、跨集卡点矩阵、钩子轮换、OS 信息差用法、可迁移公式 |
| 阶段四 | **《离线单页 HTML 报告 & CSV》** | 结构化 JSON → 一键封装；字段契约见 `references/data-schema.json`，出稿前自动字段体检 |

## 🖥 报告界面（V4.0.1 精修）

- **主视觉**：渐变 Hero + 元信息胶囊（通道 / 时长 / 场次 / 人物 / 句数 / 日期），首屏即见全片规模；
- **导航**：悬浮胶囊目录 + 顶部阅读进度条 + 当前章节高亮，长剧本不迷路；
- **段落**：章节编号徽标、场景卡左侧渐变色条、`SCENE 01` 标签、动作行 `△` 高亮；
- **人物**：首列头像块（取角色首字），一眼锁人；
- **台词**：说话人与 OS 分色 + `OS` 小徽章，闭嘴独白 vs 现场对白一眼分辨；
- **表格**：斑马纹 + 悬停高亮 + 表头吸顶，逐字稿拉长照样好读；
- **交互**：复制 / CSV 导出均有 Toast 反馈，右下角回到顶部，明暗一键切换；
- **打印**：强制浅色、隐藏操作栏、避免跨页断卡，直接打印或转 PDF 就是交付稿；
- **零依赖**：单文件、无外链、无网络字体，断网双击即开。

## 🧰 脚本工具

| 脚本 | 用途 | 核心命令 |
|---|---|---|
| `batch_prep.py` | ① 批量抽 16kHz 极轻音轨 ② **逐句时间码中点 1:1 抽帧绑定**（失败即报警，退出码 3） ③ 裁剪 4FPS 底部字幕带 | `python scripts/batch_prep.py --bind-frames ep01.mp4 ep01.srt`<br>`python scripts/batch_prep.py --audio-dir ./videos` |
| `srt_to_script.py` | SRT / VTT / 剪映 `draft_content.json` → L1 逐字稿（不盲拼吞句 + 断层预警 + 同音词纠偏 + OS 初标） | `python scripts/srt_to_script.py ep01.srt --merge 0 --gap-warn 3.5 --glossary "错词=正词"` |
| `export_html.py` | JSON → **离线单页滚动 HTML 报告**（锚点导航 / 复制整集 / CSV 导出 / 打印强制浅色）；`--write-example` 产出标准样例 | `python scripts/export_html.py data.json --out report.html`<br>`python scripts/export_html.py --write-example` |

三个脚本均内置 `--selftest`（含 BOM 兼容回归断言），已验证通过（本机 ffmpeg 可用）。

## ⚙️ 快速开始

```bash
# 安装到 OpenClaw
openclaw skills install ./short-drama-teardown --as short-drama-teardown

# 自检（三个都要过，缺啥装啥）
python short-drama-teardown/scripts/batch_prep.py --selftest
python short-drama-teardown/scripts/srt_to_script.py --selftest
python short-drama-teardown/scripts/export_html.py --selftest

# 通道 B 核心：逐句台词中点抽帧绑定
python short-drama-teardown/scripts/batch_prep.py --bind-frames ep01.mp4 ep01.srt

# 字幕 → 逐字稿
python short-drama-teardown/scripts/srt_to_script.py ep01.srt --merge 0 --gap-warn 3.5

# 逐字稿 → 结构化 JSON → 离线 HTML 报告
python short-drama-teardown/scripts/export_html.py --write-example --out data.json   # 先拿标准样例
python short-drama-teardown/scripts/export_html.py data.json --out report.html
```

**给 AI 助手的最小执行序列**：读 `SKILL.md` → 锁定进场通道（A/B）→ 确认模型能看图 → 通道 B 先建唯一人物档案 → 逐句绑定画面与嘴型 → 交付逐字稿 → 还原剧本 → 骨架分析卡 → JSON → HTML 报告。

### 🧮 常用指令

`扒剧` · `扒剧本` · `扒一下这部短剧` · `拆解爆款` · `拉片` · `逐字稿` · `还原剧本` · `骨架分析` · `生成拉片HTML` · `剧本还原报告`

## 📦 项目结构

```text
short-drama-teardown/
├── SKILL.md                          # 总控：视觉门禁 + 双通道 + 三把铁锁 + 四段交付
├── README.md / CHANGELOG.md / CHECKLIST.md
├── references/
│   ├── data-schema.json              # HTML 报告的 JSON 字段契约（唯一权威）
│   ├── teardown-script-template.md   # 阶段一《扒剧逐字稿》模板（含唯一人物锁定表）
│   ├── script-restoration-template.md# 阶段二《扒剧还原剧本》模板
│   └── skeleton-card-template.md     # 阶段三《骨架分析卡》模板
└── scripts/
    ├── batch_prep.py                 # 音轨提取 / 逐句中点抽帧 / 字幕带裁剪
    ├── srt_to_script.py              # SRT/VTT/剪映 → L1 逐字稿 + 纠偏 + OS 初标
    └── export_html.py                # JSON → 离线单页滚动 HTML 报告
```

## 🗓 更新历史

- **V4.0.1（2026-11-16）** —— 交付封装版修复：补 JSON 字段契约 `data-schema.json` + 出稿前字段体检（退出码 4）；抽帧失败不再静默（退出码 3）；`--merge` 换人判定三重校验 + 合并链封顶 2 句；毫秒进位、OS 统计口径、打印浅色三处修复；同版补丁：BOM 兼容（`utf-8-sig`）、视觉能力门禁、报告界面精修（Hero / 悬浮导航 / 进度条 / 头像列 / OS 徽章 / Toast / 回到顶部）+ [English README](README.en.md)。
- **V4.0（2026-11-16）** —— 新增 `batch_prep.py`（抽音轨 / 逐句中点抽帧 / 字幕带裁剪）与 `export_html.py`（离线单页 HTML + CSV 导出）；进场判定收窄为双通道，新增裸视频防乱人三把铁锁与 OS/VO 四维推导。
- **V3.1（2026-10-19）** —— 双通道门禁锁 + 三把铁锁首个公开版。

## 🛡️ 版权与用途红线

- 产物仅限**拆解学习、结构研究**；
- 逐字稿与还原剧本含原作台词，**禁止直接照搬商用**；
- 每次交付首行注明：「拆解学习用途 · 骨架可迁移 · 台词不可照搬」。

---

<div align="center">

## 📄 License

**MIT** · 拆解学习用途 · 骨架可迁移 · 台词不可照搬

</div>
