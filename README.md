<div align="center">

# 🔍 扒剧引擎 · Short-Drama Teardown

## **V3.1 双通道门禁版**

> 把爆款短剧，从成片视频逆向还原成逐字稿 → 标准剧本 → 骨架分析卡
> 给 AI 助手 / LLM 直接调用的「扒剧」技能包

![Version](https://img.shields.io/badge/版本-V3.1-6a5acd)
![Gate](https://img.shields.io/badge/门禁-双通道硬分流-00b4d8)
![Locks](https://img.shields.io/badge/防乱人-三把铁锁-2ec4b6)
![OS](https://img.shields.io/badge/画外音-OS%2FVO%20四维推导-9d4edd)
![Scripts](https://img.shields.io/badge/脚本-2%20个自检通过-ff6b6b)
![License](https://img.shields.io/badge/License-MIT-ffca3a)
![Stars](https://img.shields.io/github/stars/lixiaoxiao9888-create/short-drama-teardown?style=social)

---

### 🎬 生产管线

```
进场门禁（发链接 / 发视频） → 人物唯一化锁定 → 逐句 1:1 绑画面 → 逐字稿 → 还原剧本 → 骨架分析
```

</div>

---

## 🧭 这是什么

一套 **给 AI 助手执行的「扒剧」规则库**（OpenClaw Skill / Agent 技能包）：把一部成片短剧反向拆解为三层可用资产——**逐字稿、标准剧本、骨架分析卡**。

不是简单转写：它先解决「谁在说话、这个人到底是谁」这两个裸视频拆解的头号难题，再谈还原。

核心解决三件事：

1. **不乱人** —— 同一张脸换瞳色 / 显九尾 / 战损，绝不拆成多个角色；台词称谓反向锁定唯一真名；
2. **不乱句** —— 每句台词按时间码中点 1:1 绑定画面，看嘴型开合判定「对白 vs OS」，杜绝隔十几秒稀疏抽帧瞎猜；
3. **不漏字** —— 防漏字双轨提取 + 时间断层预警 + 同音错字三级纠偏。

## 🎯 适用场景

- **爆款短剧拆解 / 拉片**：逐字稿 + 剧本 + 骨架一次交付
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

### 一、裸视频防乱人三把铁锁（V3.1 核心升级）

1. **同人归并锁** —— 先通览全片建《出场人物唯一视觉档案》。同脸同主体服装下，瞳色 / 法相变化、本体特效显露（如九尾）、战损妆造微调，**100% 是同一角色**，严禁拆名；同框多角色必须分别建档。
2. **称谓反向锁名锁** —— 扫描全集称呼词（直呼其名 / 尊称 / 骂名），结合画面朝向锁定唯一标准名；一旦锁定，全篇统一使用，**禁用「灰衣女子」「金眼女子」等临时外貌代称**。
3. **逐句 1:1 画面嘴型硬绑定锁** —— `batch_prep.py --bind-frames` 在每句台词中点 `(start+end)/2` 抽 1 帧，逐句三看：看画面主体、看嘴唇开合（对白 vs OS）、看声线与混响。

### 二、防漏字双轨提取

- 严禁低帧率稀疏抽帧认字；
- 默认 `--merge 0` 不吞句，但对 ASR 拆碎的同一口气做同人连贯还原；
- `--gap-warn 3.5` 自动预警时间断层，纯动作段用 `△` 如实补写。

### 三、画外音（OS / VO）四维推导引擎

| 维度 | 判定铁律 | 剧本标注 |
|---|---|---|
| 画面嘴型闭嘴 | 角色特写、嘴唇紧闭但响起其声音 | `角色名（OS）` |
| 对话流零回应 | 揭底 / 挑衅台词，对手毫无反应 | `角色名（OS）` |
| 张嘴自语 vs 内心 | 独处时嘴唇明显张合 = 现场自语，不标 OS | 张嘴=`角色名`；闭嘴=`（OS）` |
| 镜头拍听众 / 远景 | 声音在当前时空发生，镜头拍听众或远景 | `角色名（画外）` |

## 🧰 脚本工具

| 脚本 | 用途 | 核心命令 |
|---|---|---|
| `batch_prep.py` | ① 批量抽 16kHz 极轻音轨 ② **逐句时间码中点 1:1 抽帧绑定** ③ 裁剪 4FPS 底部字幕带 | `python scripts/batch_prep.py --bind-frames ep01.mp4 ep01.srt`<br>`python scripts/batch_prep.py --audio-dir ./videos` |
| `srt_to_script.py` | SRT / VTT / 剪映 `draft_content.json` → L1 逐字稿（不盲拼吞句 + 断层预警 + 同音词纠偏 + OS 初标） | `python scripts/srt_to_script.py ep01.srt --merge 0 --gap-warn 3.5 --glossary "错词=正词"` |

两个脚本均内置 `--selftest`，已验证通过（本机 ffmpeg 可用）。

## ⚙️ 快速开始

```bash
# 安装到 OpenClaw
openclaw skills install ./short-drama-teardown --as short-drama-teardown

# 自检
python short-drama-teardown/scripts/batch_prep.py --selftest
python short-drama-teardown/scripts/srt_to_script.py --selftest

# 通道 B 核心：逐句台词中点抽帧绑定
python short-drama-teardown/scripts/batch_prep.py --bind-frames ep01.mp4 ep01.srt

# 字幕 → 逐字稿
python short-drama-teardown/scripts/srt_to_script.py ep01.srt --merge 0 --gap-warn 3.5
```

**给 AI 助手的最小执行序列**：读 `SKILL.md` → 锁定进场通道（A/B）→ 通道 B 先建唯一人物档案 → 逐句绑定画面与嘴型 → 交付逐字稿 → 还原剧本 → 骨架分析卡。

### 🧮 常用指令

`扒剧` · `扒剧本` · `扒一下这部短剧` · `拆解爆款` · `拉片` · `逐字稿` · `还原剧本` · `骨架分析`

## 📦 项目结构

```text
short-drama-teardown/
├── SKILL.md                          # 总控：双通道门禁 + 三把铁锁 + 三段交付
├── references/
│   ├── teardown-script-template.md   # 阶段一《扒剧逐字稿》模板（含唯一人物锁定表）
│   ├── script-restoration-template.md# 阶段二《扒剧还原剧本》模板
│   └── skeleton-card-template.md     # 阶段三《骨架分析卡》模板
└── scripts/
    ├── batch_prep.py                 # 音轨提取 / 逐句中点抽帧 / 字幕带裁剪
    └── srt_to_script.py              # SRT/VTT/剪映 → L1 逐字稿 + 纠偏 + OS 初标
```

## 🛡️ 版权与用途红线

- 产物仅限**拆解学习、结构研究**；
- 逐字稿与还原剧本含原作台词，**禁止直接照搬商用**；
- 每次交付首行注明：「拆解学习用途 · 骨架可迁移 · 台词不可照搬」。

---

<div align="center">

## 📄 License

**MIT** · 拆解学习用途 · 骨架可迁移 · 台词不可照搬

</div>
