# 03. Узел №4: ПК (`Ubuntu 22.04` + `GTX 1050 Ti 4GB`) — MoE-Учитель, Куратор Датасетов и Верификатор

Узел №4 (рабочая станция) решает три ключевые задачи:
1. **Быстрый локальный MoE-учитель (`:8090`)**: модель **`Qwen3-Coder-30B-A3B-Instruct-IQ3_XS`** с оффлоадом экспертов на CPU. Выдает **8–15 токенов/сек** на скромной связке GTX 1050 Ti (4GB) + 16GB DDR4 RAM (вместо мучительных 0.5–1.5 ток/с у плотных 33B моделей).
2. **Куратор датасетов и синхронизатор скилов**: отслеживает файлы скилов локальных IDE и агентов, очищает логи, удаляет дубликаты и готовит пакеты для еженедельного бесплатного дообучения в Google Colab T4.
3. **Хук компиляции и верификации `verify_and_learn.sh`**: компилирует прошивки/код на ПК (PlatformIO, GCC, Gradle); при ошибке автоматически запрашивает исправление через шлюз (`/v1/escalate`) и пополняет базу знаний.

> [!CAUTION]
> **Физическое ограничение VRAM: локальное обучение 7B/9B на 4GB карте невозможно.**  
> Попытка запустить `bitsandbytes` NF4 QLoRA для модели 9B на карте 4GB неизбежно падает в CUDA OOM (`device_map={"": 0}` требует минимум 7.5 ГБ VRAM). Обучение 9B вынесено на бесплатный Google Colab Tesla T4 (16 ГБ VRAM). Локально на 1050 Ti можно дообучать только модели ≤3B.

---

## 1. Подготовка и сборка llama.cpp под архитектуру Pascal (CUDA 12.x)

```bash
sudo apt update && sudo apt install -y git cmake ninja-build rsync curl jq python3-pip
pip install -U huggingface_hub
mkdir -p ~/omni_auto_trainer/{colab_inbox,backups,logs} ~/models_pc
```

> [!IMPORTANT]
> **Используйте CUDA 12.x, а не CUDA 13+!**  
> В CUDA 13 была удалена поддержка архитектуры Pascal (`sm_61`). Для GTX 1050 Ti компилируйте строго с `-DCMAKE_CUDA_ARCHITECTURES=61`.

Сборка llama.cpp:
```bash
git clone https://github.com/ggml-org/llama.cpp ~/llama.cpp
cd ~/llama.cpp
cmake -B build -G Ninja -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=61 -DGGML_RPC=OFF
cmake --build build -j8
```

Загрузка MoE-учителя:
```bash
hf download unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF --include "*IQ3_XS*" --local-dir ~/models_pc/dl
mv ~/models_pc/dl/*IQ3_XS*.gguf ~/models_pc/Qwen3-Coder-30B-A3B-Instruct-IQ3_XS.gguf
rm -rf ~/models_pc/dl
```

---

## 2. Скрипт управления учителем `manage_teacher.sh`

Создайте `~/omni_auto_trainer/manage_teacher.sh`:

