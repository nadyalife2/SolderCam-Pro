export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH
export LD_LIBRARY_PATH=$HOME/llama.cpp/build/bin:$LD_LIBRARY_PATH

taskset -c 6,7 $HOME/llama.cpp/build/bin/llama-bench -m $HOME/models/lfm25-8b-a1b-iq3xxs.gguf -p 256 -n 64 -t 2