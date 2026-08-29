from beam import function, Image
import subprocess
import time
import os

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

bzminer_url = (
    "https://github.com/bzminer/bzminer/releases/download/v24.0.2/"
    "bzminer_v24.0.2_linux.tar.gz"
)

pearl_pool = "prl.kryptex.network:7048"

pearl_wallet = (
    "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

worker_name = "beam-4090"


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
    print("PEARL MINING - BZMINER")
    print("=" * 60)

    print("checking gpu...")

    subprocess.run(
        ["bash", "-lc", "nvidia-smi"],
        check=False,
    )

    workdir = "/workspace/bzminer"
    archive = f"{workdir}/bzminer.tar.gz"

    subprocess.run(
        ["mkdir", "-p", workdir],
        check=True,
    )

    print("downloading bzminer...")
    print("url:")
    print(bzminer_url)

    result = subprocess.run(
        [
            "wget",
            "--tries=5",
            "--timeout=60",
            "--retry-connrefused",
            "--waitretry=5",
            "-O",
            archive,
            bzminer_url,
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"gagal download bzminer, exit code: {result.returncode}"
        )

    if not os.path.exists(archive):
        raise RuntimeError("file bzminer tidak ditemukan setelah download")

    size = os.path.getsize(archive)

    print("download selesai")
    print("file size:", size, "bytes")

    if size < 100000:
        raise RuntimeError(
            "file bzminer terlalu kecil, kemungkinan URL download salah"
        )

    print("extracting...")

    result = subprocess.run(
        [
            "tar",
            "-xzf",
            archive,
            "-C",
            workdir,
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"gagal extract bzminer, exit code: {result.returncode}"
        )

    result = subprocess.run(
        [
            "bash",
            "-lc",
            f'find "{workdir}" -type f \\( -name "bzminer" -o -name "bzminer-linux" \\) | head -n 1',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    miner = result.stdout.strip()

    if not miner:
        raise RuntimeError("binary bzminer tidak ditemukan")

    subprocess.run(
        ["chmod", "+x", miner],
        check=False,
    )

    print("miner:")
    print(miner)

    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)
    print("GPU       : RTX 4090")
    print("Algorithm : pearl")
    print("Pool      :")
    print(pearl_pool)
    print("Worker    :")
    print(worker_name)
    print("Wallet    : configured")
    print("Miner     : BzMiner")
    print("Version   : 24.0.2")
    print("=" * 60)

    wallet_worker = f"{pearl_wallet}/{worker_name}"

    command = [
        miner,
        "-a",
        "pearl",
        "-p",
        f"stratum+tcp://{pearl_pool}",
        "-w",
        wallet_worker,
    ]

    print("starting miner...")
    print("command:")
    print(" ".join(command))

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    start_time = time.time()

    try:

        while True:

            line = process.stdout.readline()

            if line:
                print("[bzminer]", line.rstrip(), flush=True)

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

        runtime = time.time() - start_time

        print("=" * 60)
        print("MINER STOPPED")
        print("=" * 60)
        print("exit code:")
        print(process.returncode)
        print("runtime:")
        print(f"{runtime:.2f}")
        print("seconds")
        print("=" * 60)