```bash
#!/usr/bin/env bash
# Управление локальным MoE-учителем на ПК (:8090). Без RPC, без SSH на Mi10T.
set -euo pipefail
source "$HOME/omni_auto_trainer/omni_env.sh"
ACTION="${1:-status}"
LLAMA="$LLAMA_CPP_DIR/build/bin/llama-server"
BENCH="$LLAMA_CPP_DIR/build/bin/llama-bench"
LOG="$WORK_DIR/logs/teacher.log"
PORT=8090
MODEL="${TEACHER_MODEL:-$HOME/models_pc/Qwen3-Coder-30B-A3B-Instruct-IQ3_XS.gguf}"

rotate_log() { [ -f "$LOG" ] && [ "$(stat -c%s "$LOG")" -gt 5000000 ] && tail -c 500000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"; }

stop_teacher() { pkill -f "llama-server.*--port $PORT" 2>/dev/null || true; sleep 2; }

status() {
  if curl -sf -m 2 "http://127.0.0.1:$PORT/health" >/dev/null; then echo "ONLINE"; else echo "OFFLINE"; fi
}

ensure_swap() {
  if ! swapon --show | grep -q .; then
    echo "Создаю 8G swap как страховку под 13GB модель + 16GB RAM..."
    sudo fallocate -l 8G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
  fi
}

check_cuda() {
  if command -v nvcc >/dev/null && nvcc --version | grep -qE "release 1[3-9]"; then
    echo "⚠️ CUDA 13+ не поддерживает Pascal (sm_61). Пересоберите llama.cpp с CUDA 12.x." >&2
  fi
}

start() {
  [ -f "$MODEL" ] || { echo "Нет модели: $MODEL"; exit 1; }
  check_cuda; ensure_swap; stop_teacher; rotate_log
  echo "[$(date)] start teacher" >> "$LOG"
  # -ngl 99 загружает внимание и KV в VRAM (~2.3 ГБ),
  # а -ot ".ffn_.*_exps.=CPU" держит экспертов в системной памяти DDR4
  nohup "$LLAMA" \
    -m "$MODEL" --jinja --host 0.0.0.0 --port "$PORT" \
    -ngl 99 -ot ".ffn_.*_exps.=CPU" \
    -c 16384 -ctk q8_0 -ctv q8_0 --flash-attn \
    -t 6 -tb 8 -np 1 --cache-reuse 256 \
    --temp 0.7 --top-p 0.8 --top-k 20 >> "$LOG" 2>&1 &
  sleep 3; status
}

case "$ACTION" in
  start)   start ;;
  stop)    stop_teacher; echo "stopped" ;;
  restart) stop_teacher; start ;;
  status)  status ;;
  swap)    ensure_swap ;;
  bench)   "$BENCH" -m "$MODEL" -ngl 99 -ot ".ffn_.*_exps.=CPU" -p 256 -n 64 -t 6 ;;
  *) echo "usage: $0 {start|stop|restart|status|swap|bench}"; exit 1 ;;
esac
```
```bash
chmod +x ~/omni_auto_trainer/manage_teacher.sh
```

---

## 3. Демон курации и синхронизации скилов `auto_lora_trainer.py`

