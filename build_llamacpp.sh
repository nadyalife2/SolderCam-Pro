#!/data/data/com.termux/files/usr/bin/bash
set -e
export HOME=/data/data/com.termux/files/home
export PATH=/data/data/com.termux/files/usr/bin:$PATH
export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
export PREFIX=/data/data/com.termux/files/usr

cd $HOME
if [ ! -d "llama.cpp" ]; then
    echo "Cloning llama.cpp..."
    git clone --depth 1 https://github.com/ggml-org/llama.cpp
fi

cd llama.cpp
# Build Profiles:
# 1. CPU Mode (Default): Pure Kryo 585 Gold/Prime affinity
# 2. Adreno OpenCL GPU Mode: Offload matrix multiplication to Adreno 650
USE_OPENCL="${1:-cpu}"

if [ "$USE_OPENCL" = "opencl" ]; then
    echo "Configuring with Qualcomm Adreno OpenCL GPU kernels..."
    cmake -B build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DGGML_OPENCL=ON \
      -DGGML_OPENCL_USE_ADRENO_KERNELS=ON \
      -DOpenCL_LIBRARY=/vendor/lib64/libOpenCL.so \
      -DGGML_OPENMP=OFF \
      -DGGML_RPC=OFF
else
    echo "Configuring with CMake and Ninja (Pure CPU Mode)..."
    cmake -B build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DGGML_OPENMP=OFF \
      -DGGML_RPC=OFF
fi

echo "Building binaries..."
cmake --build build -j4
echo "Build finished successfully!"
ls -lh build/bin/llama-server build/bin/llama-bench