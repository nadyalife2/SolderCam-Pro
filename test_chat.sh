export PATH=/data/data/com.termux/files/usr/bin:$PATH
curl -s -X POST http://127.0.0.1:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Respond with exactly: OK_NODE2"}],"max_tokens":10}'
echo