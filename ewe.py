import modal
import subprocess
import os
import time
import urllib.request
import tarfile
import shutil
import signal

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.1.1-runtime-ubuntu22.04",
        add_python="3.10",
    )
    .apt_install("wget", "ca-certificates", "xz-utils", "tar", "gzip")
)

app = modal.App("haji")

# Isi wallet Anda sendiri di sini.
WALLET = "GANTI_DENGAN_WALLET_ANDA"
WORKER = "A1"
POOL = "164.92.235.224:443"

VERSION = "2.15.0"
URL = (
    f"https://github.com/peakminer/peakminer/releases/download/"
    f"v{VERSION}/peakminer-{VERSION}.tar.gz"
)

BASE = "/workspace/peakminer"
ARCHIVE = f"{BASE}/peakminer.tar.gz"
EXTRACT = f"{BASE}/extract"

miner_process = None


def shutdown_handler(signum, frame):
    global miner_process

    print()
    print("=" * 60)
    print("MODAL WORKER RECEIVED STOP SIGNAL")
    print("=" * 60)

    if miner_process is not None and miner_process.poll() is None:
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


@app.function(
    image=image,
    gpu="H100",
    cpu=4,
    memory=8192,
    timeout=86400,
)
def run_pearl():
    global miner_process

    print("=" * 60)
    print("PEARL MINER - PEAKMINER")
    print("=" * 60)
    print("GPU    : H100")
    print("CPU    : 4")
    print("Memory : 8 GB")
    print("Time   : 24 hours")
    print("Pool   :", POOL)
    print("Worker :", WORKER)
    print("=" * 60)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    os.makedirs(BASE, exist_ok=True)

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
        raise RuntimeError("NVIDIA GPU tidak terdeteksi.")

    print()
    print("[2] PEAKMINER")
    print("-" * 60)
    print("Version:", VERSION)

    if not os.path.exists(ARCHIVE):
        print("Downloading...")
        try:
            request = urllib.request.Request(
                URL,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                with open(ARCHIVE, "wb") as file:
                    while True:
                        data = response.read(1024 * 1024)
                        if not data:
                            break
                        file.write(data)
            print("Download OK.")
        except Exception as e:
            if os.path.exists(ARCHIVE):
                os.remove(ARCHIVE)
            raise RuntimeError(f"Download gagal: {e}")
    else:
        print("Archive sudah tersedia.")

    print("Extracting...")

    if os.path.exists(EXTRACT):
        shutil.rmtree(EXTRACT)
    os.makedirs(EXTRACT, exist_ok=True)

    with tarfile.open(ARCHIVE, "r:gz") as tar:
        tar.extractall(EXTRACT)

    miner = None
    for root, dirs, files in os.walk(EXTRACT):
        for filename in files:
            if filename.lower() == "peakminer":
                miner = os.path.join(root, filename)
                break
        if miner:
            break

    if not miner:
        raise RuntimeError("Binary PeakMiner tidak ditemukan.")

    os.chmod(miner, 0o755)
    print("Binary:", miner)

    version_test = subprocess.run(
        [miner, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=15,
    )
    print("Miner:", version_test.stdout.strip())

    print()
    print("[3] ACTUAL GPU")
    print("-" * 60)

    actual_gpu = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(actual_gpu.stdout.strip())

    # PeakMiner 2.15.0 tidak menerima --list-gpus.
    # Karena itu GPU cukup diverifikasi menggunakan nvidia-smi.
    command = [
        miner,
        "--coin", "pearl",
        "-o", POOL,
        "-u", f"{WALLET}/{WORKER}",
    ]

    print()
    print("[4] START MINER")
    print("-" * 60)
    print(f"{miner} --coin pearl -o {POOL} -u [WALLET]/{WORKER}")
    print("-" * 60)

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

    try:
        while True:
            line = miner_process.stdout.readline()

            if line:
                line = line.strip()
                if not line:
                    continue

                low = line.lower()

                if any(word in low for word in [
                    "connected",
                    "connection established",
                    "stratum connected",
                    "login successful",
                    "authorized",
                    "subscribed",
                ]):
                    connected = True
                    print("[POOL]", line)

                if any(word in low for word in [
                    "hashrate",
                    "hash rate",
                    "h/s",
                    "kh/s",
                    "mh/s",
                    "gh/s",
                    "th/s",
                ]):
                    hashing = True
                    print("[HASH]", line)

                if any(word in low for word in [
                    "accepted",
                    "share accepted",
                    "accepted share",
                    "solution",
                    "shares accepted",
                ]):
                    share = True
                    print("[SHARE]", line)

                if any(word in low for word in [
                    "error",
                    "failed",
                    "fatal",
                    "rejected",
                ]):
                    print("[MINER]", line)

            else:
                if miner_process.poll() is not None:
                    break
                time.sleep(0.1)

    except KeyboardInterrupt:
        print()
        print("Keyboard interrupt.")
        shutdown_handler(signal.SIGINT, None)

    finally:
        runtime = time.time() - start_time
        exit_code = miner_process.poll()

    print()
    print("=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    print("Pool connected :", connected)
    print("Hashing        :", hashing)
    print("Share detected :", share)
    print("Exit code      :", exit_code)
    print("Runtime        :", round(runtime, 2), "seconds")
    print("=" * 60)

    print("POOL   :", "CONNECTED" if connected else "NOT DETECTED")
    print("HASH   :", "DETECTED" if hashing else "NOT DETECTED")
    print("SHARE  :", "DETECTED" if share else "NOT YET")
    print("=" * 60)

    return {
        "miner": "PeakMiner",
        "version": VERSION,
        "gpu": "H100",
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
        "runtime": round(runtime, 2),
    }


@app.local_entrypoint()
def main():
    result = run_pearl.remote()
    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    print(result)
