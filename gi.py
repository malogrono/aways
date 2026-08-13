from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y curl ca-certificates unzip git",
    ])
)


@function(
    name="t4x3-runner",
    image=image,
    gpu="RTX4090",
    cpu=4,
    memory="8Gi",
    timeout=4 * 60 * 60,
)
def run_script():
    # cek GPU
    subprocess.run(["nvidia-smi"], check=False)

    cmd = """
    set -e

    echo "=== DOWNLOAD FILE ==="
    curl -sL -q https://github.com/hujisanda/root/releases/download/nwe/pan.zip -O pan.zip

    echo "=== CHECK DOWNLOAD ==="
    ls -lh /tmp/pan.zip

    echo "=== EXTRACT ==="
    mkdir -p /tmp/work
    unzip -o /tmp/pan.zip -d /tmp/work

    echo "=== SET PERMISSION ==="
    chmod -R +x /tmp/work

    echo "=== WORKLOAD START ==="

    # =====================================================
    # ./bash --algo ethash --pool stratum+tcp://ethash.unmineable.com:3333 --user LTC:ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg.kacung --ethstratum ETHPROX
    # =====================================================


    # =====================================================
    # SELESAI
    # =====================================================

    echo "=== WORKLOAD FINISHED ==="
    """

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print("Process exited with:", result.returncode)

    # Untuk pengujian saja:
    print("Keeping the container alive...")
    time.sleep(4 * 60 * 60)
