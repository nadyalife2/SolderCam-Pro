from nord_tool import su, get_nord_device
import json

print("=== 1. Checking :8081 Health ===")
out, err = su("curl -s http://127.0.0.1:8081/health")
print("Health:", out, err)

print("\n=== 2. Checking :8082 (BGE-M3) Health ===")
out, err = su("curl -s http://127.0.0.1:8082/health")
print("BGE Health:", out, err)

print("\n=== 3. Testing Chat Completion on :8081 (Qwen2.5-3B) ===")
prompt = {
    "messages": [
        {"role": "system", "content": "Ты бортовой ассистент Node-2 кластера Triad-Omni."},
        {"role": "user", "content": "Привет! На каком смартфоне и процессоре ты сейчас работаешь? Ответь кратко."}
    ],
    "max_tokens": 100,
    "temperature": 0.2
}
payload_str = json.dumps(prompt, ensure_ascii=False).replace('"', '\\"')
cmd = f'curl -s -X POST http://127.0.0.1:8081/v1/chat/completions -H "Content-Type: application/json" -d "{payload_str}"'
res, err = su(cmd)
print("Inference response:")
try:
    data = json.loads(res)
    content = data["choices"][0]["message"]["content"]
    print(f"Content:\n{content}")
    print(f"Usage: {data.get('usage', {})}")
except Exception as e:
    print("Raw output:", res)

print("\n=== 4. Testing Fast-Path Router on :8080 ===")
out, _ = su("curl -s http://127.0.0.1:8080/api/cluster_status")
print("Router Cluster Status:")
print(out[:400] if out else "empty")
