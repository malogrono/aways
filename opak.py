from beam import function, Image
import subprocess
import time


image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates xz-utils procps",
    ])
)


@function(
    name="gpu-ssh",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,   # 30 jam
)
def run_script():

    print("=== GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
set -e

cd /tmp

TMATE="/usr/local/bin/tmate"
SOCKET="/tmp/tmate.sock"

echo "=== DOWNLOAD TMATE ==="

wget -q \
  https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
  -O /tmp/tmate.tar.xz

echo "=== EXTRACT TMATE ==="

rm -rf /tmp/tmate-2.4.0-static-linux-amd64

tar -xf /tmp/tmate.tar.xz

cp \
  /tmp/tmate-2.4.0-static-linux-amd64/tmate \
  "$TMATE"

chmod +x "$TMATE"

echo "TMATE VERSION:"
"$TMATE" -V

echo "=== START TMATE SESSION ==="

rm -f "$SOCKET"

"$TMATE" \
  -S "$SOCKET" \
  new-session -d

echo "=== WAITING FOR TMATE ==="

"$TMATE" \
  -S "$SOCKET" \
  wait tmate-ready

echo "=== TMATE READY ==="

SSH=$("$TMATE" \
  -S "$SOCKET" \
  display -p '#{tmate_ssh}')

WEB=$("$TMATE" \
  -S "$SOCKET" \
  display -p '#{tmate_web}')

echo ""
echo "=========================================="
echo "             TMATE SSH READY"
echo "=========================================="
echo ""
echo "SSH:"
echo "$SSH"
echo ""
echo "WEB:"
echo "$WEB"
echo ""
echo "=========================================="
echo ""

echo "=== GPU STATUS ==="

nvidia-smi

echo ""
echo "=== CONTAINER WILL STAY ALIVE ==="
echo "Maximum runtime: 30 hours"
echo ""

# Jangan exit walaupun kamu disconnect dari SSH.
# Container tetap hidup sampai Beam menghentikannya.
while true
do
    sleep 3600
done
"""

    subprocess.run(
        ["bash", "-lc", cmd],
        check=False
    )

    print("=== MAIN PROCESS EXITED ===")

    # Keep Python process alive as well.
    while True:
        time.sleep(3600)
