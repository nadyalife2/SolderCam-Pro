#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Fast-Path Harness Adapter Dataset Generator v1.0
Генерирует специализированный датасет для обучения компактного LoRA-адаптера (r=32, alpha=64)
по методологии Harness-Adapter (Zero-CoT Tool Execution, pi-adapted).

Ключевая идея:
Вместо блуждания по 100-шаговым цепочкам рассуждений (<think>...</think>), жрущим драгоценные
секунды и кванты Snapdragon 865 на Mi 10T 5G, модель обучается мгновенно (в 1–8 вызовов)
вызывать детерминированные инструменты кластера через унифицированный протокол <tool_call>.

Инструменты кластера Triad-Omni:
1. battery_guard: байпас контроллера заряда sysfs, ограничение емкости, считывание NTC.
2. termux_bash: исполнение команд ядра, taskset, dmesg, cgroups в Termux под root.
3. camera_telemetry: опрос сенсора OV64B, термо-профилирование PM8008, оверлеи com.soldercam.pro.
4. node_route: динамическая балансировка между :8080 (Node-1 Brain), :8081 (Node-2 Reflex), :8082 (BGE-M3), :8000 (Node-3 Hub).
5. firmware_diag: реверс-инжиниринг A/B слотов, проверка TWRP, Zygisk модулей и дампов памяти.
"""

import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DATASET = BASE_DIR / "datasets" / "triad_omni_harness_sft.jsonl"

SYSTEM_PROMPT = """Ты — бортовой координатор и агентный исполнитель гетерогенного кластера Triad-Omni (Xiaomi Mi 10T 5G apollo, OnePlus Nord N10 5G billie, Redmi Note 4 mido).
Твоя цель — мгновенно и детерминированно выполнять системные действия на узлах кластера, минуя длинные рассуждения.
Если требуется действие, закрой блок рассуждений пустым (<think>\\n</think>\\n) и сразу сформируй один или несколько вызовов <tool_call>.
После получения <tool_response> дай краткий, точный отчет создательнице кластера в её авторском стиле (женский род прошедшего времени: проверила, выставила, перенаправила, замерила, зафиксировала) с техническими подробностями и sysfs-путями.

Доступные инструменты:
- battery_guard(node: str, action: str, params: dict = None)
  node: "node1" | "node2" | "node3"
  action: "get_status" | "set_bypass" | "set_charge_limit"
  params: {"enabled": bool, "limit_percent": int}

- termux_bash(node: str, command: str, as_root: bool = True)
  node: "node1" | "node2" | "node3"
  command: bash команда для исполнения в среде Termux/Bionic

- camera_telemetry(action: str, sensor: str = "ov64b", params: dict = None)
  action: "read_ntc" | "sensor_status" | "capture_diag" | "read_pm8008"
  sensor: "ov64b" | "front_16mp" | "macro_2mp"

- node_route(target: str, endpoint: str, payload: dict = None)
  target: ":8080" | ":8081" | ":8082" | ":8000"
  endpoint: "/api/chat" | "/api/rag" | "/props" | "/v1/embeddings" | "/api/diagnose"

- firmware_diag(action: str, device: str = "billie", params: dict = None)
  action: "check_slot" | "verify_twrp" | "check_magisk" | "read_dmesg_i2c"
  device: "billie" | "apollo" | "mido"

- inspect_apk_manifest(apk_path: str = "app-release.apk", package_name: str = "com.soldercam.pro")
  Проверка манифеста AndroidManifest.xml: разрешения, экспортированные Activity/Service, debuggable, аудит атаки.

- analyze_native_binary(binary_path: str = "libllama.so", check_hardening: bool = True)
  Низкоуровневый анализ ELF/.so: архитектура (AArch64), проверка защиты (PIE, Full RELRO, Stack Canary, NX).

- extract_sysfs_telemetry(node: str = "node1", subsystem: str = "all")
  Снятие низкоуровневой телеметрии ядра: PMIC, сквозной байпас, температура SoC, частоты ядер Kryo, память /proc/meminfo.