Создайте `~/omni_auto_trainer/auto_lora_trainer.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Triad-Omni PC curator v4.7: skill-sync + dataset curation + Colab staging.
Локальное обучение 9B намеренно удалено (GTX 1050 Ti 4GB). Обучение — в Colab T4."""
import os, sys, json, time, hashlib, re, subprocess, urllib.request, urllib.error, fcntl
from datetime import datetime

HUB      = os.environ.get("HUB_URL", "http://192.168.1.203:8000")
TOKEN    = os.environ.get("OMNI_TOKEN", "")
NOTE4    = os.environ.get("NOTE4_IP", "192.168.1.203")
SSH_PORT = os.environ.get("SSH_PORT", "8022")
WORK     = os.path.expanduser(os.environ.get("WORK_DIR", "~/omni_auto_trainer"))
INBOX    = os.path.join(WORK, "colab_inbox")
STATE    = os.path.join(WORK, "trainer_state.json")
QUEUE    = os.path.join(WORK, "offline_skills_queue.json")
LOCK     = os.path.join(WORK, "trainer.lock")
PREPARE_STEP = 200                      # порог верифицированных пар
ADAPTER_DOMAINS = {"solder", "reva_android", "esp32"}   # под 3 слота --lora на Mi10T
BASE_FOR_DOMAIN = {d: "Qwen/Qwen3.5-9B" for d in ADAPTER_DOMAINS}
os.makedirs(INBOX, exist_ok=True)
THINK = re.compile(r"<think>.*?</think>", re.S)

def hub_req(path, payload=None, timeout=8):
    hdrs = {"Content-Type": "application/json", "X-Omni-Token": TOKEN}
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(HUB + path, data=data, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"prepared_counts": {}, "file_hashes": {}}

def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def push_skill_or_queue(payload):
    try:
        return hub_req("/v1/sync_skill", payload, timeout=6)
    except Exception:
        q = []
        if os.path.exists(QUEUE):
            try: q = json.load(open(QUEUE, encoding="utf-8"))
            except Exception: q = []
        q.append(payload)
        json.dump(q[-200:], open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False)
        return None

def flush_queue():
    if not os.path.exists(QUEUE): return
    try: q = json.load(open(QUEUE, encoding="utf-8"))
    except Exception: return
    rem = []
    for it in q:
        try: hub_req("/v1/sync_skill", it, timeout=5)
        except Exception: rem.append(it)
    json.dump(rem, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False)

def scan_skills(state, force=False):
    flush_queue()
    try:
        folders = hub_req("/v1/watched_folders", timeout=5).get("folders", [])
    except Exception:
        folders = ["~/deepseek-harness/skills", "~/.claude", "~/.cursor/rules", "~/projects/solder_blog/skills"]
    hashes = state.setdefault("file_hashes", {})
    n = 0
    for raw in folders:
        d = os.path.expanduser(raw)
        if not os.path.isdir(d): continue
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.endswith((".md", ".json", ".txt", ".cursorrules")): continue
                p = os.path.join(root, fn)
                try:
                    c = open(p, encoding="utf-8", errors="ignore").read().strip()
                    if len(c) < 20: continue
                    h = hashlib.md5(c.encode()).hexdigest()
                    if not force and hashes.get(p) == h: continue
                    if push_skill_or_queue({"topic": fn, "content": c[:3500],
                                            "source_folder": os.path.basename(d), "raw_folder": raw}):
                        hashes[p] = h; n += 1
                except Exception: pass
    if n: save_state(state); print(f"[SYNC] скилов: {n}")

def pull_dataset(dom):
    local = os.path.join(WORK, f"sft_{dom}.raw.jsonl")
    src = f"{NOTE4}:~/omni_hub/data/datasets/sft_{dom}.jsonl"
    r = subprocess.run(["scp", "-P", SSH_PORT, src, local])
    if r.returncode != 0:
        subprocess.run(["scp", "-P", SSH_PORT, f"{NOTE4}:~/omni_hub/datasets/sft_{dom}.jsonl", local], check=False)
    return local if os.path.exists(local) else None

def clean_dataset(raw, dom):
    """Только messages, без vec/domain/ts; дедуп по sha; очистка <think>."""
    out = os.path.join(INBOX, f"sft_{dom}.jsonl")
    seen, kept = set(), 0
    with open(out, "w", encoding="utf-8") as w:
        for ln in open(raw, encoding="utf-8"):
            try: rec = json.loads(ln)
            except Exception: continue
            msgs = rec.get("messages")
            if not isinstance(msgs, list) or len(msgs) < 2: continue
            u = next((m.get("content","") for m in msgs if m.get("role")=="user"), "")
            a = next((m.get("content","") for m in msgs if m.get("role")=="assistant"), "")
            if not isinstance(u,str) or not isinstance(a,str): continue
            a = THINK.sub("", a).strip()
            if len(u.strip()) < 15 or len(a) < 60: continue
            sha = hashlib.sha256((u.strip()+"\n"+a).encode()).hexdigest()
            if sha in seen: continue
            seen.add(sha)
            w.write(json.dumps({"messages":[{"role":"user","content":u},{"role":"assistant","content":a}]}, ensure_ascii=False)+"\n")
            kept += 1
    return out, kept

def stage_colab(dom, force=False):
    raw = pull_dataset(dom)
    if not raw: print(f"[{dom}] датасет не найден"); return False
    out, kept = clean_dataset(raw, dom)
    manifest = os.path.join(INBOX, f"manifest_{dom}.json")
    json.dump({"domain": dom, "base_model": BASE_FOR_DOMAIN.get(dom, "Qwen/Qwen3.5-9B"),
               "pairs": kept, "file": os.path.basename(out), "staged_at": datetime.now().isoformat(),
               "note": "Загрузить sft_<dom>.jsonl в Colab T4 (см. colab_lora_9b.py)"},
              open(manifest, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[{dom}] подготовлен Colab-пакет: {kept} пар → {out}")
    if kept < PREPARE_STEP and not force:
        print(f" ⚠️ < {PREPARE_STEP} пар: LoRA рано, копите дальше (RAG уже работает).")
    return True

def main():
    st = load_state()
    if "--sync-now" in sys.argv:
        scan_skills(st, force=True); return
    if "--force-domain" in sys.argv:
        dom = sys.argv[sys.argv.index("--force-domain")+1]
        stage_colab(dom, force=True); return
    if "--force-all" in sys.argv:
        for dom in sorted(ADAPTER_DOMAINS): stage_colab(dom, force=True)
        return
    if "--prepare-colab" in sys.argv:
        for dom in sorted(ADAPTER_DOMAINS): stage_colab(dom, force=False)
        return

    print("🔄 Curator v4.7: skill-sync + Colab staging (локального QLoRA 9B нет)")
    while True:
        try:
            scan_skills(st)
            counts = hub_req("/v1/training_status", timeout=6)
            prepared = st.setdefault("prepared_counts", {})
            for dom in ADAPTER_DOMAINS:
                cnt = counts.get(dom, 0)
                if cnt - prepared.get(dom, 0) >= PREPARE_STEP:
                    if stage_colab(dom):
                        prepared[dom] = cnt; save_state(st)
        except Exception as e:
            print(f"[WARN] {e}")
        time.sleep(60)

if __name__ == "__main__":
    with open(LOCK, "w") as lf:
        try:
            fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Уже запущен другой экземпляр тренера."); sys.exit(0)
        main()
```

