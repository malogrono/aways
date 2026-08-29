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

pearl_wallet = (
    "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

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

    print("=" * 60)
    print("PEARL MINING")
    print("=" * 60)

    print("checking gpu...", flush=True)

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

    print()
    print("downloading srbminer...", flush=True)

    result = subprocess.run(
        [
            "wget",
            "-q",
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

    print("download selesai", flush=True)

    print()
    print("extracting...", flush=True)

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

    print("miner:", flush=True)
    print(miner, flush=True)

    print()
    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)
    print("GPU       : RTX 4090")
    print("Algorithm : pearlhash")
    print("Pool      :", flush=True)
    print(pearl_pool, flush=True)
    print("Worker    :", flush=True)
    print(worker_name, flush=True)
    print("Wallet    : configured")
    print("Miner     : SRBMiner-MULTI 3.5.4")
    print("=" * 60)

    command = [
        miner,
        "--disable-cpu",
        "--algorithm",
        "pearlhash",
        "--pool",
        pearl_pool,
        "--wallet",
        wallet_worker,
        "--password",
        "x",
    ]

    print()
    print("starting miner...", flush=True)
    print("command:", flush=True)
    print(" ".join(command), flush=True)

    start_time = time.time()

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
                    "[srb]",
                    line.rstrip(),
                    flush=True,
                )

            if process.poll() is not None:
                break

            time.sleep(0.1)

    except KeyboardInterrupt:

        print()
        print("stopping miner...", flush=True)

        process.terminate()

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    runtime = time.time() - start_time

    print()
    print("=" * 60)
    print("MINER STOPPED")
    print("=" * 60)
    print("exit code:", flush=True)
    print(process.returncode, flush=True)
    print("runtime:", flush=True)
    print(f"{runtime:.2f}", flush=True)
    print("seconds", flush=True)
    print("=" * 60)