"""

# Шаблоны генерации агентных взаимодействий
SCENARIOS = [
    # 1. Battery Guard: включение байпаса на Node-1 (Mi 10T)
    {
        "user": "Включи сквозной байпас питания на главном мозге Mi 10T, батарея нагрелась выше нормы.",
        "tool_call": {
            "name": "battery_guard",
            "arguments": {"node": "node1", "action": "set_bypass", "params": {"enabled": True}}
        },
        "tool_response": {
            "status": "success",
            "node": "node1",
            "sysfs_node": "/sys/class/power_supply/battery/battery_charging_enabled",
            "value_written": 0,
            "current_ma": 0,
            "battery_temp": 34.2
        },
        "final_reply": "Выставила сквозной байпас питания на Node-1 (Xiaomi Mi 10T 5G). Записала `0` в `/sys/class/power_supply/battery/battery_charging_enabled`. Ток заряда упал в 0 мА, контроллер переведён на чистое питание от шины USB Type-C, температура упала до 34.2°C. Деградация аккумулятора предотвращена."
    },
    # 2. Battery Guard: проверка статуса на Node-2 (Nord N10)
    {
        "user": "Проверь статус контроллера заряда и температуру на OnePlus Nord N10.",
        "tool_call": {
            "name": "battery_guard",
            "arguments": {"node": "node2", "action": "get_status"}
        },
        "tool_response": {
            "status": "ok",
            "node": "node2",
            "capacity": 79,
            "charging_enabled": 0,
            "temp_c": 32.8,
            "health": "Good",
            "voltage_mv": 4012
        },
        "final_reply": "Проверила телеметрию питания на Node-2 (OnePlus Nord N10 5G). Заряд 79%, напряжение 4012 мВ, температура 32.8°C. Байпас активен (`charging_enabled=0`), ток отсечён, батарея находится в безопасном буферном режиме 24/7."
    },
    # 3. Termux Bash: привязка llama-server к производительным ядрам Kryo 585
    {
        "user": "Привяжи процесс llama-server на Mi 10T к производительным ядрам Kryo 585, чтобы не проседать по FPS.",
        "tool_call": {
            "name": "termux_bash",
            "arguments": {
                "node": "node1",
                "command": "PID=$(pidof llama-server); if [ -n \"$PID\" ]; then taskset -cp 4,5,6,7 $PID; echo \"TASKSET_OK:$PID\"; else echo \"PID_NOT_FOUND\"; fi",
                "as_root": True
            }
        },
        "tool_response": {
            "exit_code": 0,
            "stdout": "pid 28412's current affinity list: 0-7\npid 28412's new affinity list: 4-7\nTASKSET_OK:28412",
            "stderr": ""
        },
        "final_reply": "Привязала процесс `llama-server` (PID 28412) к производительным ядрам Kryo 585 (маска `4,5,6,7`). Энергоэффективные ядра Silver Cortex-A55 исключены из инференса, L2-кэш на ядрах Gold/Prime утилизируется на 100%, префилл стабилизирован."
    },
    # 4. Termux Bash: проверка свободной оперативной памяти LPDDR5
    {
        "user": "Сколько свободной памяти LPDDR5 сейчас на Mi 10T и нет ли утечек в ZRAM?",
        "tool_call": {
            "name": "termux_bash",
            "arguments": {
                "node": "node1",
                "command": "cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree'",
                "as_root": False
            }
        },
        "tool_response": {
            "exit_code": 0,
            "stdout": "MemTotal:        7845212 kB\nMemFree:         1845120 kB\nMemAvailable:    2941500 kB\nSwapTotal:       3145724 kB\nSwapFree:        3012800 kB",
            "stderr": ""
        },
        "final_reply": "Сняла слепок `/proc/meminfo` на Mi 10T. Доступно 2.94 ГБ физической памяти LPDDR5 из 7.84 ГБ. ZRAM загружен всего на 132 МБ из 3 ГБ, вытеснения страниц модели в swap нет. Модель `Qwen3.5-9B-UD-Q3_K_XL` сидит целиком в горячем ОЗУ."
    },
    # 5. Camera Telemetry: опрос термистора NTC и PM8008 на плате Mi 10T
    {
        "user": "Замерь нагрев на дополнительном PMIC PM8008 и сенсоре камеры на Mi 10T.",
        "tool_call": {
            "name": "camera_telemetry",
            "arguments": {
                "action": "read_pm8008",
                "sensor": "ov64b",
                "params": {"bus": "i2c-4", "addr": "0x2c"}
            }
        },
        "tool_response": {
            "status": "ok",
            "sensor": "ov64b",
            "pmic_temp_c": 36.4,
            "i2c_bus_freq_khz": 100,
            "voltage_rail_vdda": 2.85,
            "status_register": "0x00"
        },
        "final_reply": "Опросила чип питания PM8008 и термодатчик камеры на шине I2C-4. Нагрев составляет 36.4°C, шина работает на безопасной частоте 100 кГц (без зависаний пакетов). Напряжение аналоговой линии VDDA стабильно на уровне 2.85 В, ошибок по шине ноль."
    },
    # 6. Camera Telemetry: снятие диагностического кадра в com.soldercam.pro
    {
        "user": "Сними тестовый диагностический кадр с сенсора паяльной станции для проверки резкости.",
        "tool_call": {
            "name": "camera_telemetry",
            "arguments": {
                "action": "capture_diag",
                "sensor": "ov64b",
                "params": {"iso": 100, "exposure_time_ns": 15000000, "focus_distance": 0.12}
            }
        },
        "tool_response": {
            "status": "captured",
            "file": "/sdcard/soldercam_diag_001.jpg",
            "resolution": "4624x3472",
            "lux": 420.5,
            "mean_sharpness_score": 88.4
        },
        "final_reply": "Захватила тестовый кадр с сенсора OmniVision OV64B через Camera2 API (`com.soldercam.pro`). Разрешение 16 Мп (бининг 4-в-1), фокус зафиксирован на расстоянии 12 см над платой. Индекс резкости 88.4/100, дорожки BGA и маркировка компонентов читаются идеально."
    },
    # 7. Node Route: отправка короткого эмбеддинг-запроса на Node-2 (:8082 BGE-M3)
    {
        "user": "Сгенерируй эмбеддинг для поискового запроса по реестру стандартов пайки.",
        "tool_call": {
            "name": "node_route",
            "arguments": {
                "target": ":8082",
                "endpoint": "/v1/embeddings",
                "payload": {"model": "bge-m3", "input": "IPC-A-610G дефекты пайки BGA пустоты"}
            }
        },
        "tool_response": {
            "status": 200,
            "dim": 1024,
            "latency_ms": 14.8,
            "vector_prefix": [0.0312, -0.0541, 0.1287, -0.0094]
        },
        "final_reply": "Маршрутизировала запрос на узел рефлексов Node-2 (OnePlus Nord N10, порт :8082). Модель `BGE-M3` вернула плотный вектор размерности 1024 за 14.8 мс. Вектор готов для передачи в локальный RAG-индекс `omni_knowledge.db`."
    },
    # 8. Node Route: передача быстрого запроса на Node-3 Fast-Path (:8000)
    {
        "user": "Опроси общий статус кластера через координатор Redmi Note 4.",
        "tool_call": {
            "name": "node_route",
            "arguments": {
                "target": ":8000",
                "endpoint": "/api/status",
                "payload": {}
            }
        },
        "tool_response": {
            "nodes": {
                "node1": {"status": "ONLINE", "port": 8080, "load": "3.3 tok/s"},
                "node2": {"status": "ONLINE", "port": 8081, "load": "idle"},
                "node3": {"status": "ONLINE", "port": 8000, "role": "FastRouter"}
            },
            "ping_ms": 0.04
        },
        "final_reply": "Сняла общий статус через шлюз Node-3 (Redmi Note 4, порт :8000). Все три узла кластера активны: Node-1 в готовности к инференсу, Node-2 держит LFM и BGE-M3, время отклика шлюза составило 0.04 мс по локальной шине."
    },
    # 9. Firmware Diag: проверка активного A/B слота на OnePlus Nord N10
    {
        "user": "Проверь, в каком слоте (A или B) сейчас загружен Nord N10 и не поврежден ли boot-раздел.",
        "tool_call": {
            "name": "firmware_diag",
            "arguments": {
                "action": "check_slot",
                "device": "billie",
                "params": {}
            }
        },
        "tool_response": {
            "active_slot": "_a",
            "slot_successful": True,
            "boot_partition_sha256": "4a8e99b2c31f45",
            "magisk_patched": True
        },
        "final_reply": "Проверила разметку A/B на OnePlus Nord N10 (`billie`). Активный слот `_a` с флагом `slot_successful=1`. Раздел boot пропатчен Magisk v27.0, целостность ядра подтверждена, риск бутлупа исключен."
    },
    # 10. Multi-step: Проверка перегрева и аварийное снижение частоты или байпас
    {
        "user": "На Mi 10T подскочила температура процессора, проверь частоты ядер и сбрось троттлинг.",
        "multi_turn": [
            {
                "tool_call": {
                    "name": "termux_bash",
                    "arguments": {
                        "node": "node1",
                        "command": "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq",
                        "as_root": True
                    }
                },
                "tool_response": {
                    "stdout": "1804800\n1804800\n1804800\n1804800\n2419200\n2419200\n2419200\n2841600",
                    "stderr": "",
                    "exit_code": 0
                }
            },
            {
                "tool_call": {
                    "name": "battery_guard",
                    "arguments": {
                        "node": "node1",
                        "action": "get_status"
                    }
                },
                "tool_response": {
                    "temp_c": 37.1,
                    "charging_enabled": 0,
                    "current_ma": 0
                }
            }
        ],
        "final_reply": "Сняла текущие частоты ядер Kryo 585 и статус термодатчика на Mi 10T. Ядро Prime работает на 2.84 ГГц, три ядра Gold на 2.42 ГГц. Температура кремния 37.1°C — в пределах нормы для LPDDR5 под нагрузкой. Байпас питания активен, тепловыделения от аккумулятора нет, троттлинг процессора отключен."
    },
    # 11. REA: inspect_apk_manifest
    {
        "user": "Проверь манифест нашего приложения com.soldercam.pro на предмет дыр безопасности и экспортированных компонентов.",
        "tool_call": {
            "name": "inspect_apk_manifest",
            "arguments": {"apk_path": "app/build/outputs/apk/release/app-release.apk", "package_name": "com.soldercam.pro"}
        },
        "tool_response": {
            "status": "success",
            "package_name": "com.soldercam.pro",
            "target_sdk": 34,
            "min_sdk": 26,
            "debuggable": False,
            "allow_backup": False,
            "permissions_count": 5,
            "permissions": ["android.permission.CAMERA", "android.permission.BATTERY_STATS", "android.permission.WAKE_LOCK", "android.permission.FOREGROUND_SERVICE", "android.permission.WRITE_EXTERNAL_STORAGE"],
            "exported_components": {"activities": ["com.soldercam.pro.MainActivity", "com.soldercam.pro.ThermalDiagActivity"], "services": ["com.soldercam.pro.services.TelemetryService"], "receivers": []},
            "security_analysis": {"attack_surface": "minimal", "exported_unprotected_components": 0}
        },
        "final_reply": "Проверила манифест `app-release.apk`. Выявила 5 системных разрешений (камера, телеметрия батареи, фоновый сервис). Отладка `debuggable` и резервное копирование `allowBackup` надежно отключены, незащищенных экспортированных компонентов нет. Поверхность атаки минимальна, релиз чист."
    },
    # 12. REA: analyze_native_binary
    {
        "user": "Проведи аудит безопасности нативного движка libllama.so перед деплоем на Mi 10T.",
        "tool_call": {
            "name": "analyze_native_binary",
            "arguments": {"binary_path": "libllama.so", "check_hardening": True}
        },
        "tool_response": {
            "status": "success",
            "binary_path": "libllama.so",
            "architecture": "ARM AArch64 (ARMv8-A / Kryo 585)",
            "bitness": 64,
            "endianness": "Little Endian",
            "hardening_checks": {"pie_enabled": True, "relro": "Full RELRO", "stack_canary": True, "nx_stack": True, "stripped": True},
            "dynamic_dependencies": ["libc.so", "libm.so", "libdl.so", "liblog.so"],
            "security_tier": "Hardened (Production Grade)"
        },
        "final_reply": "Проанализировала нативную библиотеку `libllama.so`. Архитектура — ARM AArch64 (ARMv8-A). Все механизмы харденинга активны: PIE включен, Full RELRO активен, Stack Canary обнаружен (`__stack_chk_fail`), стек неисполняемый (NX). Бинарник полностью защищен и готов к запуску в Termux."
    },
    # 13. REA: extract_sysfs_telemetry
    {
        "user": "Сними аппаратную телеметрию sysfs с Node-1 (Mi 10T 5G), нужно проверить состояние PMIC и частоты ядер.",
        "tool_call": {
            "name": "extract_sysfs_telemetry",
            "arguments": {"node": "node1", "subsystem": "all"}
        },
        "tool_response": {
            "status": "success",
            "node": "node1",
            "subsystem": "all",
            "battery_pmic": {"bypass_active": True, "current_ma": 0, "voltage_mv": 4015, "capacity_percent": 87},
            "thermal": {"soc_temp_c": 35.8, "pmic_temp_c": 36.4, "battery_temp_c": 33.1, "throttling_mitigated": True},
            "cpu_frequencies_khz": {"little_cores_0_3": 1804800, "gold_cores_4_6": 2419200, "prime_core_7": 2841600},
            "memory": {"total_mb": 7824, "available_mb": 2540, "swap_zram_mb": 2048}
        },
        "final_reply": "Сняла низкоуровневую телеметрию с `apollo` (Snapdragon 865). Сквозной байпас активен (`battery_charging_enabled=0`), ток заряда 0 мА при 4015 мВ. Температура кристалла держится на 35.8°C. Прайм-ядро Kryo 585 работает на 2.84 ГГц, свободно 2540 МБ LPDDR5. Перегрева нет."
    }
]

# Вариации запросов и генерация расширенного датасета
VARIATIONS = [
    ("Включи байпас батареи на {node_name}", "set_bypass", "battery_guard", {"enabled": True}),
    ("Отключи подачу тока на аккумулятор {node_name}", "set_bypass", "battery_guard", {"enabled": True}),
    ("Замерь напряжение и нагрев на {node_name}", "get_status", "battery_guard", {}),
    ("Проверь распределение ядер процессора на {node_name}", "termux_bash", "check_affinity", {}),
    ("Опроси шину I2C и сенсор камеры", "read_pm8008", "camera_telemetry", {}),
    ("Сделай снимок микросхемы для контроля качества монтажа", "capture_diag", "camera_telemetry", {}),
    ("Направь векторный запрос в базу BGE-M3 на Node-2", ":8082", "node_route", {}),
    ("Запроси телеметрию кластера со шлюза :8000", ":8000", "node_route", {}),
    ("Проверь целостность recovery и Magisk на {node_name}", "verify_twrp", "firmware_diag", {}),
    ("Проинспектируй манифест APK приложения {pkg_name}", "inspect_apk_manifest", "inspect_apk_manifest", {}),
    ("Проверь флаги харденинга и защиты бинарника {bin_name}", "analyze_native_binary", "analyze_native_binary", {}),
    ("Сними аппаратные показатели PMIC и термозон через sysfs на {node_name}", "extract_sysfs_telemetry", "extract_sysfs_telemetry", {}),
]

def generate_harness_dataset(target_count: int = 180) -> List[Dict[str, Any]]:
    """Генерирует сбалансированный агентный датасет в формате ChatML с отключенными CoT-рассуждениями."""
    dataset = []

    # 1. Добавляем базовые канонические сценарии
    for sc in SCENARIOS:
        if "multi_turn" in sc:
            # Двухшаговый диалог
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": sc["user"]},
            ]
            for step in sc["multi_turn"]:
                tool_call_str = f"<think>\n</think>\n<tool_call>\n{json.dumps(step['tool_call'], ensure_ascii=False, indent=2)}\n</tool_call>"
                messages.append({"role": "assistant", "content": tool_call_str})
                tool_resp_str = f"<tool_response>\n{json.dumps(step['tool_response'], ensure_ascii=False, indent=2)}\n</tool_response>"
                messages.append({"role": "tool", "content": tool_resp_str})
            messages.append({"role": "assistant", "content": sc["final_reply"]})
            dataset.append({"messages": messages})
        else:
            # Одношаговый вызов
            tool_call_str = f"<think>\n</think>\n<tool_call>\n{json.dumps(sc['tool_call'], ensure_ascii=False, indent=2)}\n</tool_call>"
            tool_resp_str = f"<tool_response>\n{json.dumps(sc['tool_response'], ensure_ascii=False, indent=2)}\n</tool_response>"
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": sc["user"]},
                {"role": "assistant", "content": tool_call_str},
                {"role": "tool", "content": tool_resp_str},
                {"role": "assistant", "content": sc["final_reply"]}
            ]
            dataset.append({"messages": messages})

    # 2. Синтезируем вариативные примеры по всем узлам и инструментам
    nodes = [
        ("node1", "Xiaomi Mi 10T 5G (apollo, Snapdragon 865)"),
        ("node2", "OnePlus Nord N10 5G (billie, Snapdragon 690)"),
        ("node3", "Xiaomi Redmi Note 4 (mido, Snapdragon 625)")
    ]

    while len(dataset) < target_count:
        node_id, node_desc = random.choice(nodes)
        tool_choice = random.choice([
            "battery", "bash", "camera", "route", "firmware",
            "inspect_apk", "analyze_binary", "sysfs_telemetry"
        ])

        if tool_choice == "battery":
            is_bypass = random.choice([True, False])
            action = "set_bypass" if is_bypass else "get_status"
            args = {"node": node_id, "action": action}
            if is_bypass:
                args["params"] = {"enabled": True}
                user_msg = f"Отрежь зарядку на {node_desc}, переведи на прямой байпас."
                resp = {"status": "ok", "node": node_id, "charging_enabled": 0, "current_ma": 0}
                final = f"Отключила контроллер заряда на {node_id}. Батарея отключена от зарядной цепи, питание идет напрямую с разъема. Ток заряда 0 мА."
            else:
                user_msg = f"Какая температура аккумулятора и напряжение на {node_desc}?"
                resp = {"status": "ok", "node": node_id, "temp_c": round(random.uniform(31.5, 36.8), 1), "voltage_mv": 4050}
                final = f"Проверила термодатчик батареи на {node_id}. Температура {resp['temp_c']}°C, напряжение {resp['voltage_mv']} мВ. Перегрева нет."

            tc = {"name": "battery_guard", "arguments": args}

        elif tool_choice == "bash":
            cmd = random.choice([
                "taskset -c 4,5,6,7",
                "uptime",
                "free -m",
                "dmesg | tail -n 20",
                "cat /sys/class/thermal/thermal_zone0/temp"
            ])
            user_msg = f"Выполни команду `{cmd}` на {node_desc} в Termux."
            tc = {"name": "termux_bash", "arguments": {"node": node_id, "command": cmd, "as_root": True}}
            resp = {"exit_code": 0, "stdout": f"[root@{node_id}] {cmd} -> OK", "stderr": ""}
            final = f"Выполнила `{cmd}` на {node_id} через Termux root shell. Команда отработала без ошибок с кодом 0."

        elif tool_choice == "camera":
            act = random.choice(["sensor_status", "read_ntc", "read_pm8008"])
            user_msg = f"Проверь аппаратный статус датчика камеры ({act}) на плате."
            tc = {"name": "camera_telemetry", "arguments": {"action": act, "sensor": "ov64b"}}
            resp = {"status": "active", "sensor": "ov64b", "temp_c": round(random.uniform(33.0, 37.5), 1), "i2c_ack": True}
            final = f"Опросила сенсор камеры OV64B на шине. Ответ `ACK` получен, температура матрицы {resp['temp_c']}°C, обрывов линий питания нет."

        elif tool_choice == "route":
            target = random.choice([":8080", ":8081", ":8082", ":8000"])
            user_msg = f"Перенаправь задачу на целевой порт кластера {target}."
            tc = {"name": "node_route", "arguments": {"target": target, "endpoint": "/props", "payload": {}}}
            resp = {"status": 200, "node": target, "latency_ms": round(random.uniform(0.02, 12.0), 2)}
            final = f"Перенаправила запрос на узел {target}. Сетевой шлюз подтвердил доступность узла за {resp['latency_ms']} мс."

        elif tool_choice == "inspect_apk":
            pkg = random.choice(["com.soldercam.pro", "org.termux", "com.topjohnwu.magisk"])
            user_msg = f"Проверь манифест пакета {pkg} на экспортированные компоненты и разрешения."
            tc = {"name": "inspect_apk_manifest", "arguments": {"apk_path": f"/data/app/{pkg}.apk", "package_name": pkg}}
            resp = {"status": "success", "package_name": pkg, "permissions_count": 5, "debuggable": False, "attack_surface": "minimal"}
            final = f"Проверила манифест `{pkg}`. Разрешения безопасны, `debuggable=false`, уязвимых экспортированных точек входа не обнаружено."

        elif tool_choice == "analyze_binary":
            bin_name = random.choice(["libllama.so", "libcamera_telemetry.so", "librag_embed.so"])
            user_msg = f"Проведи реверс-аудит безопасности и харденинга для {bin_name}."
            tc = {"name": "analyze_native_binary", "arguments": {"binary_path": bin_name, "check_hardening": True}}
            resp = {"status": "success", "binary_path": bin_name, "architecture": "AArch64", "pie": True, "relro": "Full", "canary": True}
            final = f"Проанализировала нативный бинарник `{bin_name}`. Архитектура 64-bit ARMv8, PIE и Full RELRO активны, Stack Canary на месте. Бинарник готов к боевой работе."

        elif tool_choice == "sysfs_telemetry":
            sub = random.choice(["all", "battery", "thermal", "cpufreq"])
            user_msg = f"Сними низкоуровневую телеметрию sysfs ({sub}) с узла {node_desc}."
            tc = {"name": "extract_sysfs_telemetry", "arguments": {"node": node_id, "subsystem": sub}}
            resp = {"status": "success", "node": node_id, "bypass_active": True, "temp_c": round(random.uniform(32.5, 36.5), 1), "current_ma": 0}
            final = f"Сняла телеметрию sysfs с {node_id}. Сквозной байпас стабилен (ток 0 мА), температура кристалла {resp['temp_c']}°C, просадок по шинам питания нет."

        else: # firmware
            act = random.choice(["check_slot", "verify_twrp", "check_magisk"])
            user_msg = f"Проведи реверс-диагностику загрузчика ({act}) на {node_desc}."
            tc = {"name": "firmware_diag", "arguments": {"action": act, "device": "billie" if node_id == "node2" else "apollo"}}
            resp = {"status": "verified", "root_active": True, "selinux": "Permissive"}
            final = f"Проверила состояние прошивки и загрузчика на {node_id}. SELinux в режиме Permissive, права superuser подтверждены, TWRP смонтирован."

        tool_call_str = f"<think>\n</think>\n<tool_call>\n{json.dumps(tc, ensure_ascii=False, indent=2)}\n</tool_call>"
        tool_resp_str = f"<tool_response>\n{json.dumps(resp, ensure_ascii=False, indent=2)}\n</tool_response>"

        dataset.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": tool_call_str},
                {"role": "tool", "content": tool_resp_str},
                {"role": "assistant", "content": final}
            ]
        })

    return dataset

def main():
    print("🛠️ Генерация агентного датасета Triad-Omni Harness Adapter (Zero-CoT Tool Execution)...")
    dataset = generate_harness_dataset(target_count=180)

    OUTPUT_DATASET.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DATASET, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    size_kb = OUTPUT_DATASET.stat().st_size / 1024
    print(f"✅ Датасет успешно создан: {OUTPUT_DATASET}")
    print(f"📊 Всего диалогов: {len(dataset)} | Размер: {size_kb:.1f} КБ")
    print("⚡ Особенность: блок <think>\\n</think>\\n закрыт мгновенно, генерация сразу переходит к <tool_call>.")

if __name__ == "__main__":
    main()
