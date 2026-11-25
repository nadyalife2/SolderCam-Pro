#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Triad-Omni Model Downloader (Safe Resume with -f Guard)
# ==============================================================================
set -e
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH

mkdir -p "$HOME/models"
cd "$HOME/models"

TARGET="${1:-all}"

# 1. BGE-M3 (Node-2 Nord N10, Vector Embeddings)
if [ "$TARGET" = "all" ] || [ "$TARGET" = "bge" ] || [ "$TARGET" = "node2" ]; then
    echo "=== [1/3] Downloading BGE-M3 Embedding Model ==="
    if [ ! -f "bge-m3.gguf" ] || [ $(stat -c%s "bge-m3.gguf" 2>/dev/null || echo 0) -lt 500000000 ]; then
        curl -f -C - -L -o bge-m3.gguf.tmp "https://huggingface.co/ggml-org/bge-m3-Q8_0-GGUF/resolve/main/bge-m3-q8_0.gguf"
        mv bge-m3.gguf.tmp bge-m3.gguf
    fi
    echo "✅ BGE-M3 ready: $(ls -lh bge-m3.gguf)"
fi

# 2. Reflex Fast LLM (Node-2 Nord N10: Qwen2.5-3B-Instruct Q4_K_M)
if [ "$TARGET" = "all" ] || [ "$TARGET" = "qwen" ] || [ "$TARGET" = "reflex" ] || [ "$TARGET" = "node2" ]; then
    echo "=== [2/3] Downloading Qwen2.5-3B-Instruct Reflex LLM (Q4_K_M) ==="
    if [ ! -f "qwen2.5-3b-instruct-q4_k_m.gguf" ] || [ $(stat -c%s "qwen2.5-3b-instruct-q4_k_m.gguf" 2>/dev/null || echo 0) -lt 2000000000 ]; then
        curl -f -C - -L -o qwen2.5-3b-instruct-q4_k_m.gguf.tmp "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
        mv qwen2.5-3b-instruct-q4_k_m.gguf.tmp qwen2.5-3b-instruct-q4_k_m.gguf
    fi
    echo "✅ Qwen2.5-3B ready: $(ls -lh qwen2.5-3b-instruct-q4_k_m.gguf)"
fi

# 3. Brain LLM (Node-1 Mi 10T 5G, Main 9B/7B Brain)
if [ "$TARGET" = "all" ] || [ "$TARGET" = "brain" ] || [ "$TARGET" = "node1" ]; then
    echo "=== [3/3] Downloading Main Brain Model (Qwen2.5-7B / Qwen3.5-9B) ==="
    if [ ! -f "brain.gguf" ] || [ $(stat -c%s "brain.gguf" 2>/dev/null || echo 0) -lt 3000000000 ]; then
        # Default high-performance Quant: Qwen2.5-7B-Instruct-Q4_K_M
        BRAIN_URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
        echo "[*] Downloading from $BRAIN_URL ..."
        curl -f -C - -L -o brain.gguf.tmp "$BRAIN_URL"
        mv brain.gguf.tmp brain.gguf
    fi
    echo "✅ Main Brain ready: $(ls -lh brain.gguf)"
fi

echo "🎉 All requested models are verified and ready in $HOME/models!"
