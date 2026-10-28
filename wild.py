
import modal
import subprocess
import time
import os
import signal

app = modal.App("runner")

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.1.1-runtime-ubuntu22.04",
        add_python="3.10",
    )
    .apt_install(
        "curl",
        "ca-certificates",
        "tar",
        "gzip",
    )
)

SETUP_SCRIPT = r'''#!/bin/bash
set -euo pipefail

BASE="/workspace/wildrig"
VERSION="0.51.8"

WALLET="prl1pv8k2dxcv4ct4p55a6znh32ltrprf5ezh4lyejcudpzzsl73zy4aqp75g0c"
WORKER="1$RANDOM"
POOL="stratum.srw.biz.id:9000"

mkdir -p "$BASE"
cd "$BASE"

if [ ! -x "$BASE/wildrig-multi" ]; then
    echo "[SETUP] Downloading WildRig Multi ${VERSION}..."

    RELEASE_API="https://api.github.com/repos/andru-kun/wildrig-multi/releases/tags/${VERSION}"

    curl -fsSL "$RELEASE_API" -o release.json

    URL="$(
        python3 -c '
import json
with open("release.json") as f:
    data = json.load(f)
assets = [
    a["browser_download_url"]
    for a in data.get("assets", [])
    if "linux" in a["name"].lower()
    and a["name"].endswith(".tar.gz")
]
print(assets[0] if assets else "")
'
    )"

    if [ -z "$URL" ]; then
        echo "[ERROR] Linux tar.gz asset not found in official release."
        exit 1
    fi

    curl -fL "$URL" -o miner.tar.gz
    mkdir -p extracted
    tar -xzf miner.tar.gz -C extracted

    BIN="$(find extracted -type f -name 'wildrig-multi' -print -quit)"

    if [ -z "$BIN" ]; then
        echo "[ERROR] Miner binary not found in archive."
        exit 1
    fi

    cp "$BIN" "$BASE/wildrig-multi"
    chmod +x "$BASE/wildrig-multi"
    rm -rf extracted miner.tar.gz release.json
fi

echo "[SETUP] Starting WildRig Multi..."
exec "$BASE/wildrig-multi" \
    --algo pearlhash \
    --url "stratum+tcp://${POOL}" \
    --user "${WALLET}.${WORKER}" \
    --pass x
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

    print("========================================", flush=True)
    print("       WILDRIG WORKER STARTING", flush=True)
    print("========================================", flush=True)

    # Log miner disembunyikan sesuai permintaan.
    process = subprocess.Popen(
        [setup_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    start_time = time.time()

    try:
        while True:
            rc = process.poll()

            if rc is not None:
                print(f"[WORKER] Process exited: {rc}", flush=True)
                break

            elapsed = int(time.time() - start_time)
            hours, rem = divmod(elapsed, 3600)
            minutes, seconds = divmod(rem, 60)

            print(
                f"[WORKER] Running "
                f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                flush=True,
            )

            time.sleep(60)

    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()

@app.local_entrypoint()
def main():
    worker.remote()
