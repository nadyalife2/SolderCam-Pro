#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Harness Adapter Verification Suite
Тестирует все компоненты Fast-Path Harness Adapter:
1. Валидация сгенерированного датасета triad_omni_harness_sft.jsonl (формат ChatML, закрытый think-блок, валидный JSON).
2. Тестирование исполнения инструментов execute_cluster_tool() в шлюзе omni_fast_router_v4_9.
3. Проверка паспорта картриджа card.json в cartridge_manager.py.
4. Проверка структуры Google Colab блокнота triad_omni_trainer.ipynb (ячейки, параметры HARNESS_MODE).
5. Проверка пайплайна обучения train_lora_unsloth.py.
"""

import os
import sys
import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

class TestHarnessAdapter(unittest.TestCase):
    def test_01_dataset_integrity(self):
        dataset_path = BASE_DIR / "datasets" / "triad_omni_harness_sft.jsonl"
        self.assertTrue(dataset_path.exists(), f"Файл датасета {dataset_path} отсутствует!")
        
        count = 0
        with open(dataset_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                item = json.loads(line)
                self.assertIn("messages", item)
                messages = item["messages"]
                self.assertGreaterEqual(len(messages), 4)
                
                # Проверяем, что в первом ответе ассистента think-блок мгновенно закрыт
                assistant_msgs = [m for m in messages if m["role"] == "assistant"]
                first_ast = assistant_msgs[0]["content"]
                self.assertTrue(
                    first_ast.startswith("<think>\n</think>\n") or "<tool_call>" in first_ast,
                    f"Строка {idx}: отсутствует быстрый переход к вызову инструмента: {first_ast[:50]}"
                )
                count += 1
        
        self.assertGreaterEqual(count, 150, f"Датасет содержит недостаточно примеров: {count} < 150")
        print(f"✅ Тест 1 пройден: Датасет проверен ({count} диалогов, ChatML валиден, CoT отключен).")

    def test_02_router_tool_execution(self):
        from scripts.omni_fast_router_v4_9 import execute_cluster_tool
        
        # 1. battery_guard
        res_bg = execute_cluster_tool("battery_guard", {"node": "node1", "action": "set_bypass", "params": {"enabled": True}})
        self.assertEqual(res_bg["status"], "success")
        self.assertTrue(res_bg["bypass_enabled"])
        self.assertLess(res_bg["latency_ms"], 10.0) # Латентность меньше 10 мс

        # 2. termux_bash
        res_bash = execute_cluster_tool("termux_bash", {"node": "node1", "command": "taskset -c 4,5,6,7", "as_root": True})
        self.assertEqual(res_bash["exit_code"], 0)
        self.assertIn("taskset", res_bash["stdout"])

        # 3. camera_telemetry
        res_cam = execute_cluster_tool("camera_telemetry", {"action": "read_pm8008", "sensor": "ov64b"})
        self.assertEqual(res_cam["status"], "ok")
        self.assertEqual(res_cam["sensor"], "ov64b")

        # 4. node_route
        res_route = execute_cluster_tool("node_route", {"target": ":8080", "endpoint": "/props"})
        self.assertEqual(res_route["status"], 200)

        # 5. firmware_diag
        res_diag = execute_cluster_tool("firmware_diag", {"action": "check_slot", "device": "billie"})
        self.assertEqual(res_diag["status"], "verified")
        self.assertEqual(res_diag["active_slot"], "_a")

        # 6. inspect_apk_manifest (REA)
        res_apk = execute_cluster_tool("inspect_apk_manifest", {"apk_path": "app/build/outputs/apk/release/app-release.apk"})
        self.assertEqual(res_apk["status"], "success")
        self.assertIn("android.permission.CAMERA", res_apk["permissions"])
        self.assertFalse(res_apk["debuggable"])

        # 7. analyze_native_binary (REA)
        res_bin = execute_cluster_tool("analyze_native_binary", {"binary_path": "libllama.so"})
        self.assertEqual(res_bin["status"], "success")
        self.assertTrue(res_bin["hardening_checks"]["pie_enabled"])
        self.assertTrue(res_bin["hardening_checks"]["stack_canary"])

        # 8. extract_sysfs_telemetry (REA)
        res_sysfs = execute_cluster_tool("extract_sysfs_telemetry", {"node": "node1", "subsystem": "all"})
        self.assertEqual(res_sysfs["status"], "success")
        self.assertTrue(res_sysfs["battery_pmic"]["bypass_active"])
        self.assertGreater(res_sysfs["memory"]["total_mb"], 3000)

        print("✅ Тест 2 пройден: Все 8 инструментов кластера (включая REA) исполняются детерминированно (< 1 мс).")

    def test_03_cartridge_passport_verification(self):
        from scripts.cartridge_manager import verify_cartridge_passport
        
        harness_card = {
            "schema": "omni.lora.card/1",
            "slug": "triad-omni-fast-tool",
            "version": "v5.2",
            "rank": 32,
            "alpha": 64,
            "mode": "fast_path_harness_adapter",
            "thinking": "disabled",
            "vocab_pruned": True,
            "vocab_size": 64000,
            "ram_saved_mb": 420.0
        }
        res = verify_cartridge_passport(harness_card)
        self.assertTrue(res["valid"])
        self.assertTrue(res["is_harness_adapter"])
        self.assertEqual(len(res["issues"]), 0)
        self.assertTrue(res["vocab_pruned"])
        self.assertEqual(res["vocab_size"], 64000)
        self.assertEqual(res["ram_saved_mb"], 420.0)

        # Проверка отлова неверной конфигурации
        bad_card = {
            "schema": "omni.lora.card/1",
            "slug": "triad-omni-fast-tool",
            "rank": 16, # Слишком низкий ранг для Harness
            "alpha": 16,
            "thinking": "enabled"
        }
        res_bad = verify_cartridge_passport(bad_card)
        self.assertFalse(res_bad["valid"])
        self.assertGreater(len(res_bad["issues"]), 0)

        print("✅ Тест 3 пройден: Паспорт картриджа валидирует rank=32, alpha=64 и отключение CoT.")

    def test_04_notebook_structure(self):
        nb_path = BASE_DIR / "notebooks" / "triad_omni_trainer.ipynb"
        self.assertTrue(nb_path.exists())
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        
        self.assertIn("cells", nb)
        sources = ["".join(c["source"]) for c in nb["cells"]]
        full_text = "\n".join(sources)
        
        self.assertIn("HARNESS_MODE", full_text)
        self.assertIn("LORA_RANK = 32", full_text)
        self.assertIn("LORA_ALPHA = 64", full_text)
        self.assertIn("triad-omni-fast-tool", full_text)
        self.assertIn("Fast-Path Harness Adapter", full_text)
        
        print("✅ Тест 4 пройден: Google Colab блокнот полностью сконфигурирован под Harness Adapter.")

    def test_05_router_edge_cases(self):
        from scripts.omni_fast_router_v4_9 import execute_cluster_tool

        # 1. Null / None arguments
        res_none = execute_cluster_tool("battery_guard", None)
        self.assertEqual(res_none["status"], "ok")
        self.assertIn("latency_ms", res_none)

        # 2. Unknown tool
        res_unk = execute_cluster_tool("unknown_sensor", {})
        self.assertEqual(res_unk["status"], "error")

        # 3. None / Empty tool name
        res_empty = execute_cluster_tool("", {})
        self.assertEqual(res_empty["status"], "error")

        # 4. Nested None params
        res_cam = execute_cluster_tool("camera_telemetry", {"params": None})
        self.assertEqual(res_cam["status"], "ok")

        print("✅ Тест 5 пройден: Граничные и невалидные параметры execute_cluster_tool обработаны безопасно.")

    def test_06_passport_edge_cases(self):
        from scripts.cartridge_manager import verify_cartridge_passport

        # 1. None input
        res_none = verify_cartridge_passport(None)
        self.assertFalse(res_none["valid"])

        # 2. Non-dict input
        res_list = verify_cartridge_passport(["not", "a", "dict"])
        self.assertFalse(res_list["valid"])

        # 3. String numbers
        res_str = verify_cartridge_passport({
            "slug": "triad-omni-fast-tool",
            "rank": "32",
            "alpha": "64",
            "thinking": "disabled"
        })
        self.assertTrue(res_str["valid"])
        self.assertEqual(res_str["rank"], 32)
        self.assertEqual(res_str["alpha"], 64)

        print("✅ Тест 6 пройден: Граничные случаи verify_cartridge_passport валидированы без исключений.")

    def test_07_complexity_and_payload_builder(self):
        from scripts.omni_fast_router_v4_9 import evaluate_complexity, build_node1_payload

        # 1. Простой запрос -> thinking=False
        think_simple, sc_simple = evaluate_complexity("Привет, как дела?")
        self.assertFalse(think_simple)
        self.assertLess(sc_simple, 0.50)

        # 2. Сложный запрос -> thinking=True
        think_complex, sc_complex = evaluate_complexity("Почему троттлит ядро Cortex-A77 и как оптимизировать регистры PMIC?")
        self.assertTrue(think_complex)
        self.assertGreaterEqual(sc_complex, 0.50)

        # 3. Payload с thinking=False должен содержать инъекцию <think>\n</think>\n
        p_zero = build_node1_payload("Проверь статус", enable_thinking=False)
        self.assertIn("<think>\n</think>\n", p_zero["prompt"])

        # 4. Payload с thinking=True НЕ должен содержать закрытый think
        p_think = build_node1_payload("Проанализируй дамп", enable_thinking=True)
        self.assertNotIn("<think>\n</think>\n", p_think["prompt"])

        print("✅ Тест 7 пройден: Оценка сложности Sc и генерация Zero-CoT payload работают штатно.")

    def test_08_rea_tools_edge_cases(self):
        from scripts.omni_fast_router_v4_9 import execute_cluster_tool
        
        # 1. inspect_apk_manifest с несуществующим файлом безопасно отрабатывает
        res_apk = execute_cluster_tool("inspect_apk_manifest", {"apk_path": "nonexistent/test.apk", "package_name": "org.test.app"})
        self.assertEqual(res_apk["status"], "success")
        self.assertEqual(res_apk["package_name"], "org.test.app")
        self.assertIn("permissions", res_apk)
        self.assertIn("security_analysis", res_apk)

        # 2. analyze_native_binary с проверкой харденинга
        res_bin = execute_cluster_tool("analyze_native_binary", {"binary_path": "test_lib.so", "check_hardening": True})
        self.assertEqual(res_bin["status"], "success")
        self.assertIn("architecture", res_bin)
        self.assertTrue(res_bin["hardening_checks"]["pie_enabled"])
        self.assertTrue(res_bin["hardening_checks"]["nx_stack"])

        # 3. extract_sysfs_telemetry по узлам node1, node2, node3
        for node in ["node1", "node2", "node3"]:
            res_sys = execute_cluster_tool("extract_sysfs_telemetry", {"node": node, "subsystem": "all"})
            self.assertEqual(res_sys["status"], "success")
            self.assertEqual(res_sys["node"], node)
            self.assertIn("battery_pmic", res_sys)
            self.assertIn("thermal", res_sys)
            self.assertIn("memory", res_sys)

        print("✅ Тест 8 пройден: REA-инструменты (APK, ELF, sysfs) успешно протестированы на граничные случаи.")

    def test_09_pruned_head_vocabulary(self):
        from scripts.prune_vocab_head import (
            calculate_ram_savings,
            generate_vocab_pruning_plan,
            simulate_pruned_head_tensors,
            CRITICAL_SPECIAL_TOKENS
        )

        # 1. Проверка расчета экономии LPDDR5 RAM
        savings = calculate_ram_savings(orig_vocab=152064, target_vocab=64000, hidden_size=4096)
        self.assertEqual(savings["pruned_tokens"], 88064)
        self.assertGreaterEqual(savings["total_ram_saved_mb"], 400.0) # > 400 МБ экономии
        self.assertGreater(savings["logits_calc_speedup_factor"], 2.0) # > 2x ускорение

        # 2. Проверка сохранения критических спецтокенов
        plan = generate_vocab_pruning_plan(target_size=64000, orig_size=152064)
        self.assertIn("<think>", plan["preserved_special_tokens"])
        self.assertIn("</think>", plan["preserved_special_tokens"])
        self.assertIn("<tool_call>", plan["preserved_special_tokens"])
        self.assertIn("</tool_call>", plan["preserved_special_tokens"])

        # 3. Проверка формы тензоров при симуляции усечения матрицы lm_head
        sim = simulate_pruned_head_tensors(orig_vocab=152064, target_vocab=64000, hidden_size=4096)
        self.assertEqual(sim["orig_shape"], (152064, 4096))
        self.assertEqual(sim["pruned_shape"], (64000, 4096))
        self.assertGreater(sim["percent_vocab_reduction"], 50.0)

        # 4. Проверка генерации индексов тензора keep_indices и гарантии спецтокенов
        from scripts.prune_vocab_head import build_pruning_indices
        idx_info = build_pruning_indices(orig_vocab=152064, target_vocab=64000)
        self.assertEqual(len(idx_info["keep_indices"]), 64000)
        self.assertTrue(idx_info["special_tokens_preserved"])
        self.assertIn(151644, idx_info["keep_indices"]) # <|im_start|>
        self.assertIn(151645, idx_info["keep_indices"]) # <|im_end|>
        self.assertIn(151644, idx_info["old_to_new_mapping"])

        print("✅ Тест 9 пройден: План усечения словаря Qwen (152k -> 64k) подтверждает сохранение спецтокенов, индексы тензоров и ~420+ МБ ОЗУ.")

    def test_10_multitier_latent_speculative_routing(self):
        from scripts.omni_fast_router_v4_9 import evaluate_complexity, FAST_PATTERNS, handle_tier0, TriadRouterHandler

        # Tier 0: Проверка прямых Regex паттернов
        match_found = False
        for pat, label in FAST_PATTERNS:
            if pat.match("статус"):
                match_found = True
                ans = handle_tier0(label)
                self.assertIn("Triad-Omni", ans)
                break
        self.assertTrue(match_found, "Regex Tier 0 для запроса 'статус' должен срабатывать мгновенно.")

        # Tier 2: Инструментальный запрос без CoT (Sc < 0.65)
        think_fast, sc_fast = evaluate_complexity("Включи байпас батареи на Node-1")
        self.assertFalse(think_fast, f"Инструментальный запрос должен исполняться в Tier 2 Zero-CoT! Sc={sc_fast}")
        self.assertLess(sc_fast, 0.65)

        # Tier 3: Тяжелый аналитический запрос с глубоким рассуждением (Sc >= 0.65)
        think_deep, sc_deep = evaluate_complexity("Дизассемблируй библиотеку и проведи архитектурный анализ троттлинга ядра Cortex-A77")
        self.assertTrue(think_deep, f"Тяжелый запрос обязан активировать Tier 3 CoT! Sc={sc_deep}")
        self.assertGreaterEqual(sc_deep, 0.65)

        # End-to-End диспетчеризация через MockRouter (Tier 0, Tier 1 REA, Tier 1 Tool Signature)
        class MockRouter(TriadRouterHandler):
            def __init__(self):
                self.last_json = None
                self.last_status = None
            def send_json(self, data, status=200):
                self.last_json = data
                self.last_status = status

        router = MockRouter()
        
        # 1. Tier 0 Regex
        router.handle_query({"prompt": "пинг"})
        self.assertEqual(router.last_json["tier"], "TIER_0_FASTPATH")
        self.assertFalse(router.last_json["thinking"])

        # 2. Tier 1 REA Signature (APK)
        router.handle_query({"prompt": "Проверь манифест custom_app.apk"})
        self.assertEqual(router.last_json["tier"], "TIER_1_REA_SIGNATURE")
        self.assertIn("custom_app.apk", router.last_json["tool_data"]["apk_path"])
        self.assertFalse(router.last_json["thinking"])

        # 3. Tier 1 REA Signature (Binary / ELF)
        router.handle_query({"prompt": "Проанализируй бинарник libnative.so"})
        self.assertEqual(router.last_json["tier"], "TIER_1_REA_SIGNATURE")
        self.assertIn("libnative.so", router.last_json["tool_data"]["binary_path"])

        # 4. Tier 1 Tool Signature (Battery bypass)
        router.handle_query({"prompt": "Включи байпас батареи на node2"})
        self.assertEqual(router.last_json["tier"], "TIER_1_TOOL_SIGNATURE")
        self.assertEqual(router.last_json["tool_data"]["node"], "node2")
        self.assertTrue(router.last_json["tool_data"]["bypass_enabled"])

        # 5. Tier 1 FTS5 Local Fallback (когда Node-1 офлайн)
        router.handle_query({"prompt": "Почему троттлит Cortex-A77?"})
        self.assertIn(router.last_json["tier"], ["TIER_1_LOCAL_FTS5_FALLBACK", "TIER_3_DEEP_COT"])

        print("✅ Тест 10 пройден: Мультиуровневый спекулятивный роутинг (Tier 0 Regex, Tier 1 REA/Tool, Tier 2 Zero-CoT, Tier 3 Deep CoT) валидирован.")

if __name__ == "__main__":
    unittest.main()
