#!/bin/bash

set -e

echo "[+] Mengecek arsitektur..."
ARCH=$(uname -m)

if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "amd64" ]; then
    echo "[-] Script ini khusus Linux x86_64/amd64."
    echo "    Arsitektur terdeteksi: $ARCH"
    exit 1
fi

echo "[+] Mengambil release Upterm terbaru..."

URL=$(curl -fsSL \
  https://api.github.com/repos/owenthereal/upterm/releases/latest |
  grep -o 'https://[^"]*upterm[^"]*Linux[^"]*x86_64[^"]*' |
  head -n1)

if [ -z "$URL" ]; then
    echo "[-] Tidak menemukan binary Upterm terbaru."
    exit 1
fi

echo "[+] Download:"
echo "$URL"

wget -O upterm "$URL"
chmod +x upterm

echo "[+] Menjalankan Upterm..."
echo

./upterm host
