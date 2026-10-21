package com.soldercam.pro

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Color
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.BatteryManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import androidx.appcompat.app.AppCompatActivity
import com.soldercam.pro.databinding.ActivityBatteryDiagnosticsBinding
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.abs

class BatteryDiagnosticsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityBatteryDiagnosticsBinding
    private val handler = Handler(Looper.getMainLooper())
    private var toneGenerator: ToneGenerator? = null

    // NTC Health Tracking
    private val tempHistory = ArrayDeque<Float>()
    private var isNtcFrozen = false
    private var lastAlertBeep = 0L

    // In-App NTC Stress Test
    private var isStressRunning = false
    private var stressSecondsPassed = 0
    private var initialTestTemp = 0.0f
    private val stressWorkers = mutableListOf<Thread>()

    // Persistent CSV Logging
    private lateinit var csvLogFile: File
    private var lastCsvWriteTime = 0L
    private var currentLevel = 0
    private var currentTempC = 24.0f
    private var currentStatusStr = "Unknown"
    private var currentSourceStr = "Unknown"

    private val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())

    private val batteryReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == Intent.ACTION_BATTERY_CHANGED) {
                updateBatteryData(intent)
            }
        }
    }

    private val tickerRunnable = object : Runnable {
        override fun run() {
            // Periodic update of current and power
            readRealtimeProperties()
            handler.postDelayed(this, 1000)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityBatteryDiagnosticsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        supportActionBar?.title = "OnePlus N10 - Тест АКБ"
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        try {
            toneGenerator = ToneGenerator(AudioManager.STREAM_ALARM, 70)
        } catch (e: Exception) {
            logMessage("Не удалось инициализировать сирену: ${e.message}")
        }

        logMessage("Старт монитора питания OnePlus Nord N10 5G...")
        logMessage("Драйвер контроллера: TI BQ27541 / Qualcomm PM7250B")

        // Initialize CSV file
        csvLogFile = File(getExternalFilesDir(null), "battery_telemetry.csv")
        if (!csvLogFile.exists()) {
            csvLogFile.writeText("Time,Level_Percent,Voltage_mV,Current_mA,Power_Watts,Temp_C,Status,Source\n")
        }
        binding.tvLogFilePath.text = "Файл: ${csvLogFile.name} (${csvLogFile.length() / 1024} KB)"

        binding.btnShareLog.setOnClickListener {
            shareCsvFile()
        }

        binding.btnClearLog.setOnClickListener {
            clearCsvLog()
        }

        binding.btnRunNtcTest.setOnClickListener {
            if (!isStressRunning) {
                startNtcStressTest()
            } else {
                stopNtcStressTest()
            }
        }
    }

    override fun onResume() {
        super.onResume()
        registerReceiver(batteryReceiver, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        handler.post(tickerRunnable)
    }

    override fun onPause() {
        super.onPause()
        unregisterReceiver(batteryReceiver)
        handler.removeCallbacks(tickerRunnable)
    }

    override fun onDestroy() {
        super.onDestroy()
        toneGenerator?.release()
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }

    private fun updateBatteryData(intent: Intent) {
        val rawVoltage = intent.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 0)
        val rawTemp = intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0)
        val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, 0)
        val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, 100)
        val plugged = intent.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0)
        val status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, BatteryManager.BATTERY_STATUS_UNKNOWN)

        val percent = if (scale > 0) (level * 100) / scale else level
        val tempCelsius = rawTemp / 10.0f

        currentLevel = percent
        currentTempC = tempCelsius

        // 1. Process Temperature & NTC check
        binding.tvTemperature.text = String.format(Locale.US, "%.1f °C", tempCelsius)
        trackNtcHealth(tempCelsius, status == BatteryManager.BATTERY_STATUS_CHARGING)

        // 2. Process Voltage & Overvoltage check
        val voltageMv = if (rawVoltage > 1000) rawVoltage else rawVoltage * 1000 // handle volts vs millivolts
        binding.tvVoltage.text = "$voltageMv mV"
        checkOvervoltage(voltageMv, status == BatteryManager.BATTERY_STATUS_CHARGING)

        // 3. Level & Source
        binding.tvLevel.text = "$percent %"
        val sourceText = when (plugged) {
            BatteryManager.BATTERY_PLUGGED_AC -> "Сеть (220V Блок)"
            BatteryManager.BATTERY_PLUGGED_USB -> "USB Порт"
            BatteryManager.BATTERY_PLUGGED_WIRELESS -> "Беспроводная"
            else -> "От батареи (Разряд)"
        }
        val statusText = when (status) {
            BatteryManager.BATTERY_STATUS_CHARGING -> "Идет заряд"
            BatteryManager.BATTERY_STATUS_DISCHARGING -> "Разряжается"
            BatteryManager.BATTERY_STATUS_FULL -> "100% Заряжен"
            BatteryManager.BATTERY_STATUS_NOT_CHARGING -> "Не заряжается"
            else -> "Статус: неизвестен"
        }
        currentSourceStr = sourceText
        currentStatusStr = statusText
        binding.tvSource.text = "$sourceText | $statusText"

        readRealtimeProperties(voltageMv)
    }

    private fun readRealtimeProperties(currentVoltageMv: Int = 4200) {
        val batteryManager = getSystemService(Context.BATTERY_SERVICE) as BatteryManager

        // Current in uA or mA
        var currentMicroAmps = batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW)
        if (currentMicroAmps == Int.MIN_VALUE || currentMicroAmps == 0) {
            // Try direct sysfs fallback
            currentMicroAmps = readSysfsInt("/sys/class/power_supply/battery/current_now")
        }

        // Standardize to mA
        val currentMa = if (abs(currentMicroAmps) > 10000) currentMicroAmps / 1000 else currentMicroAmps
        binding.tvCurrent.text = "$currentMa mA"

        if (currentMa > 0) {
            binding.tvCurrent.setTextColor(Color.parseColor("#4CAF50")) // Charging
        } else if (currentMa < 0) {
            binding.tvCurrent.setTextColor(Color.parseColor("#2196F3")) // Discharging
        } else {
            binding.tvCurrent.setTextColor(Color.parseColor("#9E9E9E"))
        }

        // Power calculation in Watts
        val powerWatts = (abs(currentVoltageMv) * abs(currentMa)) / 1_000_000.0f
        binding.tvPower.text = String.format(Locale.US, "Мощность: %.2f W", powerWatts)

        // Persistent CSV row logging
        writeCsvRow(currentLevel, currentVoltageMv, currentMa, powerWatts, currentTempC, currentStatusStr, currentSourceStr)
    }

    private fun trackNtcHealth(temp: Float, isCharging: Boolean) {
        tempHistory.addLast(temp)
        if (tempHistory.size > 20) {
            tempHistory.removeFirst()
        }

        // If all readings are identical and equal to exactly 24.0 or 25.0, it's a fixed resistor
        val allIdentical = tempHistory.size >= 10 && tempHistory.all { it == temp }
        if (allIdentical && (temp == 24.0f || temp == 25.0f)) {
            isNtcFrozen = true
            binding.tvTemperatureStatus.text = "⚠️ ВНИМАНИЕ: ОБМАНКА 10k! Датчик не меняется"
            binding.tvTemperatureStatus.setTextColor(Color.parseColor("#FF5252"))
            binding.tvAlertNtc.text = "• ТЕРМОДАТЧИК: ОБМАНКА! Зафиксирован на $temp°C. Защита от перегрева НЕ работает!"
            binding.tvAlertNtc.setTextColor(Color.parseColor("#FF5252"))
        } else {
            isNtcFrozen = false
            binding.tvTemperatureStatus.text = "Датчик NTC: Активен (динамика OK)"
            binding.tvTemperatureStatus.setTextColor(Color.parseColor("#4CAF50"))
            binding.tvAlertNtc.text = "• Термодатчик NTC передает живые данные ($temp°C)"
            binding.tvAlertNtc.setTextColor(Color.parseColor("#E0E0E0"))
        }
    }

    private fun checkOvervoltage(voltageMv: Int, isCharging: Boolean) {
        when {
            voltageMv >= 4400 -> {
                binding.tvVoltage.setTextColor(Color.parseColor("#FF5252"))
                binding.tvVoltageStatus.text = "ОПАСНО: > 4.40V! Электролиз в банке!"
                binding.tvVoltageStatus.setTextColor(Color.parseColor("#FF5252"))
                binding.tvAlertVoltage.text = "• НАПРЯЖЕНИЕ: $voltageMv mV! Превышен критический лимит. Срочно отключите зарядку!"
                binding.tvAlertVoltage.setTextColor(Color.parseColor("#FF5252"))

                triggerAlarmBeep()
            }
            voltageMv >= 4350 -> {
                binding.tvVoltage.setTextColor(Color.parseColor("#FFA726"))
                binding.tvVoltageStatus.text = "Предупреждение: 4.35V (порог копий АКБ)"
                binding.tvVoltageStatus.setTextColor(Color.parseColor("#FFA726"))
                binding.tvAlertVoltage.text = "• Напряжение $voltageMv mV. Для неоригинального АКБ рекомендуется снять с зарядки."
                binding.tvAlertVoltage.setTextColor(Color.parseColor("#FFA726"))
            }
            else -> {
                binding.tvVoltage.setTextColor(Color.parseColor("#4CAF50"))
                binding.tvVoltageStatus.text = "В безопасной зоне (< 4.35V)"
                binding.tvVoltageStatus.setTextColor(Color.parseColor("#9E9E9E"))
                binding.tvAlertVoltage.text = "• Напряжение $voltageMv mV в норме"
                binding.tvAlertVoltage.setTextColor(Color.parseColor("#E0E0E0"))
            }
        }
    }

    private fun triggerAlarmBeep() {
        if (!binding.switchAlarm.isChecked) return
        val now = System.currentTimeMillis()
        if (now - lastAlertBeep > 3000) {
            lastAlertBeep = now
            try {
                toneGenerator?.startTone(ToneGenerator.TONE_CDMA_EMERGENCY_RINGBACK, 500)
            } catch (e: Exception) {
                // Ignore audio errors
            }
        }
    }

    private fun logMessage(msg: String) {
        val time = timeFormat.format(Date())
        val currentLog = binding.tvLog.text.toString()
        val newLog = "[$time] $msg\n$currentLog"
        binding.tvLog.text = newLog
    }

    private fun startNtcStressTest() {
        val currentTempStr = binding.tvTemperature.text.toString().replace(" °C", "").trim()
        initialTestTemp = currentTempStr.toFloatOrNull() ?: 24.0f
        isStressRunning = true
        stressSecondsPassed = 0

        binding.btnRunNtcTest.text = "Остановить тест"
        binding.btnRunNtcTest.setBackgroundColor(Color.parseColor("#D32F2F"))
        binding.progressStress.visibility = android.view.View.VISIBLE
        binding.progressStress.progress = 0
        binding.tvStressResult.text = "Тест запущен: прогрев 8 ядер CPU... (0/15 сек)"
        binding.tvStressResult.setTextColor(Color.parseColor("#FFA726"))

        logMessage("Запуск 15-сек стресс-теста NTC... Базовая температура: $initialTestTemp°C")

        // Start CPU load on all available cores
        val cores = Runtime.getRuntime().availableProcessors().coerceAtLeast(4)
        stressWorkers.clear()
        for (i in 0 until cores) {
            val t = Thread {
                var x = 0.0
                while (isStressRunning) {
                    x += Math.sin(x) * Math.cos(x)
                }
            }
            stressWorkers.add(t)
            t.start()
        }

        // Timer handler for 15 seconds
        val stressRunnable = object : Runnable {
            override fun run() {
                if (!isStressRunning) return
                stressSecondsPassed++
                binding.progressStress.progress = stressSecondsPassed
                binding.tvStressResult.text = "Прогрев ядер процессора... ($stressSecondsPassed/15 сек)"

                if (stressSecondsPassed >= 15) {
                    stopNtcStressTest()
                    evaluateNtcResult()
                } else {
                    handler.postDelayed(this, 1000)
                }
            }
        }
        handler.postDelayed(stressRunnable, 1000)
    }

    private fun stopNtcStressTest() {
        isStressRunning = false
        stressWorkers.clear()
        binding.btnRunNtcTest.text = "Запустить тест термодатчика (15 сек)"
        binding.btnRunNtcTest.setBackgroundColor(Color.parseColor("#1976D2"))
        binding.progressStress.visibility = android.view.View.GONE
    }

    private fun evaluateNtcResult() {
        val currentTempStr = binding.tvTemperature.text.toString().replace(" °C", "").trim()
        val finalTemp = currentTempStr.toFloatOrNull() ?: initialTestTemp
        val delta = finalTemp - initialTestTemp

        if (delta <= 0.05f && (initialTestTemp == 24.0f || initialTestTemp == 25.0f)) {
            // Frozen at exactly 24 or 25!
            binding.tvStressResult.text = "❌ ВЕРДИКТ: ОБМАНКА 10 кОм ПОДТВЕРЖДЕНА!\nПроцессор разогрелся, но температура батареи осталась ровно $initialTestTemp°C. Термозащиты физически нет!"
            binding.tvStressResult.setTextColor(Color.parseColor("#FF5252"))
            logMessage("Тест NTC завершен: ОБМАНКА ПОДТВЕРЖДЕНА ($finalTemp°C без изменений)")
            triggerAlarmBeep()
        } else if (delta >= 0.5f) {
            binding.tvStressResult.text = "✅ ВЕРДИКТ: ТЕРМОДАТЧИК ЖИВОЙ!\nЗафиксирован нагрев на +${String.format(Locale.US, "%.1f", delta)}°C ($initialTestTemp -> $finalTemp°C)."
            binding.tvStressResult.setTextColor(Color.parseColor("#4CAF50"))
            logMessage("Тест NTC завершен: Датчик работает штатно (+${delta}°C)")
        } else {
            binding.tvStressResult.text = "⚠️ ВЕРДИКТ: Разница температур минимальна (+$delta°C). Попробуйте заряжать телефон и повторить тест."
            binding.tvStressResult.setTextColor(Color.parseColor("#FFA726"))
        }
    }

    private fun writeCsvRow(
        level: Int,
        voltageMv: Int,
        currentMa: Int,
        powerWatts: Float,
        tempC: Float,
        status: String,
        source: String
    ) {
        val now = System.currentTimeMillis()
        if (now - lastCsvWriteTime < 2000) return // sample every 2 sec
        lastCsvWriteTime = now
        try {
            val time = timeFormat.format(Date())
            val row = "$time,$level,$voltageMv,$currentMa,${String.format(Locale.US, "%.2f", powerWatts)},${String.format(Locale.US, "%.1f", tempC)},$status,$source\n"
            csvLogFile.appendText(row)
            val kb = csvLogFile.length() / 1024
            binding.tvLogFilePath.text = "Файл: ${csvLogFile.name} ($kb KB)"
        } catch (e: Exception) {
            // ignore disk errors
        }
    }

    private fun shareCsvFile() {
        try {
            if (!csvLogFile.exists() || csvLogFile.length() == 0L) {
                android.widget.Toast.makeText(this, "Журнал пока пуст", android.widget.Toast.LENGTH_SHORT).show()
                return
            }
            val uri = androidx.core.content.FileProvider.getUriForFile(
                this,
                "${applicationContext.packageName}.fileprovider",
                csvLogFile
            )
            val sendIntent = Intent(Intent.ACTION_SEND).apply {
                type = "text/comma-separated-values"
                putExtra(Intent.EXTRA_STREAM, uri)
                putExtra(Intent.EXTRA_SUBJECT, "OnePlus Nord N10 - Журнал Батареи (CSV)")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(sendIntent, "Поделиться журналом батареи (CSV)"))
        } catch (e: Exception) {
            android.widget.Toast.makeText(this, "Ошибка экспорта: ${e.message}", android.widget.Toast.LENGTH_LONG).show()
        }
    }

    private fun clearCsvLog() {
        try {
            csvLogFile.writeText("Time,Level_Percent,Voltage_mV,Current_mA,Power_Watts,Temp_C,Status,Source\n")
            binding.tvLog.text = ""
            logMessage("Журнал замеров очищен")
            binding.tvLogFilePath.text = "Файл: ${csvLogFile.name} (0 KB)"
            android.widget.Toast.makeText(this, "Журнал очищен", android.widget.Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            // ignore
        }
    }

    private fun readSysfsInt(path: String): Int {
        return try {
            val file = File(path)
            if (file.exists() && file.canRead()) {
                file.readText().trim().toIntOrNull() ?: 0
            } else 0
        } catch (e: Exception) {
            0
        }
    }
}
