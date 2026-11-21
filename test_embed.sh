export PATH=/data/data/com.termux/files/usr/bin:$PATH
curl -s -X POST http://127.0.0.1:8082/embedding \
  -H "Content-Type: application/json" \
  -d '{"content":"Nord N10 hardware cluster test"}' | cut -c 1-200
echo