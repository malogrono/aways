from beam import function, Image
import subprocess
import time


# ============================================================
# BEAM IMAGE
# ============================================================

image = (
    Image(
        base_image="nvidia/cuda:12.4.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates",
        "rm -rf /var/lib/apt/lists/*",
    ])
)


# ============================================================
# PEARL CONFIGURATION
# ============================================================

PEARL_MINER_URL = (
    "https://pearlhash.xyz/downloads/pearl-miner-v4"
)

PEARL_POOL = "84.32.220.219:9000"

PEARL_WALLET = (
    "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

WORKER_NAME = "beam-4090"


# ============================================================
# BEAM FUNCTION
# ============================================================

@function(
    name="hama",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=27 * 60 * 60,
)
def run_pearl():

    print("=" * 60)
    print("       PEARL MINER - BEAM RTX 4090")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. CHECK GPU
    # --------------------------------------------------------

    print("\n[1] Checking GPU...")

    gpu_check = subprocess.run(
        ["bash", "-lc", "nvidia-smi"],
        check=False,
    )

    if gpu_check.returncode != 0:
        print("[WARNING] nvidia-smi gagal dijalankan.")

    # --------------------------------------------------------
    # 2. PREPARE DIRECTORY
    # --------------------------------------------------------

    workdir = "/workspace/pearl"

    subprocess.run(
        [
            "bash",
            "-lc",
            f"mkdir -p {workdir}",
        ],
        check=False,
    )

    miner = f"{workdir}/pearl-miner"

    # --------------------------------------------------------
    # 3. DOWNLOAD PEARL MINER
    # --------------------------------------------------------

    print("\n[2] Downloading Pearl Miner...")

    download_cmd = f"""
        set -e

        wget \
            --tries=3 \
            --timeout=30 \
            -O "{miner}" \
            "{PEARL_MINER_URL}"

        chmod +x "{miner}"

        echo
        echo "Miner information:"
        file "{miner}"

        echo
        echo "Miner size:"
        ls -lh "{miner}"
    """

    result = subprocess.run(
        ["bash", "-lc", download_cmd],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Gagal mendownload pearl-miner-v2."
        )

    # --------------------------------------------------------
    # 4. START MINER
    # --------------------------------------------------------

    print("\n[3] Starting Pearl Miner...")
    print()
    print("GPU    : NVIDIA RTX 4090")
    print("Pool   :", PEARL_POOL)
    print("Worker :", WORKER_NAME)
    print("Wallet : configured")
    print()

    command = [
        miner,
        "--host",
        PEARL_POOL,
        "--user",
        PEARL_WALLET,
        "--worker",
        WORKER_NAME,
    ]

    # --------------------------------------------------------
    # 5. RUN MINER
    # --------------------------------------------------------

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:

        while True:

            line = process.stdout.readline()

            if line:
                print(
                    "[PEARL]",
                    line.rstrip(),
                    flush=True,
                )

            if process.poll() is not None:
                break

            time.sleep(0.1)

    except KeyboardInterrupt:

        print("\nStopping Pearl Miner...")

        process.terminate()

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    finally:

        return_code = process.poll()

        print()
        print("=" * 60)
        print("PEARL MINER STOPPED")
        print("Exit code:", return_code)
        print("=" * 60)


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("Deploying Pearl Miner to Beam")
    print("GPU: RTX4090")
    print("=" * 60)

    run_pearl.remote()
