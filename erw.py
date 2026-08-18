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

    wget -q \
      https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz \
      -O tmate.tar.xz

    tar -xf tmate.tar.xz

    mv tmate-2.4.0-static-linux-amd64/tmate /usr/local/bin/tmate

    chmod +x /usr/local/bin/tmate

    rm -rf tmate.tar.xz tmate-2.4.0-static-linux-amd64

    echo "=== START TMATE ==="

    tmate -F > /tmp/tmate.log 2>&1 &

    sleep 10

    echo "=== TMATE LOG ==="

    cat /tmp/tmate.log

    echo "=== SSH ==="

    tmate display -p '#{tmate_ssh}'

    echo "=== WEB ==="

    tmate display -p '#{tmate_web}'

    echo "=== GPU ==="

    nvidia-smi
    """

    subprocess.run(
        ["bash", "-lc", cmd],
        check=False
    )

    print("=== GPU STAYING ALIVE ===")

    while True:
        time.sleep(3600)
