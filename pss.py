from beam import function, Image
import subprocess
import time


image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget curl ca-certificates xz-utils",
    ])
)


@function(
    name="gpu-ssh",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_script():

    print("========================================")
    print("=== GPU CHECK ===")
    print("========================================")

    subprocess.run(
        ["nvidia-smi"],
        check=False
    )

    cmd = r"""
set -u

TMATE="/tmp/tmate-2.4.0-static-linux-amd64/tmate"
SOCKET="/tmp/tmate.sock"
LOG="/tmp/tmate.log"

echo
echo "========================================"
echo "=== DNS TEST ==="
echo "========================================"

getent hosts ssh.tmate.io || true

echo
echo "========================================"
echo "=== NETWORK TEST ==="
echo "========================================"

curl -Iv \
    --connect-timeout 10 \
    --max-time 20 \
    https://ssh.tmate.io \
    2>&1 || true

echo
echo "========================================"
echo "=== DOWNLOAD TMATE ==="
echo "========================================"

cd /tmp

rm -rf tmate-2.4.0-static-linux-amd64
rm -f tmate.tar.xz
rm -f "$SOCKET"
rm -f "$LOG"

wget \
    --timeout=30 \
    --tries=3 \
    -q \
    https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
    -O tmate.tar.xz

echo "TMATE ARCHIVE:"
ls -lh tmate.tar.xz

echo
echo "========================================"
echo "=== EXTRACT ==="
echo "========================================"

tar -xf tmate.tar.xz

chmod +x "$TMATE"

echo
echo "TMATE VERSION:"
"$TMATE" -V

echo
echo "========================================"
echo "=== START TMATE ==="
echo "========================================"

"$TMATE" \
    -S "$SOCKET" \
    new-session -d \
    2>"$LOG"

TMATE_PID=$!

echo "TMATE STARTED"
echo "SOCKET: $SOCKET"

echo
echo "========================================"
echo "=== WAIT FOR TMATE ==="
echo "========================================"

READY=0

for i in $(seq 1 60)
do

    echo "TMATE CHECK $i/60"

    if grep -q "ssh session:" "$LOG" 2>/dev/null
    then
        READY=1
        break
    fi

    if grep -q "Error connecting" "$LOG" 2>/dev/null
    then
        echo "TMATE CONNECTION ERROR DETECTED"
        cat "$LOG"
    fi

    sleep 2

done

echo
echo "========================================"
echo "=== TMATE LOG ==="
echo "========================================"

cat "$LOG" 2>/dev/null || true

echo
echo "========================================"
echo "=== TMATE STATUS ==="
echo "========================================"

"$TMATE" \
    -S "$SOCKET" \
    has-session \
    2>&1 || true

if [ "$READY" -eq 1 ]
then

    echo
    echo "========================================"
    echo "=== TMATE SSH ==="
    echo "========================================"

    "$TMATE" \
        -S "$SOCKET" \
        display -p '#{tmate_ssh}'

    echo
    echo "========================================"
    echo "=== TMATE WEB ==="
    echo "========================================"

    "$TMATE" \
        -S "$SOCKET" \
        display -p '#{tmate_web}'

    echo
    echo "========================================"
    echo "=== SUCCESS ==="
    echo "========================================"

else

    echo
    echo "========================================"
    echo "=== TMATE FAILED ==="
    echo "========================================"

    echo
    echo "TMATE tidak berhasil mendapatkan SSH session."

    echo
    echo "Kemungkinan masalah:"
    echo "1. Koneksi outbound Beam ke ssh.tmate.io"
    echo "2. DNS/network"
    echo "3. Koneksi tmate ditolak"
    echo "4. Server tmate tidak dapat dijangkau"

fi

echo
echo "========================================"
echo "=== FINAL GPU CHECK ==="
echo "========================================"

nvidia-smi

echo
echo "========================================"
echo "=== KEEPING CONTAINER ALIVE ==="
echo "========================================"

while true
do
    sleep 3600
done
"""

    subprocess.run(
        ["bash", "-lc", cmd],
        check=False
    )

    while True:
        time.sleep(3600)
