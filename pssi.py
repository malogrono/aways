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
    timeout=27 * 60 * 60,
)
def run_script():

    print("=== GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
set -e

cd /tmp

TMATE="/tmp/tmate-2.4.0-static-linux-amd64/tmate"
SOCKET="/tmp/tmate.sock"
LOG="/tmp/tmate.log"

echo "========================================"
echo "=== DNS ==="
echo "========================================"

getent hosts ssh.tmate.io || true

echo "========================================"
echo "=== NETWORK ==="
echo "========================================"

curl -k -Iv \
    --connect-timeout 10 \
    --max-time 20 \
    https://ssh.tmate.io \
    2>&1 || true

echo "========================================"
echo "=== DOWNLOAD TMATE ==="
echo "========================================"

rm -rf tmate-2.4.0-static-linux-amd64
rm -f tmate.tar.xz
rm -f "$SOCKET"
rm -f "$LOG"

wget -q \
    https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
    -O tmate.tar.xz

tar -xf tmate.tar.xz

chmod +x "$TMATE"

echo "TMATE VERSION:"
"$TMATE" -V

echo "========================================"
echo "=== START TMATE ==="
echo "========================================"

"$TMATE" \
    -S "$SOCKET" \
    new-session -d \
    2>"$LOG"

echo "========================================"
echo "=== WAIT TMATE ==="
echo "========================================"

READY=0

for i in $(seq 1 60)
do
    echo "CHECK $i/60"

    cat "$LOG" 2>/dev/null || true

    if "$TMATE" \
        -S "$SOCKET" \
        wait tmate-ready \
        2>/dev/null
    then
        READY=1
        break
    fi

    sleep 2
done

echo "========================================"
echo "=== TMATE LOG ==="
echo "========================================"

cat "$LOG" 2>/dev/null || true

if [ "$READY" = "1" ]
then

    echo "========================================"
    echo "=== TMATE SSH ==="
    echo "========================================"

    "$TMATE" \
        -S "$SOCKET" \
        display -p '#{tmate_ssh}'

    echo "========================================"
    echo "=== TMATE WEB ==="
    echo "========================================"

    "$TMATE" \
        -S "$SOCKET" \
        display -p '#{tmate_web}'

else

    echo "========================================"
    echo "=== TMATE FAILED ==="
    echo "========================================"

    echo "TMATE belum mendapatkan koneksi."

fi

echo "========================================"
echo "=== GPU ==="
echo "========================================"

nvidia-smi

echo "========================================"
echo "=== KEEP ALIVE ==="
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
