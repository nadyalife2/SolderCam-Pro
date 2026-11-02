---
name: melvin-edge-ai
description: Engineering blueprint and deployment guide for building ultra-fast on-device autonomous AI voice assistants on low-spec Android hardware (MediaTek/Qualcomm, 2-3GB RAM) using native ARMv8 llama.cpp, PRoot Alpine Linux, deterministic fast-tool routing, and hands-free WebAudio UI.
---

# Melvin Edge AI: On-Device Autonomous Smart Assistant Blueprint

This skill captures the complete engineering methodology, architectural patterns, and troubleshooting techniques for deploying responsive, hands-free voice assistants directly on resource-constrained Android smartphones without relying on cloud services.

---

## 1. Architecture Overview: The Hybrid Bionic / PRoot Stack

Low-spec Android devices (e.g. MediaTek Helio X20 MT6797, 3GB RAM, Android 6.0–8.0) struggle under heavy virtualized overhead. Running an LLM inside PRoot Linux causes severe `ptrace` system call emulation penalties (up to 40% performance loss).

### Dual-Layer Execution Model:
```
┌─────────────────────────────────────────────────────────────┐
│ Android Host (Bionic C-Runtime / ext4 / /data/local/tmp)     │
│  - llama-server (Pure Native ARMv8 aarch64 NEON)            │
│  - Host Torch Bridge: watches /sdcard/melvin/torch_cmd      │
│  - MIUI Intent Broadcast: am broadcast TOGGLE_TORCH        │
└───────────────────────────┬─────────────────────────────────┘
                            │ localhost:8080 (HTTP /completion)
┌───────────────────────────▼─────────────────────────────────┐
│ Alpine Linux PRoot Jail (/data/local/tmp/alpine)            │
│  - Python 3.11 Runtime (Flask + FTS5 SQLite RAG)            │
│  - Sherpa-NCNN On-Device Speech-to-Text (STT)               │
│  - Dialogue Engine (Persona Routing: Rick Sanchez / Melvin)  │
│  - Fast Deterministic Tools: Math AST, CBR Rates, RSS News  │
│  - Organizer Engine: Notes SQLite & Background Alarms       │
└───────────────────────────┬─────────────────────────────────┘
                            │ localhost:5000 (HTTP / WebSocket)
┌───────────────────────────▼─────────────────────────────────┐
│ Client Layer (ai.melvin.app WebView / Mobile Browser)       │
│  - Hands-Free Voice VAD Loop (AudioContext / Resampling)    │
│  - Web Audio Multi-Tone Buzzer Alarm                        │
│  - Dark Glassmorphism Chat UI with Per-Message Timestamps   │
│  - White Floodlight Screen Screen Overlay                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Low-Latency Deterministic Routing Hierarchy

Never pass deterministic queries (arithmetic, calendar, reminders, flashlight, live currency, weather, news) to a 0.5B–1.5B LLM. Small SLMs take 5–8 seconds to infer on mobile CPU and hallucinate numbers.

### Priority Router in `agent_orchestrator.py`:
1. **Capability Questions (0.04s):**
   - Intercepts meta-questions (`что ты умеешь`, `ты можешь создать заметку`, `тест`) in `dialogue_engine.py` using canonical persona templates.
2. **Safe Math & Conversion (0.05–0.08s):**
   - Pure AST / regex evaluation in `smart_calc.py`.
   - Live Central Bank of Russia (CBR) XML feed for USD, EUR, CNY conversion.
   - Physical unit converter (miles $\leftrightarrow$ km, lbs $\leftrightarrow$ kg, °F $\leftrightarrow$ °C).
3. **Organizer & Memory (0.04–0.09s):**
   - Regex intent parser for `создай заметку`, `добавь заметку`, `прочитай мои заметки`.
   - Direct SQLite transaction (`agent_memory.db`) + mirror in `notes.md`.
4. **Live RSS News & Detail Reader (0.09s):**
   - Multi-source feed parser: VC.ru, Habr, 4PDA, iXBT, DTF, Rozetked, RIA Novosti.
   - Dynamic count extraction (`extract_news_count`): 1 to 10 items.
   - Topic extraction (`extract_news_topic`): filters articles by keywords.
   - In-memory article cache (`LAST_NEWS_CACHE`).
   - Deep detail reader (`parse_news_detail_request`): parses requests like `расскажи про 3 подробнее` or `что в 7` and reads a 3–4 sentence essence of the article.
5. **Hardware & Environment Bridge (0.05s):**
   - Flashlight toggle via IPC file `/sdcard/melvin/torch_cmd` + host MIUI broadcast.
   - Battery telemetry via `/sys/class/power_supply/battery/`.
6. **Local LLM Fallback (Qwen2.5-0.5B / 1.5B via `llama-server`):**
   - Triggered only for open-ended conversational queries.

---

## 3. Hardware Torch IPC Bridge on Android

Android `WebView` applications often lack `android.permission.CAMERA`, preventing direct `CameraManager.setTorchMode` usage. In PRoot Alpine Linux, Android Java APIs cannot be called directly.

### The File-Watcher IPC Solution:
1. In `phone_tools.py`, write target state `"1"` or `"0"` to `/sdcard/melvin/torch_cmd`.
2. In host bionic shell startup script (`start_melvin.sh`):
   ```bash
   (
       while true; do
           if [ -f /sdcard/melvin/torch_cmd ]; then
               CMD=$(cat /sdcard/melvin/torch_cmd 2>/dev/null)
               rm -f /sdcard/melvin/torch_cmd
               if [ "$CMD" = "1" ]; then
                   /system/bin/am broadcast -a miui.intent.action.TOGGLE_TORCH --ez miui.intent.extra.IS_ENABLE true >/dev/null 2>&1
               elif [ "$CMD" = "0" ]; then
                   /system/bin/am broadcast -a miui.intent.action.TOGGLE_TORCH --ez miui.intent.extra.IS_ENABLE false >/dev/null 2>&1
               fi
           fi
           sleep 0.1
       done
   ) &
   ```
3. Simultaneously trigger client-side white screen floodlight in the web interface for maximum ambient illumination.

---

## 4. UI/UX Rules for Hands-Free Smart Speakers

1. **Per-Message Timestamps:**
   - Both user and assistant bubbles must display local `HH:MM` time.
   - Assistant bubbles include inference latency (`0.04s`) and tool badges (`🔧 safe_calculator`, `🔧 live_web_date`).
2. **Preserve Line Breaks:**
   - Always include `white-space: pre-wrap;` in message CSS to prevent numbered lists from collapsing into dense paragraphs.
3. **Audio Feedback & Wake Cues:**
   - Web Audio synthesizer provides clean 4-tone alert chimes for timer expirations without external sound file dependencies.
   - Audio elements must use `play().catch(...)` to prevent unhandled promise rejections before user gesture initialization.


---

## 5. Hardware Audit & Pinout Reference (Android TV & External Devices)

For physical wiring, safety rules, and SoC identification, refer to the verified technical reference:
* [`references/HARDWARE_PINOUTS_AND_SOC_AUDIT.md`](references/HARDWARE_PINOUTS_AND_SOC_AUDIT.md) — Comprehensive connector pinouts (Micro-USB 5-pin, USB-A 4-pin, Type-C 24-pin), anti-collision VBUS isolation rules, JEDEC CID flash memory table, and complete SoC nanometer database (Amlogic, Rockchip, Allwinner, Realtek, Qualcomm, MediaTek).
* Python engine: [`melvin_src/soc_database.py`](file:///d:/для%20one%20plus%20nord%20n10/melvin_src/soc_database.py).
