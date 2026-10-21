package com.soldercam.pro

import android.app.AlertDialog
import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.soldercam.pro.databinding.ActivityBugTrackerBinding
import com.soldercam.pro.databinding.ItemBugCardBinding

class BugTrackerActivity : AppCompatActivity() {

    private lateinit var binding: ActivityBugTrackerBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityBugTrackerBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnBack.setOnClickListener {
            finish()
        }

        binding.btnAddRecord.setOnClickListener {
            showAddRecordDialog()
        }

        binding.btnShare.setOnClickListener {
            if (BugTracker.getRecords().isEmpty()) {
                Toast.makeText(this, "Журнал пуст, нечего экспортировать", Toast.LENGTH_SHORT).show()
            } else {
                BugTracker.shareReport(this)
            }
        }

        binding.btnClearAll.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("Очистить журнал?")
                .setMessage("Все сохраненные отчеты о багах и крашах будут удалены.")
                .setPositiveButton("Удалить") { _, _ ->
                    BugTracker.clearLedger()
                    refreshList()
                    Toast.makeText(this, "Журнал очищен", Toast.LENGTH_SHORT).show()
                }
                .setNegativeButton("Отмена", null)
                .show()
        }

        refreshList()
    }

    override fun onResume() {
        super.onResume()
        refreshList()
    }

    private fun refreshList() {
        binding.cardsContainer.removeAllViews()
        val records = BugTracker.getRecords()

        val crashes = records.count { it.type == "CRASH" }
        val notes = records.count { it.type == "BUG_NOTE" }
        val fixes = records.count { it.type == "FIX_VERIFIED" }

        binding.tvStats.text = "Всего: ${records.size} | Крэши: $crashes | Заметки: $notes | Фиксы: $fixes"

        if (records.isEmpty()) {
            binding.tvEmptyState.visibility = View.VISIBLE
            return
        }
        binding.tvEmptyState.visibility = View.GONE

        val inflater = LayoutInflater.from(this)
        for (rec in records) {
            val cardBinding = ItemBugCardBinding.inflate(inflater, binding.cardsContainer, false)

            cardBinding.tvTimestamp.text = rec.timestamp
            cardBinding.tvTitle.text = rec.title
            cardBinding.tvDescription.text = rec.description

            // Badge styling
            when (rec.type) {
                "CRASH" -> {
                    cardBinding.tvTypeBadge.text = "💥 КРЭШ"
                    cardBinding.tvTypeBadge.setTextColor(Color.parseColor("#FF5252"))
                    cardBinding.tvTypeBadge.setBackgroundColor(Color.parseColor("#33FF5252"))
                }
                "FIX_VERIFIED" -> {
                    cardBinding.tvTypeBadge.text = "✅ ФИКС"
                    cardBinding.tvTypeBadge.setTextColor(Color.parseColor("#00E676"))
                    cardBinding.tvTypeBadge.setBackgroundColor(Color.parseColor("#3300E676"))
                }
                "METRIC_ALERT" -> {
                    cardBinding.tvTypeBadge.text = "⚠️ АЛЕРТ"
                    cardBinding.tvTypeBadge.setTextColor(Color.parseColor("#448AFF"))
                    cardBinding.tvTypeBadge.setBackgroundColor(Color.parseColor("#33448AFF"))
                }
                else -> {
                    cardBinding.tvTypeBadge.text = "📝 ЗАМЕТКА"
                    cardBinding.tvTypeBadge.setTextColor(Color.parseColor("#FFB74D"))
                    cardBinding.tvTypeBadge.setBackgroundColor(Color.parseColor("#33FFB74D"))
                }
            }

            // Battery info
            if (!rec.batteryStatus.isNullOrEmpty()) {
                cardBinding.tvBatteryStatus.text = rec.batteryStatus
                cardBinding.tvBatteryStatus.visibility = View.VISIBLE
            } else {
                cardBinding.tvBatteryStatus.visibility = View.GONE
            }

            // Camera info
            if (!rec.cameraStatus.isNullOrEmpty()) {
                cardBinding.tvCameraStatus.text = rec.cameraStatus
                cardBinding.tvCameraStatus.visibility = View.VISIBLE
            } else {
                cardBinding.tvCameraStatus.visibility = View.GONE
            }

            // Stack trace
            if (!rec.stackTrace.isNullOrEmpty()) {
                cardBinding.tvStackTrace.text = rec.stackTrace
                cardBinding.tvStackTrace.visibility = View.VISIBLE
            } else {
                cardBinding.tvStackTrace.visibility = View.GONE
            }

            // Delete button
            cardBinding.btnDelete.setOnClickListener {
                BugTracker.deleteRecord(rec.id)
                refreshList()
            }

            binding.cardsContainer.addView(cardBinding.root)
        }
    }

    private fun showAddRecordDialog() {
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(50, 40, 50, 20)
        }

        val typeSpinner = Spinner(this)
        val types = arrayOf("📝 Заметка о баге / тесте (BUG_NOTE)", "✅ Проверенный фикс (FIX_VERIFIED)", "⚠️ Предупреждение (METRIC_ALERT)")
        typeSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, types)
        layout.addView(typeSpinner)

        val inputTitle = EditText(this).apply {
            hint = "Краткое название (напр. Размытие при макро)"
            setTextColor(Color.WHITE)
            setHintTextColor(Color.GRAY)
        }
        layout.addView(inputTitle)

        val inputDesc = EditText(this).apply {
            hint = "Подробности, шаги воспроизведения, условия..."
            setTextColor(Color.WHITE)
            setHintTextColor(Color.GRAY)
            minLines = 3
        }
        layout.addView(inputDesc)

        AlertDialog.Builder(this)
            .setTitle("Зафиксировать баг / тест")
            .setView(layout)
            .setPositiveButton("Сохранить") { _, _ ->
                val title = inputTitle.text.toString().trim()
                val desc = inputDesc.text.toString().trim()
                if (title.isEmpty()) {
                    Toast.makeText(this, "Укажите название", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }

                val selectedType = when (typeSpinner.selectedItemPosition) {
                    1 -> "FIX_VERIFIED"
                    2 -> "METRIC_ALERT"
                    else -> "BUG_NOTE"
                }

                BugTracker.recordBug(
                    title = title,
                    description = desc,
                    type = selectedType
                )
                refreshList()
                Toast.makeText(this, "Запись сохранена в журнал", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Отмена", null)
            .show()
    }
}
