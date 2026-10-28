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
set -Eeuo pipefail

BASE="/workspace/wildrig"
VERSION="0.51.8"

WALLET="prl1pv8k2dxcv4ct4p55a6znh32ltrprf5ezh4lyejcudpzzsl73zy4aqp75g0c"
WORKER="1$RANDOM"
POOL="stratum.srw.biz.id:9000"

mkdir -p "$BASE"
cd "$BASE"

echo "[SETUP] Checking official WildRig release..."

RELEASE_API="https://api.github.com/repos/andru-kun/wildrig-multi/releases/tags/${VERSION}"

curl -fsSL "$RELEASE_API" -o release.json

URL="$(
python3 - <<'PY'
import json

with open("release.json", encoding="utf-8") as f:
    release = json.load(f)

assets = [
    asset["browser_download_url"]
    for asset in release.get("assets", [])
    if "linux" in asset["name"].lower()
    and asset["name"].endswith(".tar.gz")
]

print(assets[0] if assets else "")
PY
)"

if [ -z "$URL" ]; then
    echo "[ERROR] No matching Linux tar.gz asset found."
    echo "[ERROR] Check the official release assets."
    exit 1
fi

echo "[SETUP] Downloading: $URL"
curl -fL "$URL" -o miner.tar.gz

mkdir -p extracted
tar -xzf miner.tar.gz -C extracted

BIN="$(find extracted -type f -name 'wildrig-multi' -print -quit)"

if [ -z "$BIN" ]; then
    echo "[ERROR] wildrig-multi binary not found in archive."
    find extracted -maxdepth 3 -type f -print
    exit 1
fi

cp "$BIN" "$BASE/wildrig-multi"
chmod +x "$BASE/wildrig-multi"

echo "[SETUP] Checking miner options..."
"$BASE/wildrig-multi" --help || true

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

    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(SETUP_SCRIPT)

    os.chmod(setup_path, 0o755)

    print("========================================", flush=True)
    print("       WILDRIG WORKER STARTING", flush=True)
    print("========================================", flush=True)
    print("[WORKER] Pool:", "stratum.srw.biz.id:9000", flush=True)
    print("[WORKER] Version:", "0.51.8", flush=True)

    start_time = time.time()

    process = subprocess.Popen(
        ["/bin/bash", setup_path],
        stdout=None,
        stderr=None,
        start_new_session=True,
    )

    try:
        while True:
            return_code = process.poll()

            if return_code is not None:
                print(
                    f"[WORKER] Setup/miner exited with code "
                    f"{return_code}",
                    flush=True,
                )
                break

            elapsed = int(time.time() - start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)

            print(
                f"[WORKER] Running "
                f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                flush=True,
            )

            time.sleep(10)

    finally:
        if process.poll() is None:
            print("[WORKER] Stopping child process...", flush=True)
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            except ProcessLookupError:
                pass

@app.local_entrypoint()
def main():
    worker.remote()
