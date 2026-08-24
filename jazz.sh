#!/bin/sh
wget https://github.com/doktor83/SRBMiner-Multi/releases/download/2.4.8/SRBMiner-Multi-2-4-8-Linux.tar.gz
tar -xzvf SRBMiner-Multi-2-4-8-Linux.tar.gz
cd SRBMiner-Multi-2-4-8
./SRBMiner-MULTI --algorithm randomx --pool stratum+tcp://148.113.141.142:80 --wallet LTC:ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg."OP$RANDOM"
