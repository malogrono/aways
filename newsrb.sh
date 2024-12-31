#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/doktor63/SRBMiner/releases/download/2.6.9/SRBMiner-Multi-2-6-9-Linux.tar.gz
tar -xvf SRBMiner-Multi-2-6-9-Linux.tar.gz
cd SRBMiner-Multi-2-6-9
clear
./SRBMiner-MULTI --algorithm verushash --pool stratum+tcp://sg.vipor.net:5040 --wallet RJAkiJXQy8Q9PcBkEPTBypMJj7ofGgQjo6.flare $(echo $(shuf -i 1-9999 -n 1)-CPU) -t $(nproc --all)
while [ 1 ]; do
sleep 3
done
sleep 999
