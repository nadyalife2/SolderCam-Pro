export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH
export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
export PREFIX=/data/data/com.termux/files/usr

cd $HOME/llama.cpp
cmake --build build --target llama-server llama-bench -j4
ls -lh build/bin/llama-server build/tools/llama-bench