---

## 4. Хук верификации кода на ПК `verify_and_learn.sh`

Создайте `~/omni_auto_trainer/verify_and_learn.sh`:

```bash
#!/usr/bin/env bash
# usage: verify_and_learn.sh <domain> <prompt_file> <reply_file> <verify_cmd...>
# Пример: verify_and_learn.sh esp32 prompt.txt reply.txt "pio run -e esp32s3"
set -uo pipefail
source "$HOME/omni_auto_trainer/omni_env.sh"
DOM="${1:?domain}"; PF="${2:?prompt_file}"; RF="${3:?reply_file}"; shift 3
VCMD="$*"
[ -n "$VCMD" ] || { echo "нет команды верификации"; exit 1; }

ERR="$(mktemp)"
if bash -c "$VCMD" >"$ERR" 2>&1; then
  echo "✅ Верификация прошла: $VCMD"; rm -f "$ERR"; exit 0
fi

echo "❌ Верификация упала → эскалация (домен=$DOM)"
python3 - "$DOM" "$PF" "$RF" "$ERR" <<'PY'
import json,sys,os,urllib.request
dom,pf,rf,ef=sys.argv[1:5]
body={"domain":dom,"prompt":open(pf,encoding="utf-8").read(),
      "reply":open(rf,encoding="utf-8").read(),"error":open(ef,encoding="utf-8",errors="ignore").read()}
req=urllib.request.Request(os.environ["HUB_URL"]+"/v1/escalate",
    data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json","X-Omni-Token":os.environ["OMNI_TOKEN"]})
with urllib.request.urlopen(req,timeout=600) as r:
    out=json.loads(r.read().decode())
fixed=out.get("fixed","")
open(rf+".fixed","w",encoding="utf-8").write(fixed)
print(f"Источник исправления: {out.get('source')} | сохранено в {rf}.fixed")
print(fixed)
PY
rm -f "$ERR"
exit 1
```
```bash
chmod +x ~/omni_auto_trainer/verify_and_learn.sh
```

---

## 5. Деплой готового LoRA-адаптера на Mi 10T `deploy_adapter.sh`

Создайте `~/omni_auto_trainer/deploy_adapter.sh`:

```bash
#!/usr/bin/env bash
# usage: deploy_adapter.sh <domain> <lora_gguf>
set -euo pipefail
source "$HOME/omni_auto_trainer/omni_env.sh"
DOM="${1:?domain}"; GGUF="${2:?gguf}"
case "$DOM" in solder|reva_android|esp32) ;; *) echo "домен без слота LoRA"; exit 1;; esac
[ -f "$GGUF" ] || { echo "нет файла $GGUF"; exit 1; }

DST="~/adapters/lora_9b_${DOM}.gguf"
# Создание резервной копии старого адаптера
ssh -p "$SSH_PORT" "$MI10T_IP" "[ -f $DST ] && cp $DST ${DST}.bak || true"
scp -P "$SSH_PORT" "$GGUF" "$MI10T_IP:$DST"

# Перезапуск llama-server раз в неделю для считывания нового весового файла
ssh -p "$SSH_PORT" "$MI10T_IP" "~/start_brain.sh router"
sleep 20

# Проверка адаптеров и сброс KV-кэша
curl -s "http://$MI10T_IP:8080/lora-adapters"; echo
case "$DOM" in solder) ID=0;; reva_android) ID=1;; esp32) ID=2;; esac
curl -s -X POST "http://$MI10T_IP:8080/lora-adapters" \
  -d "[{\"id\":0,\"scale\":$([ $ID = 0 ] && echo 1.0 || echo 0.0)},{\"id\":1,\"scale\":$([ $ID = 1 ] && echo 1.0 || echo 0.0)},{\"id\":2,\"scale\":$([ $ID = 2 ] && echo 1.0 || echo 0.0)}]"
curl -s -X POST "http://$MI10T_IP:8080/slots/0?action=erase"; echo
echo "✅ $DOM успешно деплоен на Mi 10T."
```
```bash
chmod +x ~/omni_auto_trainer/deploy_adapter.sh
```
