import modal
import subprocess
import os
import time
import urllib.request
import tarfile
import shutil


# ============================================================
# MODAL IMAGE
# ============================================================

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.1.1-runtime-ubuntu22.04",
        add_python="3.10",
    )
    .apt_install(
        "wget",
        "ca-certificates",
        "xz-utils",
        "tar",
        "gzip",
    )
)


# ============================================================
# MODAL APP
# ============================================================

app = modal.App("pearl-miner")


# ============================================================
# KONFIGURASI
# ============================================================

# Masukkan wallet Pearl kamu di sini jika repository-nya PRIVATE.
WALLET = "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"

WORKER = "A1"

POOL = "prl-sg.kryptex.network:7048"

VERSION = "2.11.0"

URL = (
    f"https://github.com/peakminer/peakminer/"
    f"releases/download/v{VERSION}/"
    f"peakminer-{VERSION}.tar.gz"
)

BASE = "/workspace/peakminer"
ARCHIVE = f"{BASE}/peakminer.tar.gz"
EXTRACT = f"{BASE}/extract"


# ============================================================
# MODAL FUNCTION
# ============================================================

@app.function(
    image=image,
    gpu="A100",
    cpu=4,
    memory=8192,
    timeout=86400,
)
def run_pearl():

    print("=" * 60)
    print("PEARL MINER - PEAKMINER")
    print("=" * 60)

    os.makedirs(BASE, exist_ok=True)

    # ========================================================
    # GPU CHECK
    # ========================================================

    print("\n[1] CHECK GPU")
    print("-" * 60)

    gpu = subprocess.run(
        ["nvidia-smi"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print(gpu.stdout)

    if gpu.returncode != 0:
        raise RuntimeError("NVIDIA GPU tidak terdeteksi.")

    # ========================================================
    # DOWNLOAD
    # ========================================================

    print("\n" + "=" * 60)
    print("DOWNLOADING PEAKMINER")
    print("=" * 60)

    print("Version :", VERSION)
    print("Source  :", URL)

    if not os.path.exists(ARCHIVE):

        try:

            req = urllib.request.Request(
                URL,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
            )

            with urllib.request.urlopen(
                req,
                timeout=120,
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

            if os.path.exists(ARCHIVE):
                os.remove(ARCHIVE)

            raise RuntimeError(
                f"Gagal download PeakMiner: {e}"
            )

    else:

        print("Archive sudah ada.")

    # ========================================================
    # EXTRACT
    # ========================================================

    print("\n" + "=" * 60)
    print("EXTRACT")
    print("=" * 60)

    if os.path.exists(EXTRACT):
        shutil.rmtree(EXTRACT)

    os.makedirs(EXTRACT, exist_ok=True)

    with tarfile.open(
        ARCHIVE,
        "r:gz",
    ) as tar:

        tar.extractall(EXTRACT)

    # ========================================================
    # FIND MINER
    # ========================================================

    miner = None

    for root, dirs, files in os.walk(EXTRACT):

        for filename in files:

            if filename.lower() == "peakminer":

                miner = os.path.join(
                    root,
                    filename,
                )

                break

        if miner:
            break

    if not miner:

        print("Isi extraction:")

        for root, dirs, files in os.walk(EXTRACT):

            for filename in files:

                print(
                    os.path.join(
                        root,
                        filename,
                    )
                )

        raise RuntimeError(
            "Binary PeakMiner tidak ditemukan."
        )

    os.chmod(miner, 0o755)

    print("Miner :", miner)

    # ========================================================
    # VERSION
    # ========================================================

    print("\n" + "=" * 60)
    print("PEAKMINER VERSION")
    print("=" * 60)

    version = subprocess.run(
        [miner, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=15,
    )

    print(version.stdout)

    # ========================================================
    # GPU DETECTION
    # ========================================================

    print("\n" + "=" * 60)
    print("GPU DETECTION")
    print("=" * 60)

    gpu_test = subprocess.run(
        [
            miner,
            "--coin",
            "pearl",
            "--list-gpus",
            "--nvidia",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )

    print(gpu_test.stdout)

    # ========================================================
    # CONFIGURATION
    # ========================================================

    print("\n" + "=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)

    print("GPU       : A100")
    print("CPU       : 4")
    print("Memory    : 8 GB")
    print("Miner     : PeakMiner")
    print("Version   :", VERSION)
    print("Coin      : Pearl")
    print("Algorithm : PearlHash")
    print("Pool      :", POOL)
    print("Worker    :", WORKER)
    print("Wallet    : configured")

    print("=" * 60)

    # ========================================================
    # COMMAND
    # ========================================================

    command = [
        miner,
        "--coin",
        "pearl",
        "-o",
        POOL,
        "-u",
        f"{WALLET}/{WORKER}",
    ]

    print("\nSTARTING MINER")
    print("=" * 60)

    # Jangan print wallet lengkap ke log
    print(
        f"{miner} "
        f"--coin pearl "
        f"-o {POOL} "
        f"-u [WALLET]/{WORKER}"
    )

    print("=" * 60)

    # ========================================================
    # START
    # ========================================================

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    connected = False
    hashing = False
    share = False

    print("\nMINER OUTPUT")
    print("=" * 60)

    try:

        while True:

            line = process.stdout.readline()

            if line:

                line = line.rstrip()

                print(
                    "[peakminer]",
                    line,
                )

                low = line.lower()

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

                    connected = True

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
                    ]
                ):

                    hashing = True

                if any(
                    x in low
                    for x in [
                        "accepted",
                        "share accepted",
                        "accepted share",
                        "solution",
                        "shares accepted",
                    ]
                ):

                    share = True

            elif process.poll() is not None:

                break

            time.sleep(0.01)

    except KeyboardInterrupt:

        print("Stopping miner...")

        process.terminate()

    # ========================================================
    # RESULT
    # ========================================================

    exit_code = process.poll()

    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)

    print("Pool connected :", connected)
    print("Hashing        :", hashing)
    print("Share detected :", share)
    print("Exit code      :", exit_code)

    print("=" * 60)

    return {
        "miner": "PeakMiner",
        "version": VERSION,
        "gpu": "A100",
        "cpu": 4,
        "memory": "8GB",
        "coin": "Pearl",
        "algorithm": "PearlHash",
        "pool": POOL,
        "worker": WORKER,
        "connected": connected,
        "hashing": hashing,
        "share_detected": share,
        "exit_code": exit_code,
    }


# ============================================================
# LOCAL ENTRYPOINT
# ============================================================

@app.local_entrypoint()
def main():

    result = run_pearl.remote()

    print("\nRESULT:")
    print(result)
