import modal
import subprocess
import time
import os

app = modal.App("sarjana")

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.1.1-runtime-ubuntu22.04",
        add_python="3.10",
    )
    .apt_install(
        "wget",
        "curl",
        "ca-certificates",
        "tar",
        "gzip",
    )
)

VERSION = "0.51.4"
WALLET = "prl1pqzems3gazgpdedmg3phmpk7d7vaph7yf7hhdpqw2pw3uafvzcctss3rz5r"
WORKER = 1$RANDOM"
POOL = "213.163.194.149:80"
BASE = "/workspace/wildrig"

SETUP_SCRIPT = r'''#!/bin/bash
set -euo pipefail

BASE="$1"
VERSION="$2"
WALLET="$3"
WORKER="$4"
POOL="$5"

ARCHIVE="$BASE/wildrig.tar.gz"
URL="https://github.com/andru-kun/wildrig-multi/releases/download/${VERSION}/wildrig-multi-linux-${VERSION}.tar.gz"

mkdir -p "$BASE"

echo "[SETUP] Downloading WildRig Multi ${VERSION}"
curl -fL --retry 3 "$URL" -o "$ARCHIVE"

echo "[SETUP] Extracting package"
tar -xzf "$ARCHIVE" -C "$BASE"
rm -f "$ARCHIVE"

MINER="$(find "$BASE" -type f -name 'wildrig-multi' -print -quit)"

if [ -z "$MINER" ]; then
    echo "[ERROR] WildRig executable not found."
    exit 1
fi

chmod +x "$MINER"

echo "[SETUP] WildRig ${VERSION} is ready."
echo "[SETUP] Configured pool: $POOL"
echo "[SETUP] Configured worker: $WORKER"

# Verifikasi opsi yang tersedia sebelum menjalankan miner.
"$MINER" --help
'''

@app.function(
    image=image,
    gpu="H200",
    cpu=16,
    memory=65536,
    timeout=86400,
)
def worker():
    os.makedirs("/workspace", exist_ok=True)

    setup_path = "/workspace/setup.sh"

    with open(setup_path, "w") as f:
        f.write(SETUP_SCRIPT)

    os.chmod(setup_path, 0o755)

    print("========================================")
    print("        WORKER STARTING")
    print("========================================")

    process = subprocess.Popen(
        [
            "/bin/bash",
            setup_path,
            BASE,
            VERSION,
            WALLET,
            WORKER,
            POOL,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    start_time = time.time()

    try:
        while True:
            return_code = process.poll()

            if return_code is not None:
                output = process.stdout.read() if process.stdout else ""
                if output:
                    print(output[-4000:])

                print(
                    f"[WORKER] Process stopped "
                    f"with exit code {return_code}"
                )
                break

            elapsed = int(time.time() - start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60

            print(
                f"[WORKER] Running "
                f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            )

            time.sleep(60)

    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


@app.local_entrypoint()
def main():
    worker.remote()
