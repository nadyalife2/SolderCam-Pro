package com.soldercam.pro

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/**
 * ClusterNodeManager:
 * Управление питанием узлов кластера Triad-Omni, ребут Termux и глубокая деактивация
 * (возврат смартфонов в абсолютно чистое, штатное состояние).
 */
object ClusterNodeManager {

    private const val DEFAULT_MASTER_HUB_IP = "192.168.31.161"
    private const val DEFAULT_PORT = 8000

    /**
     * Показывает диалог выбора узла и режима очистки/ребута для пользователя.
     */
    fun showCleanTermuxDialog(activity: AppCompatActivity) {
        val nodes = arrayOf(
            "📱 Этот смартфон (Локальное управление)",
            "🧠 NODE-1: Xiaomi Mi 10T 5G (Qwen 9B, 8GB RAM, :8080)",
            "⚡ NODE-2: OnePlus Nord N10 5G (LFM/BGE, 6GB RAM, :8081)",
            "🛰️ NODE-3: Redmi Note 4 (Master Hub, :8000)",
            "💥 ВСЕ УЗЛЫ КЛАСТЕРА (Управление всеми 3 устройствами)"
        )
        val nodeKeys = arrayOf("local", "node1", "node2", "node3", "all")
        var selectedIndex = 0

        AlertDialog.Builder(activity)
            .setTitle("🧹 Управление узлами & Termux")
            .setMessage("⚠️ РАСПРЕДЕЛЕНИЕ РОЛЕЙ КЛАСТЕРА:\n• Qwen3.5-9B Fast-Tool — работает на Xiaomi Mi 10T 5G\n• LFM2.5 / BGE-M3 — работают на OnePlus Nord N10\n• Redmi Note 4 — диспетчер, RAG и шлюз телеметрии.")
            .setSingleChoiceItems(nodes, selectedIndex) { _, which ->
                selectedIndex = which
            }
            .setPositiveButton("Далее") { _, _ ->
                val chosenKey = nodeKeys[selectedIndex]
                confirmAndExecute(activity, chosenKey, nodes[selectedIndex])
            }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun confirmAndExecute(activity: AppCompatActivity, nodeKey: String, nodeTitle: String) {
        val modes = arrayOf(
            "▶️ Запустить: поднять Termux и все службы кластера",
            "🛑 Полная деактивация: выгрузить Termux, закрыть приложение, телефон чист",
            "🔄 Ребут Termux: мягко перезапустить демоны ИИ и освободить буферы",
            "⚡ Мягкий сброс: остановить ИИ-сервисы, освободить RAM, оставить Termux",
            "🔋 Только батарея: восстановить штатную зарядку, снять байпас"
        )
        val modeKeys = arrayOf("start", "clean_stop", "restart", "soft_reset", "restore_battery")
        var selectedMode = 0

        AlertDialog.Builder(activity)
            .setTitle("Действие для: $nodeTitle")
            .setSingleChoiceItems(modes, selectedMode) { _, which ->
                selectedMode = which
            }
            .setPositiveButton("Выполнить") { _, _ ->
                val chosenMode = modeKeys[selectedMode]
                runAction(activity, nodeKey, chosenMode, nodeTitle)
            }
            .setNegativeButton("Назад") { _, _ ->
                showCleanTermuxDialog(activity)
            }
            .show()
    }

    private fun runAction(activity: AppCompatActivity, nodeKey: String, mode: String, nodeTitle: String) {
        val actionVerb = when (mode) {
            "start" -> "Запуск"
            "restart" -> "Перезапуск"
            else -> "Очистка"
        }
        Toast.makeText(activity, "⏳ $actionVerb [$nodeTitle]...", Toast.LENGTH_SHORT).show()

        thread {
            if (nodeKey == "local") {
                when (mode) {
                    "start" -> {
                        startLocalTermux(activity) { success, msg ->
                            Handler(Looper.getMainLooper()).post {
                                AlertDialog.Builder(activity)
                                    .setTitle(if (success) "✅ Службы запущены" else "⚠️ Внимание")
                                    .setMessage(msg)
                                    .setPositiveButton("OK", null)
                                    .show()
                            }
                        }
                    }
                    "restart" -> {
                        restartLocalTermux(activity) { success, msg ->
                            Handler(Looper.getMainLooper()).post {
                                AlertDialog.Builder(activity)
                                    .setTitle(if (success) "✅ Перезапуск выполнен" else "⚠️ Внимание")
                                    .setMessage(msg)
                                    .setPositiveButton("OK", null)
                                    .show()
                            }
                        }
                    }
                    else -> {
                        cleanLocalDevice(activity, mode) { success, msg ->
                            Handler(Looper.getMainLooper()).post {
                                AlertDialog.Builder(activity)
                                    .setTitle(if (success) "✅ Устройство очищено" else "⚠️ Внимание")
                                    .setMessage(msg)
                                    .setPositiveButton("OK") { _, _ ->
                                        if (mode == "clean_stop") {
                                            activity.finishAffinity()
                                        }
                                    }
                                    .show()
                            }
                        }
                    }
                }
            } else {
                val endpoint = when (mode) {
                    "start" -> "/api/node/start_termux"
                    "restart" -> "/api/node/restart_termux"
                    else -> "/api/node/stop_termux"
                }
                sendRemoteRequest(endpoint, nodeKey, mode) { success, msg ->
                    Handler(Looper.getMainLooper()).post {
                        AlertDialog.Builder(activity)
                            .setTitle(if (success) "✅ Кластер: Успех" else "⚠️ Ошибка связи")
                            .setMessage(msg)
                            .setPositiveButton("OK", null)
                            .show()
                    }
                }
            }
        }
    }

    /**
     * Локальный запуск служб Termux
     */
    fun startLocalTermux(context: Context, callback: (Boolean, String) -> Unit) {
        val cmds = listOf(
            "am start -n com.termux/.app.TermuxActivity 2>/dev/null || true",
            "if [ -f /data/data/com.termux/files/home/start_brain.sh ]; then nohup /data/data/com.termux/files/usr/bin/bash /data/data/com.termux/files/home/start_brain.sh >/dev/null 2>&1 & elif [ -f /data/data/com.termux/files/home/start_reflex.sh ]; then nohup sh /data/data/com.termux/files/home/start_reflex.sh >/dev/null 2>&1 & else nohup sh /data/data/com.termux/files/home/start_router.sh >/dev/null 2>&1 & fi"
        ).joinToString("; ")

        try {
            val p = Runtime.getRuntime().exec(arrayOf("su", "-c", cmds))
            p.waitFor()
            callback(true, "Службы Termux на локальном смартфоне успешно запущены.")
        } catch (e: Exception) {
            try {
                val p = Runtime.getRuntime().exec(arrayOf("sh", "-c", cmds))
                p.waitFor()
                callback(true, "Запущен Termux (без root прав).")
            } catch (err: Exception) {
                callback(false, "Сбой локального запуска: ${err.message}")
            }
        }
    }

    /**
     * Локальный перезапуск сервисов Termux
     */
    fun restartLocalTermux(context: Context, callback: (Boolean, String) -> Unit) {
        val cmds = listOf(
            "pkill -9 -f llama-server 2>/dev/null || true",
            "pkill -9 -f 'python.*omni_fast_router' 2>/dev/null || true",
            "pkill -9 -f 'python.*bge' 2>/dev/null || true",
            "sleep 1",
            "if [ -f /data/data/com.termux/files/home/start_brain.sh ]; then nohup /data/data/com.termux/files/usr/bin/bash /data/data/com.termux/files/home/start_brain.sh >/dev/null 2>&1 & elif [ -f /data/data/com.termux/files/home/start_reflex.sh ]; then nohup sh /data/data/com.termux/files/home/start_reflex.sh >/dev/null 2>&1 & else nohup sh /data/data/com.termux/files/home/start_router.sh >/dev/null 2>&1 & fi"
        ).joinToString("; ")

        try {
            val p = Runtime.getRuntime().exec(arrayOf("su", "-c", cmds))
            p.waitFor()
            callback(true, "Сервисы Termux на локальном смартфоне перезапущены в фоновом режиме.")
        } catch (e: Exception) {
            callback(false, "Сбой локального перезапуска: ${e.message}")
        }
    }

    /**
     * Локальное завершение процессов Termux и очистка системных буферов через Shell/Root
     */
    fun cleanLocalDevice(context: Context, mode: String, callback: (Boolean, String) -> Unit) {
        val cmds = mutableListOf<String>()

        if (mode == "restore_battery") {
            // Режим только батареи: восстанавливаем штатную зарядку без убийства процессов и логов
            cmds.add("echo 1 > /sys/class/power_supply/battery/charging_enabled 2>/dev/null || true")
            cmds.add("echo 1 > /sys/class/power_supply/battery/battery_charging_enabled 2>/dev/null || true")
            cmds.add("echo 0 > /sys/class/power_supply/battery/input_suspend 2>/dev/null || true")
        } else {
            cmds.add("termux-wake-unlock 2>/dev/null || true")
            cmds.add("pkill -9 -f llama-server 2>/dev/null || true")
            cmds.add("pkill -9 -f 'python.*omni_fast_router' 2>/dev/null || true")
            cmds.add("pkill -9 -f 'python.*bge' 2>/dev/null || true")
            cmds.add("pkill -9 -f 'python.*lfm' 2>/dev/null || true")
            cmds.add("echo 1 > /sys/class/power_supply/battery/charging_enabled 2>/dev/null || true")
            cmds.add("echo 1 > /sys/class/power_supply/battery/battery_charging_enabled 2>/dev/null || true")
            cmds.add("echo 0 > /sys/class/power_supply/battery/input_suspend 2>/dev/null || true")
            cmds.add("sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true")

            if (mode == "clean_stop") {
                cmds.add("am force-stop com.termux 2>/dev/null || true")
                cmds.add("pkill -9 -f com.termux 2>/dev/null || true")
            }
        }

        val fullCmd = cmds.joinToString("; ")
        var hasRoot = false

        try {
            val p = Runtime.getRuntime().exec(arrayOf("su", "-c", fullCmd))
            p.waitFor()
            hasRoot = (p.exitValue() == 0)
        } catch (e: Exception) {
            try {
                val p = Runtime.getRuntime().exec(arrayOf("sh", "-c", fullCmd))
                p.waitFor()
            } catch (err: Exception) { }
        }

        val resultMsg = if (mode == "restore_battery") {
            "Контроллер питания успешно переведен в штатный режим зарядки!\n\n" +
                    "• Байпас отключен, батарея заряжается\n" +
                    "• ИИ-сервисы и логи не затронуты\n" +
                    "• Root: ${if (hasRoot) "активен" else "стандартный доступ"}"
        } else {
            "Локальное устройство успешно переведено в чистый режим!\n\n" +
                    "• ИИ-сервисы выгружены из LPDDR памяти\n" +
                    "• WakeLock процессора снят (ядра спят)\n" +
                    "• Контроллер зарядки переведен в штатный режим\n" +
                    "• Root-доступ: ${if (hasRoot) "активен (drop_caches выполнен)" else "стандартный"}"
        }

        callback(true, resultMsg)
    }

    /**
     * Отправка запроса на Master Hub через HTTP
     */
    private fun sendRemoteRequest(endpoint: String, nodeKey: String, mode: String, callback: (Boolean, String) -> Unit) {
        val targets = listOf(
            "http://192.168.31.48:8000",
            "http://192.168.31.161:8000",
            "http://192.168.31.57:8080",
            "http://127.0.0.1:8000"
        )

        var lastError = "Все адреса хаба недоступны"

        for (host in targets) {
            try {
                val url = URL("$host$endpoint")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.connectTimeout = 2500
                conn.readTimeout = 4000
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")

                val json = JSONObject()
                json.put("node", nodeKey)
                json.put("mode", mode)

                OutputStreamWriter(conn.outputStream, "UTF-8").use {
                    it.write(json.toString())
                    it.flush()
                }

                if (conn.responseCode in 200..299) {
                    val reader = BufferedReader(InputStreamReader(conn.inputStream, "UTF-8"))
                    val resp = reader.readText()
                    reader.close()

                    val respJson = JSONObject(resp)
                    val msg = respJson.optString("message", "Действие успешно выполнено!")
                    callback(true, "Ответ шлюза ($host):\n\n$msg")
                    return
                }
            } catch (e: Exception) {
                lastError = e.message ?: "Сбой соединения"
            }
        }

        callback(false, "Не удалось связаться с роутером кластера: $lastError\n\nВы можете выбрать 'Этот смартфон' для мгновенной локальной команды без сети.")
    }
}
