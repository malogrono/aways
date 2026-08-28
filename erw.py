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
    name="gpu-ssh",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_script():

    print("=== GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
    set -e

    cd /tmp

    echo "=== DOWNLOAD TMATE ==="

    wget -q \
      https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
      -O tmate.tar.xz

    echo "=== EXTRACT ==="

    tar -xf tmate.tar.xz

    cp tmate-2.4.0-static-linux-amd64/tmate /usr/local/bin/tmate
    chmod +x /usr/local/bin/tmate

    echo "=== START TMATE ==="

    tmate -F > /tmp/tmate.log 2>&1 &

    TMATE_PID=$!

    echo "TMATE PID: $TMATE_PID"

    echo "=== WAITING FOR TMATE ==="

    for i in $(seq 1 30); do
        if tmate display -p '#{tmate_ssh}' >/tmp/tmate_ssh 2>/dev/null; then
            SSH=$(cat /tmp/tmate_ssh)

            if [ -n "$SSH" ]; then
                echo ""
                echo "======================================"
                echo "          TMATE SSH READY"
                echo "======================================"
                echo "$SSH"
                echo "======================================"
                echo ""

                echo "=== WEB ==="
                tmate display -p '#{tmate_web}' || true

                echo ""
                echo "=== GPU ==="
                nvidia-smi

                break
            fi
        fi

        echo "Waiting... $i/30"
        sleep 2
    done

    echo ""
    echo "=== TMATE LOG ==="
    cat /tmp/tmate.log || true

    echo ""
    echo "=== GPU STATUS ==="
    nvidia-smi

    echo ""
    echo "=== CONTAINER STAYING ALIVE ==="

    while kill -0 $TMATE_PID 2>/dev/null; do
        sleep 30
    done

    echo "TMATE STOPPED"
    """

    subprocess.run(
        ["bash", "-lc", cmd],
        check=False
    )

    print("=== GPU STAYING ALIVE ===")

    while True:
        time.sleep(3600)
```
