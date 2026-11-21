#!/usr/bin/env python3
"""
Xiaomi Redmi Note 4 (nikel) - Edge Node & Hardware Deck Daemon
Part of the Triad-Omni Distributed AI Cluster
Integrates with the Big AI (Antigravity / PC Master)
"""

import http.server
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlparse, parse_qs

PORT = 5055

def get_battery_telemetry():
    base = "/sys/class/power_supply/battery"
    res = {
        "capacity_percent": None,
        "temperature_c": None,
        "voltage_v": None,
        "current_ma": None,
        "status": "Unknown",
        "health": "Unknown"
    }
    try:
        if os.path.exists(f"{base}/capacity"):
            with open(f"{base}/capacity") as f:
                res["capacity_percent"] = int(f.read().strip())
        if os.path.exists(f"{base}/batt_temp"):
            with open(f"{base}/batt_temp") as f:
                res["temperature_c"] = round(int(f.read().strip()) / 10.0, 1)
        if os.path.exists(f"{base}/batt_vol"):
            with open(f"{base}/batt_vol") as f:
                res["voltage_v"] = round(int(f.read().strip()) / 1000.0, 3)
        if os.path.exists(f"{base}/current_now"):
            with open(f"{base}/current_now") as f:
                res["current_ma"] = int(f.read().strip())
        if os.path.exists(f"{base}/status"):
            with open(f"{base}/status") as f:
                res["status"] = f.read().strip()
        if os.path.exists(f"{base}/health"):
            with open(f"{base}/health") as f:
                res["health"] = f.read().strip()
    except Exception as e:
        res["error"] = str(e)
    return res

def get_cpu_thermal():
    thermals = {}
    thermal_dir = "/sys/class/thermal"
    try:
        if os.path.exists(thermal_dir):
            for entry in sorted(os.listdir(thermal_dir)):
                if entry.startswith("thermal_zone"):
                    t_type_path = os.path.join(thermal_dir, entry, "type")
                    t_temp_path = os.path.join(thermal_dir, entry, "temp")
                    if os.path.exists(t_type_path) and os.path.exists(t_temp_path):
                        with open(t_type_path) as ft, open(t_temp_path) as fv:
                            sensor_type = ft.read().strip()
                            raw_temp = int(fv.read().strip())
                            if -50000 < raw_temp < 150000:
                                thermals[sensor_type] = round(raw_temp / 1000.0, 1)
    except Exception as e:
        thermals["error"] = str(e)
    return thermals

def get_ram_info():
    ram = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    k = parts[0].strip()
                    if k in ["MemTotal", "MemFree", "MemAvailable", "Cached", "Buffers"]:
                        val_kb = int(parts[1].strip().split()[0])
                        ram[k + "_MB"] = round(val_kb / 1024.0, 1)
    except Exception as e:
        ram["error"] = str(e)
    return ram

def get_uptime():
    try:
        with open("/proc/uptime") as f:
            up = float(f.read().split()[0])
            return round(up, 1)
    except Exception:
        return 0.0

def execute_local_tool(tool_name, params):
    t_start = time.time()
    result = {"success": True, "tool": tool_name}

    if tool_name == "battery":
        result["data"] = get_battery_telemetry()
    elif tool_name == "thermal":
        result["data"] = get_cpu_thermal()
    elif tool_name == "ram":
        result["data"] = get_ram_info()
    elif tool_name == "calc":
        expr = params.get("expr", "")
        # Safe math evaluation using simple parser
        allowed = set("0123456789+-*/(). %^")
        if all(c in allowed for c in expr) and expr.strip():
            safe_expr = expr.replace("^", "**")
            try:
                res = eval(safe_expr, {"__builtins__": None}, {})
                result["data"] = {"expression": expr, "result": res}
            except Exception as e:
                result["success"] = False
                result["error"] = f"Math error: {str(e)}"
        else:
            result["success"] = False
            result["error"] = "Invalid arithmetic expression"
    elif tool_name == "fts5_search":
        q = params.get("query", "")
        # Query local in-memory or on-disk FTS5 knowledge base
        db_path = "/root/omni_hub/db/knowledge.db"
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            con = sqlite3.connect(db_path)
            con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(title, content);")
            cur = con.execute("SELECT title, snippet(docs, 1, '<b>', '</b>', '...', 10) FROM docs WHERE docs MATCH ? LIMIT 5;", (q,))
            rows = cur.fetchall()
            con.close()
            result["data"] = {"query": q, "matches": [{"title": r[0], "snippet": r[1]} for r in rows]}
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
    elif tool_name == "ping":
        result["data"] = {"status": "PONG", "node": "Redmi-Note-4-Edge-Node"}
    else:
        result["success"] = False
        result["error"] = f"Unknown tool: {tool_name}"

    result["latency_ms"] = round((time.time() - t_start) * 1000, 2)
    return result

