from beam import function, Image
import subprocess
import time
import os
import tarfile
import urllib.request


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
# CONFIGURATION
# ============================================================

# BzMiner release yang digunakan
BZMINER_VERSION = "25.0.0b8"

# URL resmi BzMiner
BZMINER_URL = (
    "https://www.bzminer.com/downloads/"
    "bzminer_v25.0.0b8_linux.tar.gz"
)

POOL = "prl.kryptex.network:7048"

WALLET = (
    "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

WORKER = "beam-4090"

WORKDIR = "/workspace/bzminer"

ARCHIVE = f"{WORKDIR}/bzminer.tar.gz"


# ============================================================
# HELPER
# ============================================================

def run_command(command, timeout=None):
    print("")
    print("COMMAND:")
    print(command)

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )

    if result.stdout:
        print(result.stdout, flush=True)

    print("EXIT CODE:", result.returncode)

    return result


# ============================================================
# BEAM FUNCTION
# ============================================================

@function(
    name="pearl-bzminer-v11",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=27 * 60 * 60,
)
def run_pearl():

    print("")
    print("=" * 60)
    print("PEARL MINING - BZMINER V11")
    print("=" * 60)

    # --------------------------------------------------------
    # GPU CHECK
    # --------------------------------------------------------

    print("")
    print("checking gpu...")
    print("-" * 60)

    gpu = subprocess.run(
        ["nvidia-smi"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    print(gpu.stdout, flush=True)

    if gpu.returncode != 0:
        raise RuntimeError(
            "nvidia-smi gagal. GPU tidak tersedia."
        )

    # --------------------------------------------------------
    # PREPARE DIRECTORY
    # --------------------------------------------------------

    os.makedirs(WORKDIR, exist_ok=True)

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print("DOWNLOADING BZMINER")
    print("=" * 60)

    print("version:")
    print(BZMINER_VERSION)

    print("URL:")
    print(BZMINER_URL)

    print("")

    # Hapus file lama jika ada
    if os.path.exists(ARCHIVE):
        os.remove(ARCHIVE)

    downloaded = False

    # --------------------------------------------------------
    # METHOD 1 - WGET
    # --------------------------------------------------------

    print("download method 1: wget")

    for attempt in range(1, 4):

        print("")
        print(
            f"download attempt {attempt}/3..."
        )

        result = subprocess.run(
            [
                "wget",
                "-O",
                ARCHIVE,
                "--server-response",
                "--tries=1",
                "--timeout=60",
                "--user-agent=Mozilla/5.0",
                BZMINER_URL,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

        if result.stdout:
            print(
                result.stdout[-4000:],
                flush=True,
            )

        if (
            result.returncode == 0
            and os.path.exists(ARCHIVE)
            and os.path.getsize(ARCHIVE) > 100000
        ):
            downloaded = True
            print("")
            print("download berhasil")
            break

        print("")
        print(
            "download gagal, exit code:",
            result.returncode,
        )

        if attempt < 3:
            wait_time = attempt * 10
            print(
                f"menunggu {wait_time} detik..."
            )
            time.sleep(wait_time)

    # --------------------------------------------------------
    # METHOD 2 - PYTHON URLOPEN
    # --------------------------------------------------------

    if not downloaded:

        print("")
        print("=" * 60)
        print("DOWNLOAD METHOD 2 - PYTHON")
        print("=" * 60)

        try:

            request = urllib.request.Request(
                BZMINER_URL,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(X11; Linux x86_64) "
                        "AppleWebKit/537.36 "
                        "Chrome/120 Safari/537.36"
                    )
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=90,
            ) as response:

                status = response.status

                print(
                    "HTTP STATUS:",
                    status,
                )

                if status != 200:
                    raise RuntimeError(
                        f"HTTP status {status}"
                    )

                with open(
                    ARCHIVE,
                    "wb",
                ) as output:

                    while True:

                        chunk = response.read(
                            1024 * 1024
                        )

                        if not chunk:
                            break

                        output.write(chunk)

            if (
                os.path.exists(ARCHIVE)
                and os.path.getsize(ARCHIVE) > 100000
            ):
                downloaded = True

                print(
                    "download berhasil"
                )

        except Exception as e:

            print(
                "python download error:",
                repr(e),
            )

    # --------------------------------------------------------
    # DOWNLOAD VALIDATION
    # --------------------------------------------------------

    if not downloaded:

        raise RuntimeError(
            "Gagal download BzMiner V11. "
            "Server download menolak request "
            "atau URL release tidak tersedia."
        )

    archive_size = os.path.getsize(
        ARCHIVE
    )

    print("")
    print(
        "archive size:",
        archive_size,
        "bytes",
    )

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print("EXTRACTING BZMINER")
    print("=" * 60)

    extract_dir = WORKDIR

    try:

        with tarfile.open(
            ARCHIVE,
            "r:gz",
        ) as tar:

            tar.extractall(
                path=extract_dir
            )

    except Exception as e:

        raise RuntimeError(
            f"Gagal extract BzMiner: {e}"
        )

    # --------------------------------------------------------
    # FIND BINARY
    # --------------------------------------------------------

    print("")
    print("searching BzMiner binary...")

    miner = None

    for root, dirs, files in os.walk(
        WORKDIR
    ):

        for filename in files:

            if filename == "bzminer":

                candidate = os.path.join(
                    root,
                    filename,
                )

                miner = candidate
                break

        if miner:
            break

    if not miner:

        raise RuntimeError(
            "Binary bzminer tidak ditemukan "
            "setelah extract."
        )

    os.chmod(
        miner,
        0o755,
    )

    print("")
    print("miner:")
    print(miner)

    # --------------------------------------------------------
    # VERSION CHECK
    # --------------------------------------------------------

    print("")
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
            version_result.stdout,
            flush=True,
        )

    # --------------------------------------------------------
    # GPU CHECK FROM BZMINER
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print("BZMINER GPU DETECTION")
    print("=" * 60)

    gpu_result = subprocess.run(
        [
            miner,
            "--no-watchdog",
            "--nohttpheaders",
            "--list_devices",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
        check=False,
    )

    if gpu_result.stdout:
        print(
            gpu_result.stdout,
            flush=True,
        )

    # --------------------------------------------------------
    # MINING CONFIG
    # --------------------------------------------------------

    wallet_worker = (
        f"{WALLET}.{WORKER}"
    )

    print("")
    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)

    print("GPU       : RTX 4090")
    print("Algorithm : pearlhash")
    print("Pool      :", POOL)
    print("Worker    :", WORKER)
    print("Wallet    : configured")
    print("Miner     : BzMiner")
    print("=" * 60)

    # --------------------------------------------------------
    # START MINER
    # --------------------------------------------------------

    command = [
        miner,

        "--no-watchdog",

        "--algo",
        "pearlhash",

        "--pool",
        POOL,

        "--wallet",
        wallet_worker,

        "--nohttpheaders",
    ]

    print("")
    print("=" * 60)
    print("STARTING BZMINER")
    print("=" * 60)

    print("command:")
    print(
        " ".join(command),
        flush=True,
    )

    start_time = time.time()

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # --------------------------------------------------------
    # MONITOR
    # --------------------------------------------------------

    accepted = 0
    rejected = 0
    connected = False
    hashing = False

    try:

        while True:

            line = process.stdout.readline()

            if line:

                text = line.strip()

                print(
                    "[bzminer]",
                    text,
                    flush=True,
                )

                lower = text.lower()

                # Connection detection
                if (
                    "connected" in lower
                    or "stratum" in lower
                    or "connection established"
                    in lower
                ):
                    connected = True

                # Hashrate detection
                if (
                    "hashrate" in lower
                    or "sol/s" in lower
                    or "mh/s" in lower
                    or "gh/s" in lower
                    or "kh/s" in lower
                ):
                    hashing = True

                # Accepted shares
                if (
                    "accepted" in lower
                    or "share accepted" in lower
                ):
                    accepted += 1

                # Rejected shares
                if (
                    "rejected" in lower
                    or "share rejected" in lower
                ):
                    rejected += 1

            if process.poll() is not None:
                break

            time.sleep(0.05)

    except KeyboardInterrupt:

        print("")
        print(
            "KeyboardInterrupt - stopping miner..."
        )

        process.terminate()

        try:

            process.wait(
                timeout=10
            )

        except subprocess.TimeoutExpired:

            process.kill()

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    runtime = (
        time.time() - start_time
    )

    exit_code = process.returncode

    print("")
    print("=" * 60)
    print("MINING RESULT")
    print("=" * 60)

    print(
        "connected :",
        connected,
    )

    print(
        "hashing   :",
        hashing,
    )

    print(
        "accepted  :",
        accepted,
    )

    print(
        "rejected  :",
        rejected,
    )

    print(
        "exit code :",
        exit_code,
    )

    print(
        "runtime   :",
        round(runtime, 2),
        "seconds",
    )

    print("=" * 60)

    if exit_code != 0:

        raise RuntimeError(
            f"BzMiner berhenti dengan exit code "
            f"{exit_code}"
        )

    if not connected:

        print(
            "WARNING: belum terdeteksi koneksi "
            "ke pool."
        )

    if not hashing:

        print(
            "WARNING: belum terdeteksi hashrate."
        )

    if accepted == 0:

        print(
            "WARNING: belum ada accepted share."
        )

    print("")
    print(
        "Fungsi selesai."
    )
