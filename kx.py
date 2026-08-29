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
        "apt-get install -y wget ca-certificates tar lshw",
        "rm -rf /var/lib/apt/lists/*",
    ])
)


bzminer_url = (
    "https://bzminer.com/downloads/"
    "bzminer_v24.0.2_linux.tar.gz"
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

    print("=" * 60)
    print("PEARL MINING - BZMINER V8")
    print("=" * 60)

    # ---------------------------------------------------------
    # GPU CHECK
    # ---------------------------------------------------------

    print("checking gpu...")
    print()

    subprocess.run(
        ["bash", "-lc", "nvidia-smi"],
        check=False,
    )

    # ---------------------------------------------------------
    # DIRECTORIES
    # ---------------------------------------------------------

    workdir = "/workspace/bzminer"
    archive = f"{workdir}/bzminer.tar.gz"

    subprocess.run(
        ["mkdir", "-p", workdir],
        check=True,
    )

    # ---------------------------------------------------------
    # DOWNLOAD
    # ---------------------------------------------------------

    print("downloading bzminer...")
    print("version: 24.0.2")
    print()

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
            f"gagal download bzminer: exit code {result.returncode}"
        )

    if not os.path.exists(archive):
        raise RuntimeError(
            "file bzminer tidak ditemukan"
        )

    file_size = os.path.getsize(archive)

    print()
    print("download selesai")
    print("file size:", file_size, "bytes")

    if file_size < 100000:
        raise RuntimeError(
            "file bzminer terlalu kecil"
        )

    # ---------------------------------------------------------
    # EXTRACT
    # ---------------------------------------------------------

    print()
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
            f"gagal extract bzminer: exit code {result.returncode}"
        )

    # ---------------------------------------------------------
    # FIND MINER
    # ---------------------------------------------------------

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

    print()
    print("miner:")
    print(miner)

    # ---------------------------------------------------------
    # VERSION TEST
    # ---------------------------------------------------------

    print()
    print("checking bzminer version...")

    version_result = subprocess.run(
        [miner, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    version_output = (
        version_result.stdout.strip()
        or version_result.stderr.strip()
    )

    if version_output:
        print(version_output)

    # ---------------------------------------------------------
    # CREATE OWN CONFIG
    # ---------------------------------------------------------
    #
    # BzMiner normally loads config.txt from its working
    # directory. We remove the supplied config so there is
    # no ambiguity about which Pearl configuration is used.
    #
    # ---------------------------------------------------------

    miner_dir = os.path.dirname(miner)
    config_file = os.path.join(miner_dir, "config.txt")

    if os.path.exists(config_file):

        print()
        print("removing bundled config.txt...")

        try:
            os.remove(config_file)
        except Exception as e:
            print("warning:", e)

    # ---------------------------------------------------------
    # WALLET / WORKER
    # ---------------------------------------------------------

    wallet_worker = (
        f"{pearl_wallet}/{worker_name}"
    )

    # ---------------------------------------------------------
    # DISPLAY CONFIGURATION
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)
    print("GPU       : RTX 4090")
    print("Algorithm : pearl / PearlHash")
    print("Pool      :")
    print(pearl_pool)
    print("Worker    :")
    print(worker_name)
    print("Wallet    : configured")
    print("Miner     : BzMiner")
    print("Version   : 24.0.2")
    print("=" * 60)

    # ---------------------------------------------------------
    # MINER COMMAND
    # ---------------------------------------------------------

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
    print("starting miner...")
    print()
    print("command:")
    print(" ".join(command))
    print()

    # ---------------------------------------------------------
    # START BZMINER
    # ---------------------------------------------------------

    process = subprocess.Popen(
        command,
        cwd=miner_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    start_time = time.time()

    connected = False
    hashing = False
    accepted = 0
    rejected = 0

    # ---------------------------------------------------------
    # MONITOR
    # ---------------------------------------------------------

    try:

        while True:

            line = process.stdout.readline()

            if line:

                text = line.rstrip()

                lower = text.lower()

                # Detect pool connection
                if (
                    "connected" in lower
                    or "connection established" in lower
                    or "stratum" in lower
                ):
                    connected = True

                # Detect hashing / hashrate
                if (
                    "hashrate" in lower
                    or "hash rate" in lower
                    or "h/s" in lower
                    or "kh/s" in lower
                    or "mh/s" in lower
                    or "gh/s" in lower
                ):
                    hashing = True

                # Detect accepted
                if (
                    "accepted" in lower
                    or "share accepted" in lower
                ):
                    accepted += 1

                # Detect rejected
                if (
                    "rejected" in lower
                    or "share rejected" in lower
                ):
                    rejected += 1

                # Only print useful lines
                important = (
                    "connected" in lower
                    or "stratum" in lower
                    or "pearl" in lower
                    or "hashrate" in lower
                    or "hash rate" in lower
                    or "accepted" in lower
                    or "rejected" in lower
                    or "share" in lower
                    or "error" in lower
                    or "warning" in lower
                    or "gpu" in lower
                    or "difficulty" in lower
                    or "job" in lower
                )

                if important:
                    print(
                        "[bzminer]",
                        text,
                        flush=True,
                    )

            # -------------------------------------------------
            # PROCESS EXIT
            # -------------------------------------------------

            if process.poll() is not None:
                break

            time.sleep(0.05)

    except KeyboardInterrupt:

        print()
        print("stopping miner...")

        process.terminate()

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    finally:

        runtime = time.time() - start_time

        # -----------------------------------------------------
        # FINAL STATUS
        # -----------------------------------------------------

        print()
        print("=" * 60)
        print("MINING STATUS")
        print("=" * 60)

        print(
            "Pool connection :",
            "CONNECTED" if connected else "NOT CONFIRMED",
        )

        print(
            "Hashing         :",
            "DETECTED" if hashing else "NOT CONFIRMED",
        )

        print(
            "Accepted shares :",
            accepted,
        )

        print(
            "Rejected shares :",
            rejected,
        )

        print(
            "Exit code       :",
            process.returncode,
        )

        print(
            "Runtime         :",
            f"{runtime:.2f}",
            "seconds",
        )

        print("=" * 60)
