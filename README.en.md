<div align="center">

# 🔍 Short-Drama Teardown

## **V4.0.1 · Delivery Edition**

> Reverse-engineer a viral short-drama episode into a transcript → production-ready screenplay → skeleton breakdown → **offline single-page HTML report**

**English** | [中文](README.md)

![Version](https://img.shields.io/badge/version-V4.0.1-6a5acd)
![Gate](https://img.shields.io/badge/gate-dual--channel-00b4d8)
![Locks](https://img.shields.io/badge/identity-3%20hard%20locks-2ec4b6)
![Report](https://img.shields.io/badge/output-offline%20HTML-2b9348)
![Scripts](https://img.shields.io/badge/scripts-3%20self--tested-ff6b6b)
![License](https://img.shields.io/badge/license-MIT-ffca3a)
![Stars](https://img.shields.io/github/stars/lixiaoxiao9888-create/short-drama-teardown?style=social)

---

### 🎬 Pipeline

```
Entry gate (link / raw video) → lock unique characters → bind every line to its frame → transcript → screenplay → skeleton → offline HTML report
```

</div>

---

## 🧭 What this is

A **rule set a vision-capable AI agent executes** (OpenClaw Skill / agent skill pack) that turns a finished short-drama episode back into four usable assets: **transcript, screenplay, skeleton card, offline HTML report**.

This is not plain transcription. It first solves the two hardest problems of raw-video teardown — *who is speaking* and *who this person actually is* — and only then reconstructs the script.

Four things it guarantees:

1. **No identity splitting** — the same face under a different eye color, awakened form or battle damage stays **one** character; names are locked by in-dialogue address terms.
2. **No line guessing** — every line is bound to the frame at its exact midpoint `(start+end)/2`; mouth open = on-camera dialogue, mouth shut = OS. No sparse 10-second sampling.
3. **No dropped words** — dual-track extraction, time-gap warnings, homophone correction; frame-grab failures are raised loudly (exit code 3), never silently passed.
4. **Deliverable** — all four blocks collapse into one structured JSON (single field contract) and render as an **offline single-page HTML report**: anchor nav, copy-whole-episode, CSV export, print/PDF forced to light theme.

## 🎯 Use cases

- **Teardown / scene study** of hit short dramas — transcript, screenplay, skeleton and HTML in one pass
- **Competitive analysis** — per-episode beat tables, cross-episode cliffhanger matrix, hook rotation, transferable formulas
- **Subtitle-less raw video** — send a bare `.mp4/.mov` and still lock characters and speakers
- **Batch episodes** — three batch paths: JianYing subtitle projects, local ASR, voice-print clustering
- **Pre-adaptation research** — extract the skeleton first, then decide what to transfer and what not to

## 🔥 Core capabilities

### 0 · Entry gate (first hard rule)

| Channel | Recognized by | Main risk | Mandatory lock |
|---|---|---|---|
| **A — link** | Douyin / Kuaishou / Hongguo URL, or title + link | Dead link, login wall, no subtitle track | Scrape title / synopsis / cast into a *preset roster*; pull subtitles with `yt-dlp --write-subs`; fall back to channel B |
| **B — raw video** | User uploads `.mp4/.mov` | **No names, speakers easily swapped, one person split into many** | **No sparse frame guessing** — run the three identity hard locks below |

> With no asset yet, ask first: **A. link** or **B. raw video file**.

### 0·1 · Vision gate (added in V4.0.1)

All three locks depend on *actually seeing frames* — face and wardrobe for identity merging, subject / lip movement / expression for per-line attribution. Before starting, `read` one frame: if the model rejects images, **never infer speakers or OS/VO from text alone**. Switch to a `text+image` model, or hand the frame index and images to a human; otherwise stop — a fabricated transcript is worse than no transcript.

### 1 · Three identity hard locks

1. **Merge lock** — walk the whole episode first and build the unique visual roster. Same face + same main outfit means the same character, even across eye-color shifts, awakened forms (e.g. nine tails) or battle damage. Co-appearing characters get separate entries. Every visual anchor must come from a frame you actually viewed.
2. **Address-term lock** — scan all address terms (name, honorific, insult), confirm on screen, then use one canonical name from second 1 to the end. Temporary visual labels like “woman in grey” are banned.
3. **Per-line frame binding lock** — `batch_prep.py --bind-frames` grabs one frame per line at its midpoint; check subject, lip movement (dialogue vs OS) and voice timbre. Lines marked `❌ 未抽到帧` must be re-grabbed — never filled from memory.

### 2 · No-dropped-word extraction

- No low-FPS sparse sampling.
- `--merge 0` by default. `--merge N` only merges when three checks pass (continuation punctuation / fragment ≤ 12 chars / not a new speaker or OS block), with a hard chain cap of 2 and a `⤵` mark on merged lines.
- `--gap-warn 3.5` flags silent gaps; pure action stretches are written back as `△` lines.

### 3 · OS / VO four-dimension inference

| Signal | Rule | Script tag |
|---|---|---|
| Mouth shut in close-up | Character on screen, lips closed, their voice audible | `NAME（OS）` |
| No reaction in dialogue | Reveal / taunt with no reaction from the listener | `NAME（OS）` |
| Speaking to self | Alone and lips clearly moving = live speech | `NAME` (no OS tag) |
| Camera on listener | Voice happens in-scene, camera on listener or wide | `NAME（画外）` |

### 4 · Four-stage delivery

| Stage | Output | Content |
|---|---|---|
| 1 | **Transcript** | Unique visual/name lock table + per-line timecode, bound frame, speaker, OS/VO attribute |
| 2 | **Screenplay** | Scene numbers, day/night, interior/exterior, blocking, `△` action & expression, dialogue vs OS, cleaned homophones |
| 3 | **Skeleton card** | Per-episode beat table, cross-episode cliffhanger matrix, hook rotation, OS information-gap usage, transferable formulas |
| 4 | **Offline HTML & CSV** | Structured JSON → one command; field contract in `references/data-schema.json`; automatic field check before rendering |

## 🧰 Scripts

| Script | Purpose | Key command |
|---|---|---|
| `batch_prep.py` | ① batch 16 kHz light audio ② **per-line midpoint frame binding** (fails loudly, exit 3) ③ 4 FPS subtitle-strip cropping | `python scripts/batch_prep.py --bind-frames ep01.mp4 ep01.srt` |
| `srt_to_script.py` | SRT / VTT / JianYing `draft_content.json` → L1 transcript (no blind merging, gap warnings, glossary correction, OS pre-tagging) | `python scripts/srt_to_script.py ep01.srt --merge 0 --gap-warn 3.5` |
| `export_html.py` | JSON → **offline single-page HTML report** (anchor nav, copy episode, CSV export, light-theme print); `--write-example` emits a canonical sample | `python scripts/export_html.py data.json --out report.html` |

All three ship a `--selftest` (including BOM-compatibility regressions) and pass locally.

## ⚙️ Quick start

```bash
openclaw skills install ./short-drama-teardown --as short-drama-teardown

python short-drama-teardown/scripts/batch_prep.py --selftest
python short-drama-teardown/scripts/srt_to_script.py --selftest
python short-drama-teardown/scripts/export_html.py --selftest

python short-drama-teardown/scripts/batch_prep.py --bind-frames ep01.mp4 ep01.srt
python short-drama-teardown/scripts/srt_to_script.py ep01.srt --merge 0 --gap-warn 3.5

python short-drama-teardown/scripts/export_html.py --write-example --out data.json
python short-drama-teardown/scripts/export_html.py data.json --out report.html
```

**Minimum agent sequence**: read `SKILL.md` → lock the entry channel (A/B) → verify the model can see images → build the unique roster → bind every line to its frame → transcript → screenplay → skeleton → JSON → HTML report.

### ⌨️ Trigger words

`扒剧` · `扒剧本` · `拆解爆款` · `拉片` · `逐字稿` · `还原剧本` · `骨架分析` · `teardown` · `script restoration` · `transcript from video`

## 📦 Layout

```text
short-drama-teardown/
├── SKILL.md                          # Controller: vision gate + dual channel + three locks + four-stage delivery
├── README.md / CHANGELOG.md / CHECKLIST.md
├── references/
│   ├── data-schema.json              # JSON field contract (single source of truth)
│   ├── teardown-script-template.md   # Stage 1 transcript template
│   ├── script-restoration-template.md# Stage 2 screenplay template
│   └── skeleton-card-template.md     # Stage 3 skeleton card template
└── scripts/
    ├── batch_prep.py                 # audio / per-line frames / subtitle strip
    ├── srt_to_script.py              # subtitles → L1 transcript
    └── export_html.py                # JSON → offline HTML report
```

## 🗓 Changelog

- **V4.0.1 (2026-11-16)** — delivery-edition fixes: added the JSON field contract plus a pre-render field check (exit 4); frame-grab failures now raise (exit 3); three-check merge guard with a 2-line chain cap; millisecond carry, OS counting and print-theme fixes. Same version patched: BOM-safe reads (`utf-8-sig`) and the vision-capability gate.
- **V4.0 (2026-11-16)** — added `batch_prep.py` (audio / per-line midpoint frames / subtitle strips) and `export_html.py` (offline HTML + CSV); entry logic narrowed to two channels; three identity locks and OS/VO inference introduced.
- **V3.1 (2026-10-19)** — first public release with the dual-channel gate and three locks.

## 🛡️ Copyright

- Outputs are for **study and structural analysis only**.
- Transcripts and restored screenplays contain original dialogue — **do not reuse commercially**.
- Every deliverable starts with: “For study · structure is transferable · original dialogue is not”.

---

<div align="center">

## 📄 License

**MIT** · study use · structure transferable · dialogue not reusable

</div>
