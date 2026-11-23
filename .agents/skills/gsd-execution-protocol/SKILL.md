---
name: gsd-execution-protocol
description: Spec-driven, context-conserving task orchestration framework (Get Shit Done / BMAD Method) tailored for edge AI clusters, Android firmware engineering, and complex hardware projects. Breaks large tasks into atomic, milestone-gated phases, maintains project state in structured markdown files, and keeps context window consumption under 15%.
---

# GSD Execution Protocol: Spec-Driven Autonomous Task Orchestration

The **GSD (Get Shit Done)** protocol is an engineering execution framework designed to prevent LLM agent context rot, hallucinations, and drifting during long, complex technical tasks (firmware modifications, multi-node edge AI clusters, Android app development, and multi-file codebases).

Instead of dumping massive instructions and conversational history into the agent's context window, GSD operates on **declarative file-persisted state**: atomic phases, explicit exit criteria, and strict verification gates.

---

## 1. Core Architecture: The 3-File State Anchor

GSD eliminates reliance on conversational memory by anchoring all project state in three lightweight markdown files stored in the workspace:

```
workspace/
├── .planning/
│   ├── PROJECT_SPEC.md       # High-level architecture, boundaries, invariants, hardware constraints
│   ├── ROADMAP.md            # Numbered phases, milestones, dependencies, completed checkpoints
│   └── CURRENT_PHASE.md      # Active slice: exact commands, exit criteria, raw telemetry log
```

### File Schemas

#### A. `PROJECT_SPEC.md` (Static Anchor)
Defines what we are building, what is strictly out of scope, and physical limits:
```markdown
# Project Specification: [System / Module Name]

## 1. Hardware & System Boundaries
- Target Devices: Xiaomi Mi 10T (Snapdragon 865, 8GB), OnePlus Nord N10 (Snapdragon 690, 6GB)
- Physical Limits: Max SoC temp 45°C, sysfs charging bypass required, memory cap 4.2GB
- Network Topology: LAN 192.168.1.0/24, ports 8000 (Hub), 8080 (NODE-1), 8081 (NODE-2)

## 2. Invariants (Never Break)
- No cloud API fallbacks for factual queries (100% offline autonomy).
- ADB visual logging for all state changes (`screenshots/`).
- Author voice: feminine past tense, zero fluff, engineering precision.
```

#### B. `ROADMAP.md` (Global Progress Matrix)
Tracks cross-phase progression with binary completion status:
```markdown
# Engineering Roadmap

- [x] Phase 1: Native ARMv8 llama-server compilation & CPU affinity tuning (`taskset -c 4,5,6,7`)
- [x] Phase 2: Dynamic Lookup Cache (`lookup.cache`) & KV-cache quantization (`-ctk q8_0 -ctv q8_0`)
- [/] Phase 3: Fast-Path Router regex & empty-reasoning injection (`<think>\n</think>`)
- [ ] Phase 4: Full integration benchmark & thermal guard stress test
```

#### C. `CURRENT_PHASE.md` (Active Working Memory)
The only file read and mutated during turn execution:
```markdown
# Active Phase: Phase 3 (Fast-Path Router Optimization)

## Goal
Implement latency-based fast-routing on NODE-3 to bypass deep CoT for queries with score < 0.65.

## Step-by-Step Execution Plan
1. [x] Write regex matching table in Python route handler.
2. [/] Benchmark response latency with curl (Target: < 15ms).
3. [ ] Verify fallback to NODE-1 when complexity exceeds threshold.

## Exit Criteria (Must all be TRUE to advance)
- [ ] Roundtrip latency < 20ms confirmed via curl timer.
- [ ] Telemetry logged with timestamp.
- [ ] Screenshot captured: `screenshots/phase3_router_bench.png`.
```

---

## 2. The BMAD Workflow (Break, Map, Architect, Deliver)

When a complex user goal is received, execute the BMAD loop:

```
┌──────────────────────────────────────────────────────────────┐
│ 1. BREAK: Split monolithic goal into <= 45-minute sub-tasks  │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│ 2. MAP: Define explicit dependencies & file touches           │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│ 3. ARCHITECT: Write inputs/outputs & exit criteria           │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│ 4. DELIVER: Execute single phase, verify gate, commit state  │
└──────────────────────────────────────────────────────────────┘
```

### Execution Rules
1. **Single Phase Focus:** An agent turn may ONLY work on items in `CURRENT_PHASE.md`.
2. **Context Purge Gate:** Never keep multiline command outputs (logcat, compiler dumps) in conversational turns. Pipe output to scratch files (`scratch/build.log`), grep errors, and report only the summarized delta.
3. **Milestone Sign-Off:** When all exit criteria in `CURRENT_PHASE.md` are checked, append the result to `ROADMAP.md`, archive the log, and advance the phase.

---

## 3. Context Conservation Checklist (Anti-Token Bloat)

- [ ] Command outputs over 20 lines piped to files (`> scratch/output.log 2>&1`).
- [ ] State verified by reading file diffs, not re-reading entire source code.
- [ ] No speculative conversation; actions are backed by file edits or shell executions.
- [ ] Screenshots taken with `adb exec-out screencap -p > screenshots/<name>.png` for visual proof.
- [ ] Graphify updated after phase completion (`graphify update .`).
