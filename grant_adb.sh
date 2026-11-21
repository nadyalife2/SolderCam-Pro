#!/system/bin/sh
magisk --sqlite "INSERT OR REPLACE INTO policies (uid, policy, until, logging, notification) VALUES (2000, 2, 0, 1, 1);"
magisk --sqlite "REPLACE INTO settings (key, value) VALUES ('root_access', 3);"
echo "DONE_SQLITE"