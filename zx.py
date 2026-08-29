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
        "apt-get install -y wget ca-certificates tar",
        "rm -rf /var/lib/apt/lists/*",
    ])
)


# ============================================================
# BZMINER CONFIGURATION
# ============================================================

BZMINER_VERSION = "25.0.0b8"

BZMINER_URL = (
    "https://bzminer.com/downloads/"
    f"bzminer_v{BZMINER_VERSION}_linux.tar.gz"
)

POOL = "prl.kryptex.network:7048"

WALLET = (
    "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

WORKER_NAME = "beam-4090"

ALGORITHM = "pearl"

PASSWORD = "x"


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
    print("PEARL MINING - BZMINER V9")
    print("=" * 60)

    # --------------------------------------------------------
    # PATH
    # --------------------------------------------------------

    workdir = "/workspace/bzminer"

    archive = (
        f"{workdir}/"
        f"bzminer_v{BZMINER_VERSION}_linux.tar.gz"
    )

    extract_dir = (
        f"{workdir}/"
        f"bzminer_v{BZMINER_VERSION}_linux"
    )

    miner = f"{extract_dir}/bzminer"

    # --------------------------------------------------------
    # CREATE DIRECTORY
    # --------------------------------------------------------

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
    print("url:", BZMINER_URL)
    print("-" * 60)

    downloaded = False

    for attempt in range(1, 6):

        print(
            f"download attempt {attempt}/5...",
            flush=True,
        )

        # Hapus file lama
        try:
            os.remove(archive)
        except FileNotFoundError:
            pass

        result = subprocess.run(
            [
                "wget",
                "-q",
                "--show-progress",
                "--server-response",
                "--tries=1",
                "--timeout=60",
                "--user-agent=Mozilla/5.0",
                "-O",
                archive,
                BZMINER_URL,
            ],
            check=False,
        )

        if result.returncode == 0:

            # Pastikan file benar-benar ada
            if os.path.isfile(archive):

                size = os.path.getsize(archive)

                print(
                    f"download selesai: {size:,} bytes",
                    flush=True,
                )

                # Archive BzMiner harus berukuran cukup besar.
                # Ini mencegah HTML/error 429 ikut dianggap
                # sebagai archive yang valid.
                if size > 1_000_000:

                    downloaded = True
                    break

                print(
                    "file terlalu kecil, kemungkinan "
                    "bukan archive BzMiner",
                    flush=True,
                )

        else:

            print(
                f"download gagal, exit code: "
                f"{result.returncode}",
                flush=True,
            )

        if attempt < 5:

            wait_time = attempt * 10

            print(
                f"menunggu {wait_time} detik sebelum retry...",
                flush=True,
            )

            time.sleep(wait_time)

    if not downloaded:

        raise RuntimeError(
            "gagal download BzMiner setelah 5 percobaan. "
            "Kemungkinan server bzminer.com sedang "
            "memberikan HTTP 429."
        )

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    print("=" * 60)
    print("extracting bzminer...")
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
    # FIND MINER
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

    print("miner:")
    print(miner)

    # --------------------------------------------------------
    # MAKE EXECUTABLE
    # --------------------------------------------------------

    subprocess.run(
        ["chmod", "+x", miner],
        check=True,
    )

    # --------------------------------------------------------
    # BZMINER VERSION
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
    # CONFIGURATION
    # --------------------------------------------------------

    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)

    print("GPU       : RTX 4090")
    print("Algorithm :", ALGORITHM)
    print("Pool      :")
    print(POOL)
    print("Worker    :")
    print(WORKER_NAME)
    print("Wallet    : configured")
    print("Miner     : BzMiner")
    print("Version   :", BZMINER_VERSION)

    print("=" * 60)

    # --------------------------------------------------------
    # BZMINER COMMAND
    # --------------------------------------------------------

    pool_url = f"stratum+tcp://{POOL}"

    command = [
        miner,

        # Pearl
        "--a1",
        ALGORITHM,

        # Pool
        "--p1",
        pool_url,

        # Wallet
        "--w1",
        WALLET,

        # Worker
        "--r1",
        WORKER_NAME,

        # Password
        "--pool_password1",
        PASSWORD,

        # Pearl optimization
        "--pearl_opt",
        "auto",
    ]

    print("starting miner...")
    print("=" * 60)

    print("command:")

    print(
        " ".join(command),
        flush=True,
    )

    print("=" * 60)

    # --------------------------------------------------------
    # START BZMINER
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
    # MONITOR
    # --------------------------------------------------------

    connected = False
    hashing = False
    share_submitted = False
    share_accepted = False

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
                # CONNECTION DETECTION
                # --------------------------------------------

                if (
                    "connected" in lower
                    or "connection established" in lower
                    or "stratum connected" in lower
                    or "subscribed" in lower
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
                # HASHING DETECTION
                # --------------------------------------------

                if (
                    "hashrate" in lower
                    or "hash rate" in lower
                    or "h/s" in lower
                    or "mh/s" in lower
                    or "gh/s" in lower
                ):

                    if not hashing:

                        hashing = True

                        print(
                            "=" * 60,
                            flush=True,
                        )

                        print(
                            "STATUS: HASHING DETECTED",
                            flush=True,
                        )

                        print(
                            "=" * 60,
                            flush=True,
                        )

                # --------------------------------------------
                # SHARE SUBMITTED
                # --------------------------------------------

                if (
                    "share submitted" in lower
                    or "submitted share" in lower
                    or "share:" in lower
                    or "submit" in lower
                ):

                    if not share_submitted:

                        share_submitted = True

                        print(
                            "STATUS: SHARE SUBMISSION DETECTED",
                            flush=True,
                        )

                # --------------------------------------------
                # SHARE ACCEPTED
                # --------------------------------------------

                if (
                    "share accepted" in lower
                    or "accepted" in lower
                    or "accepted share" in lower
                ):

                    if not share_accepted:

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
    # RESULT
    # --------------------------------------------------------

    runtime = time.time() - start_time

    exit_code = process.returncode

    print("=" * 60)
    print("MINER STOPPED")
    print("=" * 60)

    print("exit code:")
    print(exit_code)

    print("runtime:")
    print(f"{runtime:.2f}")
    print("seconds")

    print("=" * 60)

    print("FINAL STATUS")
    print("=" * 60)

    print(
        "Pool connected :",
        "YES" if connected else "NO",
    )

    print(
        "Hashing        :",
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

    print("=" * 60)

    # Jangan menganggap mining berhasil hanya karena
    # process exit code = 0.

    if not connected:

        print(
            "WARNING: belum terdeteksi koneksi pool.",
            flush=True,
        )

    if not hashing:

        print(
            "WARNING: belum terdeteksi hashrate.",
            flush=True,
        )

    if not share_accepted:

        print(
            "WARNING: belum terdeteksi accepted share.",
            flush=True,
        )

    print("=" * 60)
