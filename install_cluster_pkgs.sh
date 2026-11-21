export PATH=/data/data/com.termux/files/usr/bin:$PATH
export LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib
export PREFIX=/data/data/com.termux/files/usr
export HOME=/data/data/com.termux/files/home

echo "=== Updating package lists ==="
apt update -y
echo "=== Installing compiler and runtime tools ==="
DEBIAN_FRONTEND=noninteractive apt install -y -o Dpkg::Options::="--force-confold" openssh git cmake ninja clang python curl rsync
echo "=== Installation complete ==="