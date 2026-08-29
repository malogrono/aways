from beam import function, Image
import subprocess
import os
import time
import tarfile
import urllib.request

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates xz-utils pciutils",
    ])
)


@function(
    name="pearl-mining-v13",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=27 * 60 * 60,
)
def run_pearl():

    print("=" * 60)
    print("PEARL MINING - BZMINER V13")
    print("=" * 60)

    # ============================================================
    # CONFIG
    # ============================================================

    WALLET = "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
    WORKER = "beam-4090"
    POOL = "stratum+tcp://prl.kryptex.network:7048"

    VERSION = "25.0.0b9"

    BASE = "/workspace"
    MINER_DIR = f"{BASE}/bzminer_v{VERSION}_linux"
    ARCHIVE = f"{BASE}/bzminer.tar.gz"
    MINER = f"{MINER_DIR}/bzminer"

    URL = (
        f"https://www.bzminer.com/downloads/"
        f"bzminer_v{VERSION}_linux.tar.gz"
    )

    # ============================================================
    # GPU CHECK
    # ============================================================

    print("checking gpu...")
    print("-" * 60)

    subprocess.run(
        ["nvidia-smi"],
        check=False
    )

    print("-" * 60)

    # ============================================================
    # DOWNLOAD
    # ============================================================

    print("downloading bzminer...")
    print("version:")
    print(VERSION)
    print("-" * 60)

    if os.path.exists(MINER):
        print("BzMiner sudah tersedia:")
        print(MINER)
    else:

        downloaded = False

        # --------------------------------------------------------
        # METHOD 1 - wget
        # --------------------------------------------------------

        print("download method 1 - wget")

        cmd = [
            "wget",
            "-q",
            "--show-progress",
            "--user-agent=Mozilla/5.0",
            "-O",
            ARCHIVE,
            URL,
        ]

        result = subprocess.run(
            cmd,
            check=False
        )

        if result.returncode == 0 and os.path.exists(ARCHIVE):
            size = os.path.getsize(ARCHIVE)

            if size > 1000000:
                downloaded = True
                print("download berhasil")
                print("size:", size)

        # --------------------------------------------------------
        # METHOD 2 - python urllib
        # --------------------------------------------------------

        if not downloaded:

            print("-" * 60)
            print("download method 2 - python")

            try:
                req = urllib.request.Request(
                    URL,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 "
                            "(X11; Linux x86_64) "
                            "AppleWebKit/537.36 "
                            "Chrome/120 Safari/537.36"
                        ),
                        "Accept": "*/*",
                    },
                )

                with urllib.request.urlopen(
                    req,
                    timeout=120
                ) as response:

                    with open(ARCHIVE, "wb") as f:
                        while True:
                            chunk = response.read(1024 * 1024)

                            if not chunk:
                                break

                            f.write(chunk)

                if os.path.exists(ARCHIVE):
                    size = os.path.getsize(ARCHIVE)

                    if size > 1000000:
                        downloaded = True
                        print("download python berhasil")
                        print("size:", size)

            except Exception as e:
                print("python download error:")
                print(str(e))

        if not downloaded:
            raise RuntimeError(
                "Gagal download BzMiner. "
                "Server bzminer.com masih menolak request."
            )

    # ============================================================
    # EXTRACT
    # ============================================================

    print("=" * 60)
    print("EXTRACTING BZMINER")
    print("=" * 60)

    if not os.path.exists(MINER):

        if os.path.exists(MINER_DIR):
            subprocess.run(
                ["rm", "-rf", MINER_DIR],
                check=False
            )

        result = subprocess.run(
            [
                "tar",
                "-xzf",
                ARCHIVE,
                "-C",
                BASE,
            ],
            check=False
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Gagal extract BzMiner"
            )

    # ============================================================
    # FIND BINARY
    # ============================================================

    print("mencari binary BzMiner...")

    if not os.path.exists(MINER):

        find_result = subprocess.run(
            [
                "find",
                BASE,
                "-type",
                "f",
                "-name",
                "bzminer",
            ],
            capture_output=True,
            text=True,
            check=False
        )

        paths = [
            x.strip()
            for x in find_result.stdout.splitlines()
            if x.strip()
        ]

        if not paths:
            raise RuntimeError(
                "Binary bzminer tidak ditemukan."
            )

        MINER = paths[0]

    os.chmod(MINER, 0o755)

    print("miner:")
    print(MINER)

    # ============================================================
    # VERSION
    # ============================================================

    print("=" * 60)
    print("BZMINER VERSION")
    print("=" * 60)

    version_result = subprocess.run(
        [MINER, "--version"],
        capture_output=True,
        text=True,
        check=False
    )

    print("stdout:")
    print(version_result.stdout)

    print("stderr:")
    print(version_result.stderr)

    # ============================================================
    # GPU DETECTION BY BZMINER
    # ============================================================

    print("=" * 60)
    print("BZMINER GPU DETECTION")
    print("=" * 60)

    gpu_result = subprocess.run(
        [
            MINER,
            "--devices",
        ],
        capture_output=True,
        text=True,
        check=False
    )

    print("stdout:")
    print(gpu_result.stdout)

    print("stderr:")
    print(gpu_result.stderr)

    # ============================================================
    # PEARL HELP CHECK
    # ============================================================

    print("=" * 60)
    print("CHECKING PEARL SUPPORT")
    print("=" * 60)

    help_result = subprocess.run(
        [
            MINER,
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False
    )

    help_text = (
        help_result.stdout +
        "\n" +
        help_result.stderr
    )

    pearl_lines = []

    for line in help_text.splitlines():

        low = line.lower()

        if (
            "pearl" in low
            or "prl" in low
        ):
            pearl_lines.append(line)

    if pearl_lines:

        print("PEARL-RELATED HELP:")
        print("-" * 60)

        for line in pearl_lines:
            print(line)

    else:

        print(
            "Tidak menemukan pearl pada help."
        )

    # ============================================================
    # MINING CONFIGURATION
    # ============================================================

    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)

    print("GPU       : RTX 4090")
    print("Miner     : BzMiner")
    print("Version   :", VERSION)
    print("Algorithm : pearl")
    print("Pool      :", POOL)
    print("Worker    :", WORKER)
    print("Wallet    : configured")

    print("=" * 60)

    # ============================================================
    # MINIMAL COMMAND
    # ============================================================

    command = [
        MINER,

        "-a",
        "pearl",

        "-p",
        POOL,

        "-w",
        WALLET,

        "--worker",
        WORKER,

        "--nvidia",
        "1",

        "-v",
        "4",

        "--immediate_log",

        "--log_date",
        "1",
    ]

    print("STARTING PEARL MINER")
    print("=" * 60)

    print("command:")

    # wallet disamarkan pada log
    display_command = command.copy()

    for i, value in enumerate(display_command):

        if value == WALLET:
            display_command[i] = "<WALLET>"

    print(" ".join(display_command))

    print("=" * 60)
    print("MINER OUTPUT")
    print("=" * 60)

    # ============================================================
    # RUN MINER
    # ============================================================

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    pool_connected = False
    hashing = False
    share_detected = False

    start_time = time.time()

    try:

        for line in iter(
            process.stdout.readline,
            ""
        ):

            if not line:
                break

            line = line.rstrip()

            print("[bzminer]")
            print(line)

            low = line.lower()

            # ----------------------------------------------------
            # CONNECTION DETECTION
            # ----------------------------------------------------

            if (
                "connected" in low
                or "connection established" in low
                or "stratum connected" in low
            ):
                pool_connected = True

            # ----------------------------------------------------
            # HASHING DETECTION
            # ----------------------------------------------------

            if (
                "hashrate" in low
                or "hash rate" in low
                or "sol/s" in low
                or "h/s" in low
                or "mh/s" in low
                or "gh/s" in low
            ):
                hashing = True

            # ----------------------------------------------------
            # SHARE DETECTION
            # ----------------------------------------------------

            if (
                "accepted" in low
                or "share accepted" in low
                or "solution accepted" in low
            ):
                share_detected = True

            # ----------------------------------------------------
            # STOP IF MINER DIES
            # ----------------------------------------------------

            if process.poll() is not None:
                break

    except KeyboardInterrupt:

        print("Keyboard interrupt.")

    finally:

        if process.poll() is None:

            print(
                "Miner masih berjalan."
            )

            # Jangan langsung kill.
            # Biarkan Beam menjaga process tetap hidup.

    exit_code = process.poll()

    runtime = time.time() - start_time

    # ============================================================
    # FINAL STATUS
    # ============================================================

    print("=" * 60)
    print("FINAL STATUS")
    print("=" * 60)

    print("Pool connected :")
    print(pool_connected)

    print("Hashing        :")
    print(hashing)

    print("Share detected :")
    print(share_detected)

    print("Exit code      :")
    print(exit_code)

    print("Runtime        :")
    print(round(runtime, 2))
    print("seconds")

    print("=" * 60)

    if pool_connected:
        print("POOL TERDETEKSI TERHUBUNG.")
    else:
        print(
            "BELUM TERBUKTI POOL TERHUBUNG."
        )

    if hashing:
        print("HASHING TERDETEKSI.")
    else:
        print(
            "BELUM TERBUKTI HASHING."
        )

    if share_detected:
        print(
            "SHARE DITERIMA POOL."
        )
    else:
        print(
            "BELUM ADA SHARE ACCEPTED."
        )

    print("=" * 60)
    print("PEARL MINING V13 SELESAI")
    print("=" * 60)


if __name__ == "__main__":
    run_pearl()
