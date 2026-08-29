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

bzminer_version = "24.0.2"

bzminer_url = (
    "https://bzminer.com/downloads/"
    f"bzminer_v{bzminer_version}_linux.tar.gz"
)

pearl_pool = "stratum+tcp://prl.kryptex.network:7048"

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

    print("=" * 60, flush=True)
    print("PEARL MINING - BZMINER", flush=True)
    print("=" * 60, flush=True)

    print()
    print("checking gpu...", flush=True)

    subprocess.run(
        ["bash", "-lc", "nvidia-smi"],
        check=False,
    )

    workdir = "/workspace/bzminer"
    archive = f"{workdir}/bzminer.tar.gz"

    subprocess.run(
        ["bash", "-lc", f"mkdir -p {workdir}"],
        check=True,
    )

    print()
    print("downloading bzminer...", flush=True)
    print("version:", bzminer_version, flush=True)

    result = subprocess.run(
        [
            "wget",
            "-q",
            "--show-progress",
            "--tries=3",
            "--timeout=60",
            "-O",
            archive,
            bzminer_url,
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "gagal download bzminer"
        )

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
        raise RuntimeError(
            "gagal extract bzminer"
        )

    print("extract selesai", flush=True)

    print()
    print("searching bzminer binary...", flush=True)

    result = subprocess.run(
        [
            "bash",
            "-lc",
            f'find "{workdir}" -type f -name "bzminer" | head -n 1',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    miner = result.stdout.strip()

    if not miner:
        raise RuntimeError(
            "binary bzminer tidak ditemukan"
        )

    subprocess.run(
        ["chmod", "+x", miner],
        check=False,
    )

    print("miner:", flush=True)
    print(miner, flush=True)

    print()
    print("=" * 60, flush=True)
    print("MINING CONFIGURATION", flush=True)
    print("=" * 60, flush=True)
    print("GPU       : RTX 4090", flush=True)
    print("Algorithm : pearl", flush=True)
    print("Pool      :", flush=True)
    print(pearl_pool, flush=True)
    print("Worker    :", flush=True)
    print(worker_name, flush=True)
    print("Wallet    : configured", flush=True)
    print("Miner     : BzMiner", flush=True)
    print("Version   :", bzminer_version, flush=True)
    print("=" * 60, flush=True)

    wallet_worker = (
        f"{pearl_wallet}/{worker_name}"
    )

    command = [
        miner,
        "-a",
        "pearl",
        "-p",
        pearl_pool,
        "-w",
        wallet_worker,
        "--nvidia",
        "1",
        "--amd",
        "0",
        "--intel",
        "0",
        "--igpu",
        "0",
        "--cpu",
        "0",
        "--cpu_threads",
        "0",
        "--nc",
        "1",
    ]

    print()
    print("starting miner...", flush=True)
    print("command:", flush=True)
    print(" ".join(command), flush=True)
    print()

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
                    "[bz]",
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
    print("=" * 60, flush=True)
    print("MINER STOPPED", flush=True)
    print("=" * 60, flush=True)
    print("exit code:", flush=True)
    print(process.returncode, flush=True)
    print("runtime:", flush=True)
    print(f"{runtime:.2f}", flush=True)
    print("seconds", flush=True)
    print("=" * 60, flush=True)
