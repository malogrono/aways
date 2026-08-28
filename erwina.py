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
    timeout=30 * 60 * 60,  # 30 JAM
)
def run_script():

    print("=== GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
set -e

cd /tmp

echo "=== INSTALL TMATE ==="

wget -q \
  https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
  -O tmate.tar.xz

tar -xf tmate.tar.xz

cp tmate-2.4.0-static-linux-amd64/tmate /usr/local/bin/tmate
chmod +x /usr/local/bin/tmate

TMATE_SOCKET="/tmp/tmate.sock"

rm -f "$TMATE_SOCKET"

echo "=== START TMATE ==="

tmate \
  -S "$TMATE_SOCKET" \
  new-session -d

echo "=== WAITING FOR TMATE ==="

tmate \
  -S "$TMATE_SOCKET" \
  wait tmate-ready

sleep 3

SSH=$(tmate \
  -S "$TMATE_SOCKET" \
  display -p '#{tmate_ssh}')

WEB=$(tmate \
  -S "$TMATE_SOCKET" \
  display -p '#{tmate_web}')

echo ""
echo "======================================"
echo "           SSH CONNECTION"
echo "======================================"
echo "$SSH"
echo ""
echo "WEB:"
echo "$WEB"
echo "======================================"
echo ""

echo "=== GPU ==="
nvidia-smi

echo ""
echo "======================================"
echo "      CONTAINER WILL STAY ALIVE"
echo "             FOR 30 HOURS"
echo "======================================"
echo ""

# ----------------------------------------------------------
# JANGAN EXIT KETIKA TMATE PUTUS
# Container tetap hidup sampai Beam timeout.
# ----------------------------------------------------------

while true; do
    sleep 3600
done
"""

    subprocess.run(
        ["bash", "-lc", cmd],
        check=False
    )

    print("Container process exited.")
