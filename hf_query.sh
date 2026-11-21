export PATH=/data/data/com.termux/files/usr/bin:$PATH
curl -s -L https://huggingface.co/api/models/LiquidCloud/LFM2.5-8B-A1B-GGUF | grep -o '"rfilename":"[^"]*"'
echo "--- BGE ---"
curl -s -L https://huggingface.co/api/models/ggml-org/bge-m3-GGUF | grep -o '"rfilename":"[^"]*"'