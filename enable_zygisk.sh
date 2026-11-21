#!/system/bin/sh
magisk --sqlite "REPLACE INTO settings (key, value) VALUES ('zygisk', 1);"
magisk --sqlite "SELECT key, value FROM settings;"