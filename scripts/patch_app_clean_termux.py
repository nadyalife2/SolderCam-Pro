#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch Android layout and activities to add Termux Clean Decommission controls.
"""

from pathlib import Path

def patch_battery_layout():
    p = Path("app/src/main/res/layout/activity_battery_diagnostics.xml")
    text = p.read_text(encoding="utf-8")
    target = "<!-- RECOMMENDATIONS -->"
    btn_xml = """        <!-- TERMUX DECOMMISSION & CLEAN BUTTON -->
        <com.google.android.material.button.MaterialButton
            android:id="@+id/btnCleanTermux"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="16dp"
            android:backgroundTint="#D32F2F"
            android:text="🧹 Отключить Termux &amp; Очистить узел"
            android:textColor="#FFFFFF"
            app:cornerRadius="8dp" />

"""
    if target in text and "btnCleanTermux" not in text:
        text = text.replace(target, btn_xml + "        " + target)
        p.write_text(text, encoding="utf-8")
        print("✅ Added btnCleanTermux to activity_battery_diagnostics.xml")

def patch_battery_activity():
    p = Path("app/src/main/java/com/soldercam/pro/BatteryDiagnosticsActivity.kt")
    text = p.read_text(encoding="utf-8")
    target = "binding.btnShareLog.setOnClickListener {"
    listener_code = """        binding.btnCleanTermux.setOnClickListener {
            ClusterNodeManager.showCleanTermuxDialog(this)
        }

        binding.btnShareLog.setOnClickListener {"""
    if target in text and "btnCleanTermux" not in text:
        text = text.replace(target, listener_code, 1)
        p.write_text(text, encoding="utf-8")
        print("✅ Added btnCleanTermux listener in BatteryDiagnosticsActivity.kt")

def patch_main_activity():
    p = Path("app/src/main/java/com/soldercam/pro/MainActivity.kt")
    text = p.read_text(encoding="utf-8")
    target = "binding.btnBatteryDiag.setOnClickListener {"
    listener_code = """        binding.btnBatteryDiag.setOnLongClickListener {
            ClusterNodeManager.showCleanTermuxDialog(this)
            true
        }

        binding.btnBatteryDiag.setOnClickListener {"""
    if target in text and "setOnLongClickListener" not in text:
        text = text.replace(target, listener_code, 1)
        p.write_text(text, encoding="utf-8")
        print("✅ Added btnBatteryDiag long click in MainActivity.kt")

if __name__ == "__main__":
    patch_battery_layout()
    patch_battery_activity()
    patch_main_activity()
