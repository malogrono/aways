import modal
import subprocess
import os
import time
import urllib.request
import tarfile
import shutil
import signal


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

app = modal.App("haji")


# ============================================================
# CONFIGURATION
# ============================================================

WALLET = (
    "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

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
# GLOBAL PROCESS
# ============================================================

miner_process = None


# ============================================================
# CLEAN SHUTDOWN
# ============================================================

def shutdown_handler(signum, frame):

    global miner_process

    print()
    print("=" * 60)
    print("MODAL WORKER RECEIVED STOP SIGNAL")
    print("=" * 60)

    if miner_process is not None:

        if miner_process.poll() is None:

            print("Stopping PeakMiner...")

            try:
                miner_process.terminate()

                try:
                    miner_process.wait(timeout=10)

                except subprocess.TimeoutExpired:

                    print("Miner did not stop gracefully.")
                    print("Sending kill signal...")

                    miner_process.kill()

            except Exception as e:

                print("Shutdown error:", e)

    print("Shutdown selesai.")


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

    global miner_process

    print("=" * 60)
    print("PEARL MINER - PEAKMINER")
    print("=" * 60)

    print("GPU    : A100")
    print("CPU    : 4")
    print("Memory : 8 GB")
    print("Time   : 24 hours")
    print("Pool   :", POOL)
    print("Worker :", WORKER)
    print("=" * 60)


    # ========================================================
    # SIGNAL HANDLERS
    # ========================================================

    signal.signal(
        signal.SIGTERM,
        shutdown_handler,
    )

    signal.signal(
        signal.SIGINT,
        shutdown_handler,
    )


    # ========================================================
    # DIRECTORY
    # ========================================================

    os.makedirs(
        BASE,
        exist_ok=True,
    )


    # ========================================================
    # GPU CHECK
    # ========================================================

    print()
    print("[1] GPU CHECK")
    print("-" * 60)

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


    # ========================================================
    # DOWNLOAD PEAKMINER
    # ========================================================

    print()
    print("[2] PEAKMINER")
    print("-" * 60)

    print("Version:", VERSION)

    if not os.path.exists(ARCHIVE):

        print("Downloading...")

        try:

            request = urllib.request.Request(
                URL,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=120,
            ) as response:

                with open(
                    ARCHIVE,
                    "wb",
                ) as file:

                    while True:

                        data = response.read(
                            1024 * 1024
                        )

                        if not data:
                            break

                        file.write(data)

            print("Download OK.")

        except Exception as e:

            if os.path.exists(ARCHIVE):
                os.remove(ARCHIVE)

            raise RuntimeError(
                f"Download gagal: {e}"
            )

    else:

        print("Archive sudah tersedia.")


    # ========================================================
    # EXTRACT
    # ========================================================

    print("Extracting...")

    if os.path.exists(EXTRACT):

        shutil.rmtree(EXTRACT)

    os.makedirs(
        EXTRACT,
        exist_ok=True,
    )

    with tarfile.open(
        ARCHIVE,
        "r:gz",
    ) as tar:

        tar.extractall(EXTRACT)


    # ========================================================
    # FIND BINARY
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

        raise RuntimeError(
            "Binary PeakMiner tidak ditemukan."
        )


    os.chmod(
        miner,
        0o755,
    )

    print("Binary:", miner)


    # ========================================================
    # VERSION
    # ========================================================

    version_test = subprocess.run(
        [
            miner,
            "--version",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=15,
    )

    print(
        "Miner:",
        version_test.stdout.strip(),
    )


    # ========================================================
    # GPU DETECTION
    # ========================================================

    print()
    print("[3] MINER GPU")
    print("-" * 60)

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
    # MINING COMMAND
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


    print()
    print("[4] START MINER")
    print("-" * 60)

    # Wallet sengaja tidak ditampilkan
    print(
        f"{miner} "
        f"--coin pearl "
        f"-o {POOL} "
        f"-u [WALLET]/{WORKER}"
    )

    print("-" * 60)


    # ========================================================
    # START MINER
    # ========================================================

    miner_process = subprocess.Popen(
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


    print()
    print("[5] MINER RUNNING")
    print("-" * 60)


    # ========================================================
    # READ MINER OUTPUT
    # ========================================================

    try:

        while True:

            line = miner_process.stdout.readline()

            if line:

                line = line.strip()

                if not line:
                    continue

                low = line.lower()


                # --------------------------------------------
                # CONNECTION
                # --------------------------------------------

                if any(
                    word in low
                    for word in [
                        "connected",
                        "connection established",
                        "stratum connected",
                        "login successful",
                        "authorized",
                        "subscribed",
                    ]
                ):

                    connected = True

                    print(
                        "[POOL]",
                        line,
                    )


                # --------------------------------------------
                # HASHRATE
                # --------------------------------------------

                if any(
                    word in low
                    for word in [
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

                    print(
                        "[HASH]",
                        line,
                    )


                # --------------------------------------------
                # SHARE
                # --------------------------------------------

                if any(
                    word in low
                    for word in [
                        "accepted",
                        "share accepted",
                        "accepted share",
                        "solution",
                        "shares accepted",
                    ]
                ):

                    share = True

                    print(
                        "[SHARE]",
                        line,
                    )


                # --------------------------------------------
                # ERROR
                # --------------------------------------------

                if any(
                    word in low
                    for word in [
                        "error",
                        "failed",
                        "fatal",
                        "rejected",
                    ]
                ):

                    print(
                        "[MINER]",
                        line,
                    )


            else:

                if miner_process.poll() is not None:

                    break

                time.sleep(0.1)


    except KeyboardInterrupt:

        print()
        print("Keyboard interrupt.")

        shutdown_handler(
            signal.SIGINT,
            None,
        )


    finally:

        runtime = (
            time.time() - start_time
        )

        exit_code = miner_process.poll()


    # ========================================================
    # FINAL STATUS
    # ========================================================

    print()
    print("=" * 60)
    print("FINAL STATUS")
    print("=" * 60)

    print(
        "Pool connected :",
        connected,
    )

    print(
        "Hashing        :",
        hashing,
    )

    print(
        "Share detected :",
        share,
    )

    print(
        "Exit code      :",
        exit_code,
    )

    print(
        "Runtime        :",
        round(runtime, 2),
        "seconds",
    )

    print("=" * 60)


    # ========================================================
    # STATUS MESSAGE
    # ========================================================

    if connected:

        print("POOL   : CONNECTED")

    else:

        print("POOL   : NOT DETECTED")


    if hashing:

        print("HASH   : DETECTED")

    else:

        print("HASH   : NOT DETECTED")


    if share:

        print("SHARE  : DETECTED")

    else:

        print("SHARE  : NOT YET")


    print("=" * 60)


    # ========================================================
    # RESULT
    # ========================================================

    return {

        "miner": "PeakMiner",

        "version": VERSION,

        "gpu": "A100",

        "cpu": 4,

        "memory": "8GB",

        "timeout": "24 hours",

        "coin": "Pearl",

        "algorithm": "PearlHash",

        "pool": POOL,

        "worker": WORKER,

        "connected": connected,

        "hashing": hashing,

        "share_detected": share,

        "exit_code": exit_code,

        "runtime": round(
            runtime,
            2,
        ),
    }


# ============================================================
# LOCAL ENTRYPOINT
# ============================================================

@app.local_entrypoint()
def main():

    result = run_pearl.remote()

    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    print(result)
