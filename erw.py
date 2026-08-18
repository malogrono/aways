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

echo "=== DOWNLOAD TMATE ==="

wget -q \
https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
-O tmate.tar.xz

echo "=== EXTRACT ==="

tar -xf tmate.tar.xz

chmod +x "$TMATE"

echo "=== TMATE VERSION ==="

"$TMATE" -V

echo "=== START TMATE ==="

rm -f "$SOCKET"

"$TMATE" \
    -S "$SOCKET" \
    new-session -d /bin/bash

echo "=== WAIT TMATE ==="

"$TMATE" \
    -S "$SOCKET" \
    wait tmate-ready

echo "=== TMATE SSH ==="

"$TMATE" \
    -S "$SOCKET" \
    display -p '#{tmate_ssh}'

echo "=== TMATE WEB ==="

"$TMATE" \
    -S "$SOCKET" \
    display -p '#{tmate_web}'

echo "=== TMATE PROCESS ==="

ps aux | grep '[t]mate'

echo "=== GPU ==="

nvidia-smi

echo "=== CONTAINER READY ==="

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
