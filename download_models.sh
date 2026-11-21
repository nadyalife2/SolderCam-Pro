#!/data/data/com.termux/files/usr/bin/bash
set -e
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH

mkdir -p $HOME/models
cd $HOME/models

echo "=== Downloading BGE-M3 Embedding Model ==="
if [ ! -f "bge-m3.gguf" ] || [ $(stat -c%s "bge-m3.gguf" 2>/dev/null || echo 0) -lt 500000000 ]; then
    curl -C - -L -o bge-m3.gguf.tmp "https://huggingface.co/ggml-org/bge-m3-Q8_0-GGUF/resolve/main/bge-m3-q8_0.gguf"
    mv bge-m3.gguf.tmp bge-m3.gguf
fi
echo "? BGE-M3 ready: $(ls -lh bge-m3.gguf)"

echo "=== Downloading LFM2.5-8B-A1B Reflex LLM (IQ3_XXS) ==="
if [ ! -f "lfm25-8b-a1b-iq3xxs.gguf" ] || [ $(stat -c%s "lfm25-8b-a1b-iq3xxs.gguf" 2>/dev/null || echo 0) -lt 2500000000 ]; then
    curl -C - -L -o lfm25-8b-a1b-iq3xxs.gguf.tmp "https://huggingface.co/unsloth/LFM2.5-8B-A1B-GGUF/resolve/main/LFM2.5-8B-A1B-UD-IQ3_XXS.gguf"
    mv lfm25-8b-a1b-iq3xxs.gguf.tmp lfm25-8b-a1b-iq3xxs.gguf
fi
echo "? LFM2.5 ready: $(ls -lh lfm25-8b-a1b-iq3xxs.gguf)"