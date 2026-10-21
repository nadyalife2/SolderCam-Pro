package com.soldercam.pro

import org.json.JSONObject

data class BugRecord(
    val id: String,
    val timestamp: String,
    val type: String, // "CRASH", "BUG_NOTE", "FIX_VERIFIED", "METRIC_ALERT"
    val title: String,
    val description: String,
    val batteryStatus: String? = null,
    val cameraStatus: String? = null,
    val stackTrace: String? = null
) {
    fun toJson(): JSONObject {
        val obj = JSONObject()
        obj.put("id", id)
        obj.put("timestamp", timestamp)
        obj.put("type", type)
        obj.put("title", title)
        obj.put("description", description)
        obj.put("batteryStatus", batteryStatus ?: "")
        obj.put("cameraStatus", cameraStatus ?: "")
        obj.put("stackTrace", stackTrace ?: "")
        return obj
    }

    companion object {
        fun fromJson(obj: JSONObject): BugRecord {
            return BugRecord(
                id = obj.optString("id", System.currentTimeMillis().toString()),
                timestamp = obj.optString("timestamp", ""),
                type = obj.optString("type", "BUG_NOTE"),
                title = obj.optString("title", "Без названия"),
                description = obj.optString("description", ""),
                batteryStatus = obj.optString("batteryStatus").takeIf { it.isNotEmpty() },
                cameraStatus = obj.optString("cameraStatus").takeIf { it.isNotEmpty() },
                stackTrace = obj.optString("stackTrace").takeIf { it.isNotEmpty() }
            )
        }
    }
}
