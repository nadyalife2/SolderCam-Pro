---
name: karpathy-code-principles
description: Andrej Karpathy-inspired engineering principles for ultra-minimalist, zero-abstraction, high-performance code. Emphasizes single-file implementations, stdlib-first architecture, explicit dataflows without magical frameworks, low-memory buffers for mobile ARMv8/Snapdragon chips, and immediate reproducible verification.
---

# Karpathy Code Principles: Minimalist, Zero-Magic Engineering

This skill codifies the engineering philosophy popularized by Andrej Karpathy (creator of `nanoGPT`, `micrograd`, `llm.c`): writing code that is **radically simple, fully transparent, computationally efficient, and entirely devoid of enterprise boilerplate**.

In the context of the **Triad-Omni Edge AI Cluster** and Android/ARMv8 systems programming, this philosophy prevents bloated frameworks from consuming RAM, degrading cache locality, and causing unneeded CPU thrashing on mobile SoCs.

---

## 1. The Core Commandments

### I. Single-File Over Micro-Packages
- If a utility, micro-service, or model bridge can fit into 150–400 lines of clean Python, C, or Kotlin, **keep it in one file**.
- Avoid creating 10 directories (`/interfaces`, `/factories`, `/adapters`, `/models`, `/services`) for a straightforward 200-line script.
- Anyone (including an LLM agent with limited context) should be able to read top-to-bottom and hold the entire execution graph in memory.

### II. Stdlib & POSIX First, Zero Magic
- Before importing an external package (like LangChain, AutoGen, heavy ORMs), ask: *Can Python's `sqlite3`, `urllib.request`, `subprocess`, `dataclasses`, or C's standard POSIX sockets do this natively?*
- In 95% of cases, native standard libraries are 10x faster, zero-dependency, and never suffer from breaking API changes or dependency drift.

### III. Explicit Loops & Flat Execution Flows
- Reject nested decorators, abstract metaclasses, and multi-layered event dispatchers that obscure what actually runs on the CPU.
- Write explicit loops, direct buffer writes, and clear procedural steps.
- Code should read like an instruction list: allocate memory → read stream → compute → write output.

### IV. Mechanical Sympathy (Hardware & Memory Awareness)
- On mobile SoCs (Kryo 585 on Snapdragon 865, Kryo 560 on Snapdragon 690):
  - Avoid creating thousands of temporary objects per second (causes garbage collection pauses in Android/Python).
  - Pre-allocate arrays and buffers (`bytearray`, contiguous C arrays).
  - Respect L1/L2/L3 cache: keep micro-batches contiguous and memory access linear.
  - Bind threads to physical performance cores via `taskset` (e.g. Kryo Gold cores 4,5,6,7) instead of letting the OS scheduler bounce threads across energy-saving Silver cores.

### V. Reproducible One-Liner Verification
- Every script must have a standalone execution path:
  ```bash
  python3 router.py --test
  # or
  gcc -O3 -march=armv8-a+neon engine.c -o engine && ./engine --bench
  ```
- If you can't verify functionality with a single terminal command in under 3 seconds, the testing abstraction is broken.

---

## 2. Before & After: Enterprise Slop vs. Karpathy Minimalist

### Example: Fast Telemetry & Routing Service

#### ❌ The Over-Engineered Approach (Enterprise Slop)
```python
# 12 files, 4 abstract classes, pydantic models, async event loops
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pydantic import BaseModel
import asyncio

class AbstractTelemetryPayload(BaseModel):
    timestamp: float
    device_id: str

class ITelemetryService(ABC):
    @abstractmethod
    async def process(self, payload: AbstractTelemetryPayload) -> None:
        pass

class TelemetryDispatcherFactory:
    @staticmethod
    def get_dispatcher(provider: str) -> ITelemetryService:
        # 40 lines of dependency injection and registration
        ...
```

#### ✅ The Karpathy Minimalist Approach (Direct, Fast, Clean)
```python
#!/usr/bin/env python3
"""Single-file edge telemetry router & bypass controller."""
import json, socket, time, sys

CONFIG = {
    "node1_host": "192.168.1.101",
    "node1_port": 8080,
    "max_temp_c": 45.0,
    "bypass_score": 0.65
}

def check_thermal_guard(temp_c: float) -> bool:
    """Returns True if thermal limits require charge suspension."""
    return temp_c > CONFIG["max_temp_c"]

def route_query(prompt: str, complexity_score: float) -> str:
    """Route instantly if complexity is trivial, else forward to main LLM."""
    if complexity_score < CONFIG["bypass_score"]:
        return "<think>\n</think>\nFast-Path: query resolved deterministically."
    
    # Direct raw socket / HTTP forward with zero framework overhead
    s = socket.create_connection((CONFIG["node1_host"], CONFIG["node1_port"]), timeout=2.0)
    req = f"POST /completion HTTP/1.1\r\nHost: node1\r\nContent-Length: {len(prompt)}\r\n\r\n{prompt}"
    s.sendall(req.encode())
    res = s.recv(4096).decode()
    s.close()
    return res

if __name__ == "__main__":
    if "--test" in sys.argv:
        t0 = time.perf_counter()
        out = route_query("ping", 0.2)
        dt_ms = (time.perf_counter() - t0) * 1000
        print(f"PASS: latency={dt_ms:.2f}ms output='{out[:40]}'")
```

---

## 3. Rules of Engagement for Coding Turns

1. **Ask First:** Is there a simpler way with standard libraries before adding an external package?
2. **Never Add Unused Code:** No speculative interfaces, "future-proofing" methods, or boilerplate getters/setters.
3. **Verify Immediately:** Run the script or test command directly via terminal to verify the exit code.
4. **Keep it Readable:** Code should be simple enough that someone reading it on a mobile screen in Termux understands it instantly.
