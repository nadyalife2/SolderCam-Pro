# Project Guidelines: Triad-Omni Edge AI Cluster (Xiaomi Mi 10T, OnePlus Nord N10 5G, Redmi Note 4)

## Domain Scope
- **Heterogeneous AI Cluster (Triad-Omni v4.7):**
  - **NODE-1 (Main Brain):** Xiaomi Mi 10T 5G (`M2007J3SY`, `apollo`, Snapdragon 865 `kona`, 8GB LPDDR5, LibreMobileOS 15) — `Qwen3.5-9B-MTP UD-Q3_K_XL` + `Gemma 4 E4B` @ `:8080`.
  - **NODE-2 (Reflex & Embeddings):** OnePlus Nord N10 5G (`BE2029`, `billie`, Snapdragon 690, 6GB LPDDR4X, OxygenOS 11) — `LFM2.5-8B-A1B` @ `:8081` + `BGE-M3` @ `:8082` + TWRP + Battery Guard 24/7.
  - **NODE-3 (Master Hub & Telemetry Gateway):** Xiaomi Redmi Note 4 (`mido`, Snapdragon 625) @ `:8000`.
- **Android App Development:** `com.soldercam.pro` (Camera2 API, NTC thermistor & battery telemetry, Kotlin, Jetpack).
- **Hardware & Firmware Engineering:** Partitioning (A/B, boot, dtbo, recovery, TWRP), kernel patching via Magisk, battery PMIC switches (sysfs charging limits), thermal throttling guards.

## Mandatory Execution Rules (Strictly Follow on EVERY Turn Without Reminders)
1. **Mandatory Screenshot & Visual Logging via ADB:**
   - Every single operational phase, flash step, boot transition, recovery verification, process startup, benchmark, and error diagnosis MUST automatically take high-quality device screenshots via `adb exec-out screencap -p > screenshots/<name>.png` and save them with descriptive filenames.
   - Never wait for the user to ask for screenshots.
2. **Strict Author Voice & Style (`USER_VOICE_STYLE_GUIDE.md`):**
   - ALL articles, summaries, responses, and technical notes MUST be written strictly in the user's voice: **feminine past tense** («прошила», «собрала», «раскопала», «протестировала», «проверила»), conversational, punchy, zero fluff, maximum engineering precision.
   - Never wait for the user to remind about the author's voice.
3. **Graphify Knowledge Graph Sync:**
   - After updating code, scripts, or articles, keep `graphify` updated.

## Active Skills for This Workspace
Only the following skills are authorized for this project:
- `gadget-camera-tuning` (Camera2 API, OV64B sensor tuning, PMIC/NTC diagnostics)
- `mobile-android-design` (Material Design 3, touch targets, mobile UX)
- `compose-multiplatform-patterns` (Jetpack Compose & CMP, state hoisting, recomposition, 48dp targets)
- `tailwind-patterns` (Tailwind v4 CSS-first tokens, container queries, anti-slop HUD design)
- `seo-geo-optimizer` (Technical SEO, Schema.org JSON-LD, Generative Engine Optimization for Perplexity/ChatGPT)
- `product-growth-cro` (RICE scoring, high-converting copywriting, landing page CRO)
- `schema-markup` (Schema.org JSON-LD structured data generator)
- `content-creator` (Brand voice compliance and anti-slop analyzer)
- `copywriting` (Landing pages, value propositions, objection handling)
- `content-marketer` (Multi-platform content atomization and distribution)
- `programmatic-seo` (Template-driven long-tail keyword scaling)
- `product-manager` (PRD, lean canvas, RICE prioritization)
- `marketing-ideas` (140+ growth tactics and devtool launch playbooks)
- `ui-design-system` (Tokens, OLED dark theme, component states)
- `artifacts-builder` (Interactive standalone HTML/SVG widgets)
- `onboarding-cro` (First-run UX and friction reduction)
- `android-cli`
- `reverse-engineer-anything`
- `awesome-rea` (Offline knowledge base of 1,265+ reverse engineering tools, papers & decompilation cases)
- `rea-analysis-optimization`, `rea-tool-design`, `rea-ci-tests-audit`, `rea-changelog-update`
- `impeccable`
- `melvin-edge-ai` (On-device LLM, PRoot Alpine, hybrid Bionic stack, fast tools & voice assistant)
- `budget-tablet-unmasking-tuning` (Hardware unmasking, anti-spoofing, fastboot driver fixes, debloating, AOT compilation & DPI bypass)
- `tochka-plavleniya-pipeline` (Full-cycle autonomous content & engineering SaaS pipeline for Tochka-Plavleniya: 2 voices, schema v1.1, OTK, delivery_cli, Rich Snippets)
- `gsd-execution-protocol` (Spec-driven context-conserving task orchestration, BMAD method & milestone gates for edge AI & Android)
- `karpathy-code-principles` (Andrej Karpathy-inspired minimalist, zero-abstraction, stdlib-first engineering for ARMv8/Snapdragon)
- `graphify` (Codebase & architecture persistent knowledge graph, god nodes, community detection, traversal)
- Built-in Antigravity utilities (`agy-customizations`, `automation`, `generative_ui`)

## Excluded Skills
All biomedical/science skills (`science` plugin: PubMed, AlphaFold, ChEMBL, UniProt, BLAST, etc.), cloud infrastructure (`google-cloud-developer`), and unrelated external skills are explicitly excluded and must not be used in this workspace.
