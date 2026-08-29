from beam import function, Image
import subprocess
import time
import os


# ============================================================
# IMAGE
# ============================================================

image = (
    Image(
        base_image="nvidia/cuda:12.4.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates tar gzip",
        "rm -rf /var/lib/apt/lists/*",
    ])
)


# ============================================================
# MINING CONFIGURATION
# ============================================================

BZMINER_VERSION = "25.0.0b8"

# Official BzMiner release
BZMINER_URL = (
    "https://bzminer.com/downloads/"
    "bzminer_v25.0.0b8_linux.tar.gz"
)

POOL = "prl.kryptex.network:7048"

WALLET = (
    "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

WORKER_NAME = "beam-4090"

ALGORITHM = "pearl"


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
    print("PEARL MINING - BZMINER V10")
    print("=" * 60)

    # --------------------------------------------------------
    # DIRECTORIES
    # --------------------------------------------------------

    workdir = "/workspace/bzminer"

    archive = (
        f"{workdir}/"
        f"bzminer_v{BZMINER_VERSION}_linux.tar.gz"
    )

    subprocess.run(
        ["mkdir", "-p", workdir],
        check=True,
    )

    # --------------------------------------------------------
    # GPU CHECK
    # --------------------------------------------------------

    print("checking gpu...")
    print("-" * 60)

    subprocess.run(
        ["bash", "-lc", "nvidia-smi"],
        check=False,
    )

    print("-" * 60)

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    print("downloading bzminer...")
    print("version:", BZMINER_VERSION)
    print("-" * 60)

    downloaded = False

    for attempt in range(1, 6):

        print(
            f"download attempt {attempt}/5...",
            flush=True,
        )

        try:
            if os.path.exists(archive):
                os.remove(archive)
        except Exception:
            pass

        result = subprocess.run(
            [
                "wget",
                "-q",
                "--show-progress",
                "--tries=1",
                "--timeout=90",
                "--user-agent=Mozilla/5.0",
                "-O",
                archive,
                BZMINER_URL,
            ],
            check=False,
        )

        if result.returncode == 0:

            if os.path.isfile(archive):

                size = os.path.getsize(archive)

                print(
                    f"download selesai: {size:,} bytes",
                    flush=True,
                )

                if size > 1_000_000:

                    downloaded = True
                    break

                print(
                    "file hasil download terlalu kecil",
                    flush=True,
                )

        else:

            print(
                "download gagal, exit code:",
                result.returncode,
                flush=True,
            )

        if attempt < 5:

            wait_time = attempt * 15

            print(
                f"menunggu {wait_time} detik...",
                flush=True,
            )

            time.sleep(wait_time)

    if not downloaded:

        raise RuntimeError(
            "Gagal download BzMiner. "
            "Server bzminer.com kemungkinan "
            "sedang memberikan HTTP 429."
        )

    # --------------------------------------------------------
    # CHECK ARCHIVE
    # --------------------------------------------------------

    print("=" * 60)
    print("CHECKING ARCHIVE")
    print("=" * 60)

    test_archive = subprocess.run(
        [
            "tar",
            "-tzf",
            archive,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    if test_archive.returncode != 0:

        print(
            test_archive.stdout,
            flush=True,
        )

        raise RuntimeError(
            "Archive BzMiner tidak valid."
        )

    print("archive valid")

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    print("=" * 60)
    print("EXTRACTING BZMINER")
    print("=" * 60)

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

    # --------------------------------------------------------
    # FIND BZMINER
    # --------------------------------------------------------

    result = subprocess.run(
        [
            "bash",
            "-lc",
            (
                f'find "{workdir}" '
                '-type f '
                '-name "bzminer" '
                '| head -n 1'
            ),
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
        check=True,
    )

    print("miner:")
    print(miner)

    # --------------------------------------------------------
    # VERSION
    # --------------------------------------------------------

    print("=" * 60)
    print("BZMINER VERSION")
    print("=" * 60)

    version_result = subprocess.run(
        [miner, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    if version_result.stdout:

        print(
            version_result.stdout.strip(),
            flush=True,
        )

    # --------------------------------------------------------
    # MINING CONFIGURATION
    # --------------------------------------------------------

    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)

    print("GPU       : RTX 4090")
    print("Algorithm : pearl")
    print("Pool      :")
    print(POOL)
    print("Worker    :")
    print(WORKER_NAME)
    print("Wallet    : configured")
    print("Miner     : BzMiner")
    print("Version   :", BZMINER_VERSION)

    print("=" * 60)

    # --------------------------------------------------------
    # OFFICIAL KRYPTEX BZMINER COMMAND
    # --------------------------------------------------------

    pool_url = (
        "stratum+tcp://"
        + POOL
    )

    wallet_worker = (
        WALLET
        + "/"
        + WORKER_NAME
    )

    command = [
        miner,

        "-a",
        ALGORITHM,

        "-p",
        pool_url,

        "-w",
        wallet_worker,

        "--nvidia",
        "1",

        "--amd",
        "1",

        "--intel",
        "1",

        "--igpu",
        "0",

        "--cpu",
        "0",

        "--cpu_threads",
        "0",

        "--nc",
        "1",
    ]

    # --------------------------------------------------------
    # SHOW COMMAND
    # --------------------------------------------------------

    print("starting miner...")
    print("=" * 60)

    print("command:")

    print(
        " ".join(command),
        flush=True,
    )

    print("=" * 60)

    # --------------------------------------------------------
    # START MINER
    # --------------------------------------------------------

    start_time = time.time()

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # --------------------------------------------------------
    # STATUS FLAGS
    # --------------------------------------------------------

    connected = False
    hashing = False
    share_submitted = False
    share_accepted = False
    share_rejected = False

    # --------------------------------------------------------
    # MONITOR OUTPUT
    # --------------------------------------------------------

    try:

        while True:

            line = process.stdout.readline()

            if line:

                text = line.rstrip()

                print(
                    "[bzminer]",
                    text,
                    flush=True,
                )

                lower = text.lower()

                # --------------------------------------------
                # CONNECTION
                # --------------------------------------------

                connection_words = [
                    "connected",
                    "stratum connected",
                    "connection established",
                    "subscribed",
                ]

                if any(
                    word in lower
                    for word in connection_words
                ):

                    if not connected:

                        connected = True

                        print(
                            "=" * 60,
                            flush=True,
                        )

                        print(
                            "STATUS: POOL CONNECTED",
                            flush=True,
                        )

                        print(
                            "=" * 60,
                            flush=True,
                        )

                # --------------------------------------------
                # HASHRATE
                # --------------------------------------------

                hash_words = [
                    "hashrate",
                    "hash rate",
                    "h/s",
                    "kh/s",
                    "mh/s",
                    "gh/s",
                    "th/s",
                ]

                if any(
                    word in lower
                    for word in hash_words
                ):

                    if not hashing:

                        hashing = True

                        print(
                            "=" * 60,
                            flush=True,
                        )

                        print(
                            "STATUS: HASHRATE DETECTED",
                            flush=True,
                        )

                        print(
                            "=" * 60,
                            flush=True,
                        )

                # --------------------------------------------
                # SHARE SUBMITTED
                # --------------------------------------------

                submit_words = [
                    "share submitted",
                    "submitted share",
                    "share accepted",
                    "accepted share",
                ]

                if any(
                    word in lower
                    for word in submit_words
                ):

                    share_submitted = True

                    print(
                        "STATUS: SHARE SUBMISSION DETECTED",
                        flush=True,
                    )

                # --------------------------------------------
                # SHARE ACCEPTED
                # --------------------------------------------

                accepted_words = [
                    "share accepted",
                    "accepted share",
                    "accepted",
                ]

                if any(
                    word in lower
                    for word in accepted_words
                ):

                    if (
                        "rejected" not in lower
                        and "reject" not in lower
                    ):

                        share_accepted = True

                        print(
                            "=" * 60,
                            flush=True,
                        )

                        print(
                            "STATUS: SHARE ACCEPTED",
                            flush=True,
                        )

                        print(
                            "=" * 60,
                            flush=True,
                        )

                # --------------------------------------------
                # SHARE REJECTED
                # --------------------------------------------

                if (
                    "share rejected" in lower
                    or "rejected share" in lower
                    or "reject" in lower
                ):

                    share_rejected = True

                    print(
                        "WARNING: SHARE REJECTED",
                        flush=True,
                    )

            # -----------------------------------------------
            # PROCESS EXIT
            # -----------------------------------------------

            if process.poll() is not None:

                break

            time.sleep(0.1)

    except KeyboardInterrupt:

        print(
            "stopping bzminer...",
            flush=True,
        )

        process.terminate()

        try:

            process.wait(
                timeout=10
            )

        except subprocess.TimeoutExpired:

            process.kill()

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    runtime = time.time() - start_time

    exit_code = process.returncode

    print("=" * 60)
    print("MINER STOPPED")
    print("=" * 60)

    print("exit code:")
    print(exit_code)

    print("runtime:")
    print(
        f"{runtime:.2f}"
    )

    print("seconds")

    print("=" * 60)
    print("FINAL MINING STATUS")
    print("=" * 60)

    print(
        "Pool connected :",
        "YES" if connected else "NO",
    )

    print(
        "Hashrate       :",
        "YES" if hashing else "NO",
    )

    print(
        "Share submitted:",
        "YES" if share_submitted else "NO",
    )

    print(
        "Share accepted :",
        "YES" if share_accepted else "NO",
    )

    print(
        "Share rejected :",
        "YES" if share_rejected else "NO",
    )

    print("=" * 60)

    # --------------------------------------------------------
    # FINAL DIAGNOSTIC
    # --------------------------------------------------------

    if connected and hashing and share_accepted:

        print(
            "RESULT: MINING BERHASIL",
            flush=True,
        )

    elif connected and hashing:

        print(
            "RESULT: CONNECTED + HASHING, "
            "BELUM ADA ACCEPTED SHARE",
            flush=True,
        )

    elif connected:

        print(
            "RESULT: POOL CONNECTED, "
            "HASHRATE BELUM TERDETEKSI",
            flush=True,
        )

    else:

        print(
            "RESULT: BELUM TERBUKTI MINING",
            flush=True,
        )

    print("=" * 60)
