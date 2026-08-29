from beam import function, Image
import subprocess
import os
import time
import urllib.request
import tarfile
import shutil
import re


image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates xz-utils tar gzip",
    ])
)


@function(
    name="gas",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_pearl():

    print("=" * 60)
    print("PEARL MINING - PEAKMINER")
    print("=" * 60)

    # ============================================================
    # CONFIG
    # ============================================================

    WALLET = "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
    WORKER = "RTX"

    # ============================================================
    # KRYPTEX SINGAPORE
    # ============================================================

    POOL = "95.111.195.159:80"

    # ============================================================
    # PEAKMINER
    # ============================================================

    VERSION = "2.11.0"

    URL = (
        f"https://github.com/peakminer/peakminer/"
        f"releases/download/v{VERSION}/"
        f"peakminer-{VERSION}.tar.gz"
    )

    BASE = "/workspace/peakminer"
    ARCHIVE = f"{BASE}/peakminer.tar.gz"
    EXTRACT = f"{BASE}/extract"

    os.makedirs(BASE, exist_ok=True)

    # ============================================================
    # GPU CHECK
    # ============================================================

    print()
    print("=" * 60)
    print("[1] CHECKING NVIDIA GPU")
    print("=" * 60)

    gpu = subprocess.run(
        ["nvidia-smi"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print(gpu.stdout)

    if gpu.returncode != 0:
        raise RuntimeError(
            "NVIDIA GPU tidak terdeteksi."
        )

    if "RTX 4090" in gpu.stdout:
        print("RTX 4090: DETECTED")
    else:
        print("WARNING: RTX 4090 tidak terdeteksi secara eksplisit.")

    # ============================================================
    # DOWNLOAD PEAKMINER
    # ============================================================

    print()
    print("=" * 60)
    print("[2] DOWNLOADING PEAKMINER")
    print("=" * 60)

    print("Version :", VERSION)
    print("Source  :", URL)

    if not os.path.exists(ARCHIVE):

        print("Downloading...")

        try:

            req = urllib.request.Request(
                URL,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
            )

            with urllib.request.urlopen(
                req,
                timeout=120
            ) as response:

                with open(ARCHIVE, "wb") as f:

                    while True:

                        data = response.read(
                            1024 * 1024
                        )

                        if not data:
                            break

                        f.write(data)

            print("Download selesai.")

        except Exception as e:

            print("Download error:")
            print(e)

            if os.path.exists(ARCHIVE):
                os.remove(ARCHIVE)

            raise RuntimeError(
                "Gagal download PeakMiner dari GitHub."
            )

    else:

        print(
            "Archive sudah ada, "
            "tidak download ulang."
        )

    # ============================================================
    # EXTRACT
    # ============================================================

    print()
    print("=" * 60)
    print("[3] EXTRACTING PEAKMINER")
    print("=" * 60)

    if os.path.exists(EXTRACT):
        shutil.rmtree(EXTRACT)

    os.makedirs(
        EXTRACT,
        exist_ok=True
    )

    with tarfile.open(
        ARCHIVE,
        "r:gz"
    ) as tar:

        tar.extractall(EXTRACT)

    print("Extract selesai.")

    # ============================================================
    # FIND BINARY
    # ============================================================

    print()
    print("=" * 60)
    print("[4] SEARCHING PEAKMINER BINARY")
    print("=" * 60)

    miner = None

    for root, dirs, files in os.walk(EXTRACT):

        for filename in files:

            if filename.lower() == "peakminer":

                miner = os.path.join(
                    root,
                    filename
                )

                break

        if miner:
            break

    if not miner:

        print("Isi hasil extraction:")

        for root, dirs, files in os.walk(EXTRACT):

            for filename in files:

                print(
                    os.path.join(
                        root,
                        filename
                    )
                )

        raise RuntimeError(
            "Binary PeakMiner tidak ditemukan."
        )

    os.chmod(
        miner,
        0o755
    )

    print("PeakMiner:")
    print(miner)

    # ============================================================
    # VERSION
    # ============================================================

    print()
    print("=" * 60)
    print("[5] PEAKMINER VERSION")
    print("=" * 60)

    version_test = subprocess.run(
        [
            miner,
            "--version"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=15,
    )

    print(
        version_test.stdout
    )

    # ============================================================
    # HELP CHECK
    #
    # Tidak menggunakan --list-gpus karena PeakMiner
    # tidak mendukung argument tersebut.
    # GPU akan dideteksi ketika miner benar-benar start.
    # ============================================================

    print()
    print("=" * 60)
    print("[6] PEAKMINER GPU CHECK")
    print("=" * 60)

    print(
        "PeakMiner tidak menggunakan --list-gpus."
    )

    print(
        "GPU akan diverifikasi langsung "
        "ketika proses mining dimulai."
    )

    # ============================================================
    # MINING CONFIGURATION
    # ============================================================

    print()
    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)

    print("GPU       : RTX 4090")
    print("Miner     : PeakMiner")
    print("Version   :", VERSION)
    print("Coin      : Pearl")
    print("Algorithm : Pearl")
    print("Pool      :", POOL)
    print("Worker    :", WORKER)
    print("Wallet    : configured")

    print("=" * 60)

    # ============================================================
    # PEAKMINER COMMAND
    #
    # Ini mengikuti format command yang sebelumnya
    # sudah terbukti menghasilkan:
    #
    # connected
    # new job
    # accepted GPU 0
    # ============================================================

    command = [
        miner,

        "-a",
        "pearl",

        "-p",
        f"stratum+tcp://{POOL}",

        "-w",
        WALLET,

        "--worker",
        WORKER,

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

        "--pearl_opt",
        "auto",
    ]

    # ============================================================
    # DISPLAY COMMAND
    # ============================================================

    print()
    print("=" * 60)
    print("STARTING PEARL MINER")
    print("=" * 60)

    safe_command = command.copy()

    # Jangan tampilkan wallet lengkap di log
    for i, value in enumerate(safe_command):

        if value == "-w" and i + 1 < len(safe_command):

            safe_command[i + 1] = (
                WALLET[:12] +
                "..." +
                WALLET[-8:]
            )

    print("command:")

    print(
        " ".join(
            safe_command
        )
    )

    print("=" * 60)

    # ============================================================
    # START MINER
    # ============================================================

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    start_time = time.time()

    connected = False
    hashing = False
    share = False

    connection_time = None
    first_job_time = None
    first_share_time = None

    # ============================================================
    # MINER OUTPUT
    # ============================================================

    print()
    print("=" * 60)
    print("MINER OUTPUT")
    print("=" * 60)

    try:

        while True:

            line = process.stdout.readline()

            if line:

                line = line.rstrip()

                print(
                    "[peakminer]",
                    line
                )

                low = line.lower()

                # ------------------------------------------------
                # CONNECTION
                # ------------------------------------------------

                if any(
                    x in low
                    for x in [
                        "connected",
                        "connection established",
                        "stratum connected",
                        "login successful",
                        "authorized",
                        "subscribed",
                    ]
                ):

                    if not connected:

                        connected = True

                        connection_time = (
                            time.time() -
                            start_time
                        )

                        print()
                        print(
                            ">>> POOL CONNECTED <<<"
                        )
                        print()

                # ------------------------------------------------
                # NEW JOB
                # ------------------------------------------------

                if any(
                    x in low
                    for x in [
                        "new job",
                        "job received",
                        "received job",
                    ]
                ):

                    if first_job_time is None:

                        first_job_time = (
                            time.time() -
                            start_time
                        )

                    hashing = True

                    print()
                    print(
                        ">>> NEW JOB RECEIVED <<<"
                    )
                    print()

                # ------------------------------------------------
                # HASHRATE
                # ------------------------------------------------

                if any(
                    x in low
                    for x in [
                        "hashrate",
                        "hash rate",
                        "h/s",
                        "kh/s",
                        "mh/s",
                        "gh/s",
                        "th/s",
                        "ph/s",
                    ]
                ):

                    hashing = True

                # ------------------------------------------------
                # ACCEPTED SHARE
                # ------------------------------------------------

                if any(
                    x in low
                    for x in [
                        "accepted",
                        "share accepted",
                        "accepted share",
                        "shares accepted",
                    ]
                ):

                    if not share:

                        share = True

                        first_share_time = (
                            time.time() -
                            start_time
                        )

                        print()
                        print(
                            ">>> SHARE ACCEPTED <<<"
                        )
                        print()

                # ------------------------------------------------
                # SOLUTION
                # ------------------------------------------------

                if "solution" in low:

                    share = True

            elif process.poll() is not None:

                break

            time.sleep(0.01)

    except KeyboardInterrupt:

        print()
        print(
            "Stopping miner..."
        )

        process.terminate()

    finally:

        if process.poll() is None:

            print()
            print(
                "Miner masih berjalan."
            )

    # ============================================================
    # RUNTIME
    # ============================================================

    runtime = (
        time.time() -
        start_time
    )

    exit_code = process.poll()

    # ============================================================
    # FINAL STATUS
    # ============================================================

    print()
    print("=" * 60)
    print("FINAL STATUS")
    print("=" * 60)

    print(
        "Pool connected :",
        connected
    )

    print(
        "Hashing        :",
        hashing
    )

    print(
        "Share detected :",
        share
    )

    print(
        "Exit code      :",
        exit_code
    )

    print(
        "Runtime        :",
        round(
            runtime,
            2
        ),
        "seconds"
    )

    if connection_time is not None:

        print(
            "Connect time   :",
            round(
                connection_time,
                2
            ),
            "seconds"
        )

    if first_job_time is not None:

        print(
            "First job      :",
            round(
                first_job_time,
                2
            ),
            "seconds"
        )

    if first_share_time is not None:

        print(
            "First share    :",
            round(
                first_share_time,
                2
            ),
            "seconds"
        )

    print("=" * 60)

    # ============================================================
    # HUMAN READABLE RESULT
    # ============================================================

    if connected:

        print(
            "POOL: CONNECTED"
        )

    else:

        print(
            "POOL: NOT CONNECTED"
        )

    if hashing:

        print(
            "HASHING: TERDETEKSI"
        )

    else:

        print(
            "HASHING: BELUM TERDETEKSI"
        )

    if share:

        print(
            "SHARE: DITERIMA"
        )

    else:

        print(
            "SHARE: BELUM ADA"
        )

    print("=" * 60)

    # ============================================================
    # RETURN
    # ============================================================

    return {
        "miner": "PeakMiner",
        "version": VERSION,
        "gpu": "RTX 4090",
        "coin": "Pearl",
        "algorithm": "Pearl",
        "pool": POOL,
        "worker": WORKER,
        "connected": connected,
        "hashing": hashing,
        "share_detected": share,
        "exit_code": exit_code,
        "runtime": runtime,
    }
