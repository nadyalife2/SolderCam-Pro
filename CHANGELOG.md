# Changelog - Triad-Omni Edge AI Cluster

All notable changes to the Triad-Omni Edge AI Cluster and SolderCam-Pro project are documented in this file.

## [5.1.0] - 2026-11-21

### Added
- **Full MCP Protocol Handshake:** Added compliant JSON-RPC 2.0 `initialize` (protocolVersion `2024-11-05`), `ping`, and `notifications/initialized` handlers in `omni_mcp_server.py`. Fixes hanging connections in DeepSeek Harness, Claude Code CLI, Cursor, and Continue.
- **Central Cluster Network Matrix:** Introduced `config/cluster.env` as the single source of truth for all IP addresses (`192.168.31.x`) and ports across all shell and Python components.
- **Safe Model Downloader:** Added `-f` guard to `curl` in `download_models.sh` with size verification and explicit target for main brain model `brain.gguf`.
- **Universal Battery Guard:** Deployed `scripts/battery_guard_24x7.sh` supporting PM8150B, PM7250B, and PMI8952 sysfs nodes.
- **Legacy Gateways Archive:** Archived monolithic legacy gateways (v4.0, v4.6, v4.7, v4.8) into `archive/legacy_gateways/`.

### Fixed
- **Port 8080 Conflict on Node-1:** Prevented Fast-Path Router from binding port 8080 on Xiaomi Mi 10T (`apollo`), reserving 8080 strictly for `llama-server` and eliminating loopback recursion.
- **OpenAI `/v1/chat/completions` Schema:** Fixed missing `choices[0].message.content` wrapper in `omni_fast_router_v4_9.py`, ensuring 100% compatibility with standard OpenAI API clients while preserving backwards compatibility for Web UI.
- **`START_REDMI_DECK.bat` Reliability:** Added background execution with `nohup`, ConnectTimeout for SSH, and fixed path to `start_deck.sh`.
- **Root Documentation:** Completely purged legacy `payload-dumper-go` references from `README.md` and `CHANGELOG.md`, replacing them with canonical Triad-Omni documentation.

---

## [5.0.0] - 2026-11-19

### Added
- **Fast-Path Router v5.0 (Zero-Dependency):** Native Python standard library implementation (`ThreadingHTTPServer` + `urllib`) replacing external dependency bloat.
- **Zero-CoT Reasoning Injection:** Automatic injection of `<think>\n</think>\n` for simple classification queries, reducing Snapdragon 865 latency from 120s down to 6.15s.
- **Cyberdeck Web UI v4.9:** Real-time HUD on port 8000 with live node health indicators, hot cartridge swapping, and battery telemetry.
- **Tier-0 Regex Fast-Path:** 0.019 ms deterministic response for status, battery, ping, and diagnostic queries.

---

## [4.7.0] - 2026-11-15

### Added
- **Multi-Node Cluster Orchestration:** Dynamic telemetry routing between Xiaomi Mi 10T 5G, OnePlus Nord N10 5G, and Redmi Note 4.
- **SQLite FTS5 RAG:** Sub-4ms local document retrieval for hardware datasheets, IPC-A-610 standards, and reverse engineering notes.
- **Battery Guard 24/7:** Sysfs charging disable/enable hysteresis (70% - 78%) for continuous cluster uptime.

---

## [4.0.0] - 2026-11-10

### Added
- **Initial Hardware Deck:** First hardware-based dashboard prototype deployed to Redmi Note 4 in Alpine Linux PRoot.