def route_intent(prompt):
    """
    Sub-millisecond intent router:
    Decides whether Xiaomi can execute locally or delegates to Big AI.
    """
    p_lower = prompt.lower().strip()

    # Hardware battery checks
    if any(w in p_lower for w in ["батарея", "заряд", "аккумулятор", "вольтаж", "battery", "charge"]):
        bat = get_battery_telemetry()
        text = f"Заряд батареи: {bat.get('capacity_percent')}%, напряжение: {bat.get('voltage_v')}V, температура: {bat.get('temperature_c')}°C, статус: {bat.get('status')}."
        return {
            "routed_to": "local_hardware_probe",
            "handled_locally": True,
            "response": text,
            "telemetry": bat
        }

    # Thermal checks
    if any(w in p_lower for w in ["температура", "нагрев", "градус", "thermal", "temp", "cpu"]):
        therm = get_cpu_thermal()
        cpu_t = therm.get("mtktscpu", "н/д")
        bat_t = therm.get("mtktsbattery", "н/д")
        pmic_t = therm.get("mtktspmic", "н/д")
        text = f"Температура CPU: {cpu_t}°C, PMIC: {pmic_t}°C, Батарея: {bat_t}°C."
        return {
            "routed_to": "local_hardware_probe",
            "handled_locally": True,
            "response": text,
            "telemetry": therm
        }

    # Simple arithmetic
    m = re.match(r"^(?:посчитай|сколько будет|вычисли)?\s*([\d\s\+\-\*\/\(\)\.\^]+)$", p_lower)
    if m:
        expr = m.group(1).strip()
        calc_res = execute_local_tool("calc", {"expr": expr})
        if calc_res.get("success"):
            val = calc_res["data"]["result"]
            return {
                "routed_to": "local_fast_math",
                "handled_locally": True,
                "response": f"{expr} = {val}",
                "result": val
            }

    # Everything requiring reasoning delegates to the Big AI
    return {
        "routed_to": "big_ai_cluster",
        "handled_locally": False,
        "delegate_reason": "Cognitive reasoning, generative synthesis or code generation required",
        "query": prompt
    }

class EdgeRequestHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/", "/api/status"]:
            data = {
                "node_id": "NODE-3",
                "device_model": "Xiaomi Redmi Note 4 (nikel)",
                "soc": "MediaTek Helio X20 (MT6797) 10-core",
                "role": "Hardware Deck & Edge Probe for Big AI",
                "uptime_seconds": get_uptime(),
                "battery": get_battery_telemetry(),
                "thermal": get_cpu_thermal(),
                "ram": get_ram_info()
            }
            self._send_json(data)
        elif parsed.path == "/api/ping":
            self._send_json({"pong": True, "timestamp": time.time()})
        else:
            self._send_json({"error": "Not Found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8")
        try:
            req_data = json.loads(post_body) if post_body else {}
        except Exception:
            req_data = {}

        if parsed.path == "/api/exec":
            tool = req_data.get("tool", "")
            params = req_data.get("params", {})
            res = execute_local_tool(tool, params)
            self._send_json(res)
        elif parsed.path == "/api/query":
            prompt = req_data.get("prompt", "")
            res = route_intent(prompt)
            self._send_json(res)
        else:
            self._send_json({"error": "Unknown POST endpoint"}, 404)

def run():
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), EdgeRequestHandler)
    print(f"[EDGE NODE] Xiaomi Redmi Note 4 Edge Daemon running on port {PORT}...")
    server.serve_forever()

if __name__ == "__main__":
    run()
