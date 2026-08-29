from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.4.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates tar",
        "rm -rf /var/lib/apt/lists/*",
    ])
)

srbminer_url = (
    "https://github.com/doktor83/SRBMiner-Multi/releases/"
    "download/3.5.4/"
    "SRBMiner-Multi-3-5-4-Linux.tar.gz"
)

pearl_pool = "prl.kryptex.network:7048"
pearl_wallet = "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
worker_name = "beam-4090"


@function(
    name="pearl-srbminer-4090",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=27 * 60 * 60,
)
def run_pearl():

    print("checking gpu...")

    subprocess.run(
        ["bash", "-lc", "nvidia-smi"],
        check=False,
    )

    workdir = "/workspace/srbminer"
    archive = f"{workdir}/srbminer.tar.gz"

    subprocess.run(
        ["bash", "-lc", f"mkdir -p {workdir}"],
        check=True,
    )

    print("downloading srbminer...")

    result = subprocess.run(
        [
            "wget",
            "--show-progress",
            "--tries=3",
            "--timeout=60",
            "-O",
            archive,
            srbminer_url,
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError("gagal download srbminer")

    print("checking downloaded file...")

    result = subprocess.run(
        ["bash", "-lc", f'ls -lh "{archive}"'],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError("file srbminer tidak ditemukan")

    print("checking archive...")

    result = subprocess.run(
        ["tar", "-tzf", archive],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("archive srbminer tidak valid")

    print("extracting srbminer...")

    result = subprocess.run(
        ["tar", "-xzf", archive, "-C", workdir],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError("gagal extract srbminer")

    result = subprocess.run(
        [
            "bash",
            "-lc",
            f'find "{workdir}" -type f -name "SRBMiner-MULTI" | head -n 1',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    miner = result.stdout.strip()

    if not miner:
        raise RuntimeError("srbminer tidak ditemukan")

    subprocess.run(
        ["chmod", "+x", miner],
        check=False,
    )

    wallet_worker = f"{pearl_wallet}.{worker_name}"

    print()
    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)
    print("GPU       : RTX 4090")
    print("Algorithm : pearlhash")
    print("Pool      :", pearl_pool)
    print("Worker    :", worker_name)
    print("Wallet    : configured")
    print("Miner     : SRBMiner-MULTI 3.5.4")
    print("=" * 60)
    print()

    print("starting miner...")

    command = [
        miner,
        "--disable-cpu",
        "--algorithm",
        "pearlhash",
        "--pool",
        pearl_pool,
        "--wallet",
        wallet_worker,
    ]

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
                print("[srb]", line.rstrip(), flush=True)

            if process.poll() is not None:
                break

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("stopping miner...")
        process.terminate()

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    finally:
        print("miner stopped")
        print("exit code:", process.poll())
