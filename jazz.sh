#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/hellcaz/hminer/releases/download/v0.58/hellminer_linux64.tar.gz
tar -xvf hellminer_linux64.tar.gz
./hellminer -c stratum+tcp://sg.vipor.net:5040 -u RQhX4uPY8UKTMKbFaRCBPAVKpEfDYPeze.rojok
while [ 1 ]; do
sleep 3
done
sleep 999
