#!/usr/bin/env bash
# ==============================================================================
# Triad-Omni End-to-End Chat & Routing Verification (v5.1)
# ==============================================================================
export PATH="/data/data/com.termux/files/usr/bin:$PATH"

TARGET_URL="${1:-http://127.0.0.1:8000/v1/chat/completions}"
echo "[*] Testing chat completion on $TARGET_URL ..."

RESP=$(curl -sS -w "\n%{http_code}" --connect-timeout 4 --max-time 30 -X POST "$TARGET_URL" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"статус"}],"max_tokens":32}')

HTTP_CODE=$(echo "$RESP" | tail -n1)
BODY=$(echo "$RESP" | sed '$d')

echo "[*] HTTP Status: $HTTP_CODE"
echo "[*] Response Body:"
echo "$BODY"

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "✅ [SUCCESS] Triad-Omni chat endpoint verified!"
    exit 0
else
    echo "❌ [FAILED] Non-2xx response from $TARGET_URL (HTTP $HTTP_CODE)"
    exit 1
fi
