package com.soldercam.pro

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Build
import android.util.Log
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.CopyOnWriteArrayList

object BugTracker {
    private const val TAG = "BugTracker"
    private const val FILE_NAME = "bug_ledger.json"
    private val records = CopyOnWriteArrayList<BugRecord>()
    private var appContext: Context? = null
    private var defaultExceptionHandler: Thread.UncaughtExceptionHandler? = null

    // Текущий статус камеры (обновляется из MainActivity)
    var currentCameraInfo: String = "Камера не активна"

    fun init(context: Context) {
        if (appContext != null) return
        appContext = context.applicationContext
        loadRecords()

        // Перехват неожиданных сбоев (Uncaught Exceptions)
        defaultExceptionHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            handleUncaughtException(thread, throwable)
            defaultExceptionHandler?.uncaughtException(thread, throwable)
        }
        Log.i(TAG, "BugTracker инициализирован. Загружено записей: ${records.size}")
    }

    private fun handleUncaughtException(thread: Thread, throwable: Throwable) {
        val sw = StringWriter()
        val pw = PrintWriter(sw)
        throwable.printStackTrace(pw)
        val stackTrace = sw.toString()

        val record = BugRecord(
            id = "crash_${System.currentTimeMillis()}",
            timestamp = getCurrentTimestamp(),
            type = "CRASH",
            title = "Сбой в потоке '${thread.name}': ${throwable.javaClass.simpleName}",
            description = throwable.message ?: "Критическая ошибка без описания",
            batteryStatus = getBatterySnapshot(),
            cameraStatus = currentCameraInfo,
            stackTrace = stackTrace
        )

        records.add(0, record)
        saveRecords()
        Log.e(TAG, "Зафиксирован аварийный сбой: ${record.title}")
    }

    fun recordBug(
        title: String,
        description: String,
        type: String = "BUG_NOTE",
        customCameraInfo: String? = null
    ): BugRecord {
        val record = BugRecord(
            id = "bug_${System.currentTimeMillis()}",
            timestamp = getCurrentTimestamp(),
            type = type,
            title = title,
            description = description,
            batteryStatus = getBatterySnapshot(),
            cameraStatus = customCameraInfo ?: currentCameraInfo,
            stackTrace = null
        )
        records.add(0, record)
        saveRecords()
        return record
    }

    fun recordFix(title: String, description: String): BugRecord {
        return recordBug(title, description, type = "FIX_VERIFIED")
    }

    fun getRecords(): List<BugRecord> = records.toList()

    fun deleteRecord(id: String) {
        records.removeAll { it.id == id }
        saveRecords()
    }

    fun clearLedger() {
        records.clear()
        saveRecords()
    }

    private fun getCurrentTimestamp(): String {
        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        return sdf.format(Date())
    }

    fun getBatterySnapshot(): String {
        val ctx = appContext ?: return "Контекст недоступен"
        return try {
            val ifilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
            val bIntent = ctx.registerReceiver(null, ifilter)
            val level = bIntent?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
            val scale = bIntent?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
            val pct = if (level >= 0 && scale > 0) (level * 100 / scale) else -1
            val voltageMv = bIntent?.getIntExtra(BatteryManager.EXTRA_VOLTAGE, -1) ?: -1
            val tempTenths = bIntent?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, -1) ?: -1
            val tempC = if (tempTenths > 0) tempTenths / 10.0 else 0.0

            val bm = ctx.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
            val currentUa = bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW) ?: 0
            val currentMa = currentUa / 1000

            "АКБ: $pct%, ${voltageMv}mV (${String.format(Locale.US, "%.3f", voltageMv / 1000.0)}V), ${currentMa}mA, ${tempC}°C (Модель: ${Build.MANUFACTURER} ${Build.MODEL}, Android ${Build.VERSION.RELEASE})"
        } catch (e: Exception) {
            "Ошибка телеметрии АКБ: ${e.message}"
        }
    }

    @Synchronized
    private fun saveRecords() {
        val ctx = appContext ?: return
        try {
            val file = File(ctx.filesDir, FILE_NAME)
            val jsonArray = JSONArray()
            for (rec in records) {
                jsonArray.put(rec.toJson())
            }
            file.writeText(jsonArray.toString(2))
        } catch (e: Exception) {
            Log.e(TAG, "Ошибка сохранения bug_ledger.json", e)
        }
    }

    @Synchronized
    private fun loadRecords() {
        val ctx = appContext ?: return
        try {
            val file = File(ctx.filesDir, FILE_NAME)
            if (!file.exists()) return
            val jsonStr = file.readText()
            val jsonArray = JSONArray(jsonStr)
            records.clear()
            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                records.add(BugRecord.fromJson(obj))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Ошибка загрузки bug_ledger.json", e)
        }
    }

    fun exportLedgerJson(context: Context): File {
        val exportFile = File(context.getExternalFilesDir(null), "soldercam_bugs_${System.currentTimeMillis()}.json")
        val jsonArray = JSONArray()
        for (rec in records) {
            jsonArray.put(rec.toJson())
        }
        exportFile.writeText(jsonArray.toString(2))
        return exportFile
    }

    fun exportMarkdownSummary(context: Context): File {
        val exportFile = File(context.getExternalFilesDir(null), "soldercam_bugs_report.md")
        val sb = StringBuilder()
        sb.append("# 🐞 Журнал багов, тестов и исправлений SolderCam Pro\n\n")
        sb.append("**Устройство:** ${Build.MANUFACTURER} ${Build.MODEL} (Android ${Build.VERSION.RELEASE}, SDK ${Build.VERSION.SDK_INT})\n")
        sb.append("**Дата выгрузки:** ${getCurrentTimestamp()}\n")
        sb.append("**Всего записей:** ${records.size}\n\n")

        val crashes = records.filter { it.type == "CRASH" }
        val notes = records.filter { it.type == "BUG_NOTE" }
        val fixes = records.filter { it.type == "FIX_VERIFIED" }

        sb.append("- 💥 Крэши: ${crashes.size}\n")
        sb.append("- 📝 Заметки инженера / Баги: ${notes.size}\n")
        sb.append("- ✅ Проверенные фиксы: ${fixes.size}\n\n")
        sb.append("---\n\n")

        for ((index, rec) in records.withIndex()) {
            val icon = when (rec.type) {
                "CRASH" -> "💥 [CRASH]"
                "FIX_VERIFIED" -> "✅ [FIX]"
                else -> "📝 [BUG]"
            }
            sb.append("### ${index + 1}. $icon ${rec.title}\n")
            sb.append("- **Время:** `${rec.timestamp}`\n")
            sb.append("- **Тип:** `${rec.type}`\n")
            if (!rec.batteryStatus.isNullOrEmpty()) {
                sb.append("- **Состояние АКБ:** ${rec.batteryStatus}\n")
            }
            if (!rec.cameraStatus.isNullOrEmpty()) {
                sb.append("- **Состояние камеры:** ${rec.cameraStatus}\n")
            }
            sb.append("\n**Описание:**\n${rec.description}\n\n")
            if (!rec.stackTrace.isNullOrEmpty()) {
                sb.append("```\n${rec.stackTrace}\n```\n\n")
            }
            sb.append("---\n\n")
        }

        exportFile.writeText(sb.toString())
        return exportFile
    }

    fun shareReport(context: Context) {
        val file = exportMarkdownSummary(context)
        val uri = FileProvider.getUriForFile(context, "com.soldercam.pro.fileprovider", file)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/markdown"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_SUBJECT, "SolderCam Pro Bug Ledger - ${Build.MODEL}")
            putExtra(Intent.EXTRA_TEXT, "Отчет журнала багов и телеметрии SolderCam Pro (${records.size} записей)")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        val chooser = Intent.createChooser(intent, "Отправить отчет о багах")
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(chooser)
    }
}
