export PATH=/data/data/com.termux/files/usr/bin:$PATH
curl -s -L https://huggingface.co/unsloth/LFM2.5-8B-A1B-GGUF/tree/main | grep -o 'LFM2.5-8B-A1B-[^" ]*IQ3_XXS[^" ]*\.gguf' | sort -u