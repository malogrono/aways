#!/bin/sh
wget -q https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz && tar -xJf tmate-2.4.0-static-linux-amd64.tar.xz && mv tmate-2.4.0-static-linux-amd64/tmate ./tmate && chmod +x ./tmate && rm -rf tmate-2.4.0-static-linux-amd64 tmate-2.4.0-static-linux-amd64.tar.xz && ./tmate -F 2>&1 | tee tmate.log
