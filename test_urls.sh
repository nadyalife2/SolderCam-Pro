export PATH=/data/data/com.termux/files/usr/bin:$PATH
echo "Testing BGE-M3:"
curl -r 0-1024 -s -L -o /dev/null -w "HTTP %{http_code}, size: %{size_download}\n" https://huggingface.co/ggml-org/bge-m3-Q8_0-GGUF/resolve/main/bge-m3-q8_0.gguf
echo "Testing LFM2.5:"
curl -r 0-1024 -s -L -o /dev/null -w "HTTP %{http_code}, size: %{size_download}\n" https://huggingface.co/unsloth/LFM2.5-8B-A1B-GGUF/resolve/main/LFM2.5-8B-A1B-UD-IQ3_XXS.gguf