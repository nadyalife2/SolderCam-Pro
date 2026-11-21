export PATH=/data/data/com.termux/files/usr/bin:$PATH
echo "=== LiquidAI files ==="
curl -s -L https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF/tree/main | grep -o 'LFM2.5-8B-A1B-[^" ]*\.gguf' | sort -u
echo "=== BGE files ==="
curl -s -L https://huggingface.co/ggml-org/bge-m3-Q8_0-GGUF/tree/main | grep -o 'bge-m3-[^" ]*\.gguf' | sort -u