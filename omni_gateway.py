#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Master Gateway & Fast-Path Router v5.1
Canonical entry point for the Triad-Omni Edge AI Cluster.
Directs all traffic to the zero-dependency Master Router in scripts/omni_fast_router_v4_9.py.
Supports Web Cyberdeck (:8000), Melvin HUD (:5000), Zero-CoT routing, FTS5 RAG, and MCP.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from omni_fast_router_v4_9 import run_server

if __name__ == "__main__":
    port_to_run = int(os.environ.get("PORT", 8000))
    run_server(port_to_run)
