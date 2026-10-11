```bash
#!/usr/bin/env bash
# ============================================================
# pearl-rig-up.sh
#
# Configure any Vast.ai NVIDIA rig for YOUR Pearl pool.
#
# Usage:
#   curl -sL <raw-url> | bash
#
# SRBMiner: 3.5.3
# Algorithm: pearlhash
#
# Features:
#   - Cleans up old SRBMiner / alpha-miner / reporters
#   - Detects Vast rig ID
#   - Detects REAL NVIDIA GPU name
#   - Detects GPU count
#   - Installs SRBMiner-MULTI 3.5.3
#   - Verifies SRBMiner binary
#   - Starts SRBMiner API
#   - Verifies API before reporter starts
#   - Reports REAL GPU name + hashrate to dashboard
#   - Safe to re-run
# ============================================================

set -u

# ============================================================
# CONFIG
# ============================================================

MAC_IP="173.239.94.174"
POOL_PORT="3333"
STATS_PORT="9101"
API_PORT="21555"

WALLET="prl1pslert7uwnue75e7kwgcx3438rlefyue74f336ls5f0yzemtxnpksesrw52"

SRB_VER="3.5.3"
SRB_NAME="SRBMiner-Multi-3-5-3"
SRB_DIR="/root/${SRB_NAME}"

SRB_URL="https://github.com/doktor83/SRBMiner-Multi/releases/download/${SRB_VER}/SRBMiner-Multi-3-5-3-Linux.tar.gz"

SRB_ARCHIVE="/root/${SRB_NAME}.tar.gz"

# Official MD5 from the SRBMiner 3.5.3 release
SRB_MD5="9ab5beec11bd58480d20415273649799c"

REPORTER="/root/srb-report.sh"
REPORTER_LOG="/root/reporter.log"
MINER_LOG="/root/srbminer.log"


# ============================================================
# FUNCTIONS
# ============================================================

log() {
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

die() {
    echo
    echo "ERROR: $1"
    exit 1
}


# ============================================================
# [1/8] CLEANUP
# ============================================================

log "[1/8] Cleaning up old miners / reporters"

pkill -9 -f "alpha-miner" 2>/dev/null || true
pkill -9 -f "SRBMiner-MULTI" 2>/dev/null || true
pkill -9 -f "SRBMiner-Multi" 2>/dev/null || true
pkill -9 -f "srb-report.sh" 2>/dev/null || true

sleep 2

echo "Old miner processes stopped."


# ============================================================
# [2/8] GPU DETECTION
# ============================================================

log "[2/8] Detecting NVIDIA GPU"

command -v nvidia-smi >/dev/null 2>&1 || \
    die "nvidia-smi was not found. NVIDIA driver/GPU is not available."

GPU_LIST="$(nvidia-smi \
    --query-gpu=name \
    --format=csv,noheader 2>/dev/null)"

[ -n "$GPU_LIST" ] || \
    die "NVIDIA GPU was not detected."

GPU_RAW="$(echo "$GPU_LIST" | head -1)"

NGPU="$(echo "$GPU_LIST" | wc -l | tr -d ' ')"

[ -n "$NGPU" ] || NGPU=1

echo "GPU(s):"
echo "$GPU_LIST" | sed 's/^/    /'

echo
echo "GPU count: $NGPU"


# ============================================================
# GPU TAG
# ============================================================

GPU_TAG="$(
    echo "$GPU_RAW" |
    grep -oiE 'RTX *[0-9]{4} *(Ti|SUPER)?' |
    head -1 |
    tr -d ' ' |
    tr 'a-z' 'A-Z'
)"

if [ -z "$GPU_TAG" ]; then
    GPU_TAG="GPU"
fi


# ============================================================
# [3/8] DETECT VAST ID
# ============================================================

log "[3/8] Detecting Vast rig ID"

VASTID=""

# Environment variables
for v in \
    "$CONTAINER_ID" \
    "$VAST_CONTAINERLABEL" \
    "$VAST_INSTANCE_ID" \
    "$INSTANCE_ID"
do

    cand="$(
        echo "$v" |
        grep -oE '[0-9]{6,}' |
        head -1
    )"

    if [ -n "$cand" ]; then
        VASTID="$cand"
        break
    fi

done


# ------------------------------------------------------------
# Vast hostname / container label
# ------------------------------------------------------------

if [ -z "$VASTID" ]; then

    for f in \
        /etc/hostname \
        /proc/sys/kernel/hostname \
        /root/.vast_containerlabel
    do

        if [ -f "$f" ]; then

            cand="$(
                grep -hoE 'C\.[0-9]{6,}' "$f" 2>/dev/null |
                grep -oE '[0-9]{6,}' |
                head -1
            )"

            if [ -n "$cand" ]; then
                VASTID="$cand"
                break
            fi

        fi

    done

fi


# ------------------------------------------------------------
# Environment dump
# ------------------------------------------------------------

if [ -z "$VASTID" ]; then

    cand="$(
        env |
        grep -oE 'C\.[0-9]{6,}' |
        grep -oE '[0-9]{6,}' |
        head -1
    )"

    if [ -n "$cand" ]; then
        VASTID="$cand"
    fi

fi


# ------------------------------------------------------------
# Last resort
# ------------------------------------------------------------

if [ -z "$VASTID" ]; then
    VASTID="$(hostname | cut -c1-8)"
fi


WORKER="${GPU_TAG}-${VASTID}"

echo "Vast ID:    $VASTID"
echo "GPU:        $GPU_RAW"
echo "GPU tag:    $GPU_TAG"
echo "GPU count:  $NGPU"
echo "Worker:     $WORKER"


# ============================================================
# [4/8] INSTALL SRBMINER 3.5.3
# ============================================================

log "[4/8] Installing SRBMiner-MULTI ${SRB_VER}"

# Remove previous 3.3.x / 3.5.x directories
rm -rf \
    /root/SRBMiner-Multi-3-3-* \
    /root/SRBMiner-Multi-3-4-* \
    /root/SRBMiner-Multi-3-5-* \
    2>/dev/null || true

rm -f "$SRB_ARCHIVE"


echo "Downloading:"
echo "$SRB_URL"

curl -fL --retry 3 --retry-delay 2 \
    -o "$SRB_ARCHIVE" \
    "$SRB_URL" || \
    die "Failed to download SRBMiner ${SRB_VER}."


# ------------------------------------------------------------
# Verify MD5
# ------------------------------------------------------------

echo
echo "Verifying SRBMiner archive..."

ACTUAL_MD5="$(
    md5sum "$SRB_ARCHIVE" |
    awk '{print $1}'
)"

echo "Expected: $SRB_MD5"
echo "Actual:   $ACTUAL_MD5"

if [ "$ACTUAL_MD5" != "$SRB_MD5" ]; then
    rm -f "$SRB_ARCHIVE"
    die "MD5 verification FAILED."
fi

echo "MD5 verification PASSED."


# ------------------------------------------------------------
# Extract
# ------------------------------------------------------------

cd /root || die "Could not cd to /root."

tar xzf "$SRB_ARCHIVE" || \
    die "Failed to extract SRBMiner archive."


# ------------------------------------------------------------
# Locate extracted directory
# ------------------------------------------------------------

if [ ! -x "$SRB_DIR/SRBMiner-MULTI" ]; then

    FOUND_DIR="$(
        find /root \
            -maxdepth 1 \
            -type d \
            -name "SRBMiner-Multi-3-5-3" \
            -print -quit
    )"

    if [ -n "$FOUND_DIR" ]; then
        SRB_DIR="$FOUND_DIR"
    fi

fi


SRB_BIN="$SRB_DIR/SRBMiner-MULTI"

[ -x "$SRB_BIN" ] || \
    die "SRBMiner binary not found after extraction."


echo
echo "SRBMiner installed:"
echo "$SRB_BIN"


# ============================================================
# VERIFY SRBMINER VERSION
# ============================================================

echo
echo "Checking SRBMiner version..."

"$SRB_BIN" --version 2>&1 | head -5 || true


# ============================================================
# [5/8] WRITE REPORTER
# ============================================================

log "[5/8] Creating hashrate reporter"

cat > "$REPORTER" << 'REPEOF'
#!/usr/bin/env bash

MAC_IP="${MAC_IP:-173.239.94.174}"
STATS_PORT="${STATS_PORT:-9101}"
API_PORT="${API_PORT:-21555}"

WORKER="${WORKER:-$(hostname)}"
GPU_NAME="${GPU_NAME:-}"

echo "SRBMiner reporter starting..."
echo "Worker:   $WORKER"
echo "GPU:      $GPU_NAME"
echo "API:      127.0.0.1:$API_PORT"
echo "Dashboard: $MAC_IP:$STATS_PORT"

while true; do

    J="$(
        curl -s \
            --max-time 4 \
            "http://127.0.0.1:${API_PORT}/" \
            2>/dev/null
    )"

    if [ -n "$J" ]; then

        python3 - "$J" "$WORKER" "$MAC_IP" "$STATS_PORT" "$GPU_NAME" << 'PYEOF'

import sys
import json
import urllib.request

raw, worker, mac, port, gpu = sys.argv[1:6]

try:

    d = json.loads(raw)

    algorithms = d.get("algorithms", [])

    if not algorithms:
        raise Exception("No algorithms returned by SRBMiner API")

    alg = algorithms[0]

    # --------------------------------------------------------
    # Hashrate
    # --------------------------------------------------------

    hr = alg.get("hashrate", {}).get("gpu", {})

    total_hs = float(
        hr.get("total", 0) or 0
    )

    # --------------------------------------------------------
    # GPU count
    # --------------------------------------------------------

    gpu_keys = [
        k for k in hr
        if k.startswith("gpu") and k != "total"
    ]

    ngpu = len(gpu_keys)

    if ngpu < 1:
        ngpu = 1

    # --------------------------------------------------------
    # Shares
    # --------------------------------------------------------

    accepted = sum(
        (alg.get("gpu_accepted_shares", {}) or {}).values()
    )

    rejected = sum(
        (alg.get("gpu_rejected_shares", {}) or {}).values()
    )

    # --------------------------------------------------------
    # Dashboard payload
    # --------------------------------------------------------

    payload = json.dumps({
        "worker": worker,
        "hashrate_ths": total_hs / 1e12,
        "gpu": gpu,
        "gpu_count": ngpu,
        "accepted": accepted,
        "rejected": rejected
    }).encode()

    req = urllib.request.Request(
        f"http://{mac}:{port}/report",
        data=payload,
        headers={
            "Content-Type": "application/json"
        }
    )

    urllib.request.urlopen(
        req,
        timeout=4
    ).read()

except Exception:
    pass

PYEOF

    fi

    sleep 15

done
REPEOF

chmod +x "$REPORTER"


# ============================================================
# [6/8] START SRBMINER
# ============================================================

log "[6/8] Starting SRBMiner-MULTI ${SRB_VER}"

cd "$SRB_DIR" || \
    die "Could not enter SRBMiner directory."


echo "Starting miner..."
echo
echo "Pool:   ${MAC_IP}:${POOL_PORT}"
echo "Wallet: ${WALLET}"
echo "Worker: ${WORKER}"
echo "API:    ${API_PORT}"
echo


# ------------------------------------------------------------
# Start miner in background temporarily
# ------------------------------------------------------------

nohup "$SRB_BIN" \
    --algorithm pearlhash \
    --pool "stratum+tcp://${MAC_IP}:${POOL_PORT}" \
    --wallet "$WALLET" \
    --worker "$WORKER" \
    --api-enable \
    --api-port "$API_PORT" \
    > "$MINER_LOG" 2>&1 &

MINER_PID=$!

echo "SRBMiner PID: $MINER_PID"


# ============================================================
# [7/8] VERIFY API
# ============================================================

log "[7/8] Verifying SRBMiner API"

API_OK=0

for i in $(seq 1 20); do

    sleep 1

    if curl -sf \
        --max-time 2 \
        "http://127.0.0.1:${API_PORT}/" \
        >/tmp/srb-api.json 2>/dev/null
    then

        API_OK=1
        break

    fi

    echo "Waiting for SRBMiner API... ($i/20)"

done


if [ "$API_OK" -ne 1 ]; then

    echo
    echo "SRBMiner API did not respond."
    echo
    echo "Last miner log:"
    tail -50 "$MINER_LOG"

    kill "$MINER_PID" 2>/dev/null || true

    die "SRBMiner API verification FAILED."

fi


echo
echo "SRBMiner API is ONLINE."

echo
echo "API response:"
head -c 500 /tmp/srb-api.json
echo


# ============================================================
# [8/8] START REPORTER
# ============================================================

log "[8/8] Starting dashboard reporter"

pkill -9 -f "srb-report.sh" 2>/dev/null || true

WORKER="$WORKER" \
MAC_IP="$MAC_IP" \
STATS_PORT="$STATS_PORT" \
API_PORT="$API_PORT" \
GPU_NAME="$GPU_RAW" \
nohup bash "$REPORTER" \
    > "$REPORTER_LOG" 2>&1 &

REPORTER_PID=$!

echo "Reporter PID: $REPORTER_PID"


# ============================================================
# FINAL STATUS
# ============================================================

sleep 2

echo
echo "============================================================"
echo "                 PEARL RIG IS ONLINE"
echo "============================================================"
echo
echo "SRBMiner:     ${SRB_VER}"
echo "Algorithm:    pearlhash"
echo "GPU:          ${GPU_RAW}"
echo "GPU count:    ${NGPU}"
echo "Vast ID:      ${VASTID}"
echo "Worker:       ${WORKER}"
echo
echo "Pool:         ${MAC_IP}:${POOL_PORT}"
echo "API:          127.0.0.1:${API_PORT}"
echo "Dashboard:    ${MAC_IP}:${STATS_PORT}"
echo
echo "Miner PID:    ${MINER_PID}"
echo "Reporter PID: ${REPORTER_PID}"
echo
echo "Miner log:    ${MINER_LOG}"
echo "Reporter log: ${REPORTER_LOG}"
echo
echo "============================================================"
echo

echo "Current miner process:"
ps -p "$MINER_PID" -o pid,etime,cmd 2>/dev/null || true

echo
echo "Current GPU:"
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu --format=csv,noheader 2>/dev/null || true

echo
echo "============================================================"
echo "Done."
echo "============================================================"
```
