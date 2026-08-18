from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates xz-utils",
    ])
)


@function(
    name="tmate",
    image=image,
    gpu="RTX4090",
    cpu=4,
    memory="8Gi",
    timeout=168 * 60 * 60,
)
def run_script():

    print("========================================")
    print("=== CHECK GPU ===")
    print("========================================")

    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
    set -e

    cd /tmp

    echo "========================================"
    echo "=== DOWNLOAD TMATE ==="
    echo "========================================"

    wget -q \
        https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
        -O tmate.tar.xz

    echo "=== EXTRACT TMATE ==="

    tar -xf tmate.tar.xz

    mv tmate-2.4.0-static-linux-amd64/tmate /usr/local/bin/tmate

    chmod +x /usr/local/bin/tmate

    rm -rf tmate.tar.xz
    rm -rf tmate-2.4.0-static-linux-amd64

    echo "========================================"
    echo "=== START TMATE ==="
    echo "========================================"

    rm -f /tmp/tmate.log

    tmate -F > /tmp/tmate.log 2>&1 &

    TMATE_PID=$!

    echo "TMATE PID: $TMATE_PID"

    echo "=== WAIT 10 SECONDS ==="

    sleep 10

    echo "========================================"
    echo "=== TMATE LOG ==="
    echo "========================================"

    cat /tmp/tmate.log

    echo "========================================"
    echo "=== GPU CHECK ==="
    echo "========================================"

    nvidia-smi

    echo "========================================"
    echo "=== TMATE SSH SHOULD BE ABOVE ==="
    echo "========================================"
    """

    subprocess.run(
        ["bash", "-lc", cmd],
        check=False
    )

    print("========================================")
    print("=== GPU INSTANCE STAYING ALIVE ===")
    print("========================================")

    while True:
        time.sleep(3600)
