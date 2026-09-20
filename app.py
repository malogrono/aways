import modal
import subprocess
import time
import os

app = modal.App("haji")

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.1.1-runtime-ubuntu22.04",
        add_python="3.10",
    )
    .apt_install(
        "wget",
        "curl",
        "ca-certificates",
        "xz-utils",
        "tar",
        "gzip",
    )
)

SETUP_SCRIPT = r'''#!/bin/bash

set -e

BASE="/workspace/peakminer"
VERSION="2.16.4"

WALLET="prl1pk06kg4nye9f2f44gt6hvwchrg0fnkgkhyv058zmml7z57y9tn2cqky62kj"
WORKER="VERTEX"
POOL="prl-sg.kryptex.network:7048"

ARCHIVE="$BASE/peakminer.tar.gz"
URL="https://github.com/peakminer/peakminer/releases/download/v${VERSION}/peakminer-${VERSION}.tar.gz"

mkdir -p "$BASE"

echo "[SETUP] Preparing worker..."

if [ ! -f "$BASE/peakminer" ]; then

    echo "[SETUP] Downloading package..."

    curl -L --fail "$URL" -o "$ARCHIVE"

    echo "[SETUP] Extracting package..."

    tar -xzf "$ARCHIVE" -C "$BASE" --strip-components=1

    rm -f "$ARCHIVE"

fi

if [ ! -x "$BASE/peakminer" ]; then
    chmod +x "$BASE/peakminer"
fi

echo "[SETUP] Starting worker..."

exec "$BASE/peakminer" \
    --coin pearl \
    -o "$POOL" \
    -u "${WALLET}/${WORKER}"
'''

@app.function(
    image=image,
    gpu="A100",
    cpu=4,
    memory=8192,
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
        [setup_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(f"[WORKER] Process started: PID {process.pid}")

    start_time = time.time()

    try:
        while True:

            return_code = process.poll()

            if return_code is not None:
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


@app.local_entrypoint()
def main():
    worker.remote()
