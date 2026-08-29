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
    name="hama",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=27 * 60 * 60,
)
def run_pearl():

    print("checking gpu...", flush=True)

    subprocess.run(
        ["nvidia-smi"],
        check=False,
    )

    workdir = "/workspace/srbminer"
    archive = f"{workdir}/srbminer.tar.gz"

    subprocess.run(
        ["mkdir", "-p", workdir],
        check=True,
    )

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

    print("miner:", miner, flush=True)

    print("checking pearlhash support...", flush=True)

    result = subprocess.run(
        [
            miner,
            "--list-algorithms",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    algorithm_output = (
        result.stdout + "\n" + result.stderr
    )

    if "pearlhash" not in algorithm_output.lower():
        print(
            algorithm_output,
            flush=True,
        )
        raise RuntimeError(
            "pearlhash tidak ditemukan pada SRBMiner"
        )

    print("pearlhash supported", flush=True)

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

    print("starting miner...", flush=True)

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
                print(
                    "[srb]",
                    line.rstrip(),
                    flush=True,
                )

            if process.poll() is not None:
                break

            time.sleep(0.1)

    except KeyboardInterrupt:

        print("stopping miner...", flush=True)

        process.terminate()

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    finally:

        runtime = time.time() - start_time

        print()
        print("miner stopped", flush=True)
        print(
            "exit code:",
            process.poll(),
            flush=True,
        )
        print(
            "runtime:",
            round(runtime, 2),
            "seconds",
            flush=True,
        )
