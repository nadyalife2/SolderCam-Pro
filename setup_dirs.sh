export HOME=/data/data/com.termux/files/home
cp /data/local/tmp/omni_env.sh $HOME/omni_env.sh
chmod 600 $HOME/omni_env.sh
mkdir -p $HOME/models $HOME/models/dl $HOME/.termux/boot $HOME/.ssh
echo "omni_env created:"
ls -la $HOME/omni_env.sh