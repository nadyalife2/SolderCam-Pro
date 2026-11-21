#!/data/data/com.termux/files/usr/bin/bash
set -e
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH

cd $HOME/models

echo "=== Finishing BGE-M3 ==="
if [ ! -f "bge-m3.gguf" ]; then
    curl -C - -L -o bge-m3.gguf.tmp "https://huggingface.co/ggml-org/bge-m3-Q8_0-GGUF/resolve/main/bge-m3-q8_0.gguf"
    mv bge-m3.gguf.tmp bge-m3.gguf
fi
ls -lh bge-m3.gguf

echo "=== Downloading LFM2.5-8B-A1B (IQ3_XXS) ==="
if [ ! -f "lfm25-8b-a1b-iq3xxs.gguf" ]; then
    curl -C - -L --retry 5 --retry-delay 2 -o lfm25-8b-a1b-iq3xxs.gguf.tmp "https://huggingface.co/unsloth/LFM2.5-8B-A1B-GGUF/resolve/main/LFM2.5-8B-A1B-UD-IQ3_XXS.gguf"
    mv lfm25-8b-a1b-iq3xxs.gguf.tmp lfm25-8b-a1b-iq3xxs.gguf
fi
ls -lh lfm25-8b-a1b-iq3xxs.gguf
echo "=== ALL MODELS DOWNLOADED SUCCESSFULLY ==="