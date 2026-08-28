from beam import function, Image
import subprocess
import time


# ============================================================
# BEAM IMAGE
# ============================================================

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates openssh-client procps",
    ])
)


# ============================================================
# BEAM FUNCTION
# ============================================================

@function(
    name="gpu-upterm",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,   # 30 jam
)
def run_script():

    print("")
    print("==========================================")
    print("       BEAM RTX4090 + UPTERM")
    print("==========================================")
    print("")

    # ========================================================
    # GPU CHECK
    # ========================================================

    print("=== GPU ===")

    subprocess.run(
        ["nvidia-smi"],
        check=False,
    )

    # ========================================================
    # BASH SCRIPT
    # ========================================================

    cmd = r"""
set -e

export HOME=/root

# ==========================================================
# CONFIGURATION
# ==========================================================

UPTERM_VERSION="0.24.0"
UPTERM_DIR="/opt/upterm"
UPTERM_BIN="/opt/upterm/upterm"

SSH_DIR="/root/.ssh"
PRIVATE_KEY="$SSH_DIR/id_ed25519"
PUBLIC_KEY="$SSH_DIR/id_ed25519.pub"
KNOWN_HOSTS="$SSH_DIR/known_hosts"

mkdir -p "$UPTERM_DIR"
mkdir -p "$SSH_DIR"

chmod 700 "$SSH_DIR"


# ==========================================================
# INSTALL UPTERM
# ==========================================================

echo ""
echo "=========================================="
echo "          INSTALLING UPTERM"
echo "=========================================="
echo ""

cd /tmp

echo "Downloading Upterm $UPTERM_VERSION..."

wget -q \
    "https://github.com/owenthereal/upterm/releases/download/v${UPTERM_VERSION}/upterm_linux_amd64.tar.gz" \
    -O /tmp/upterm.tar.gz

echo "Download complete."

echo "Extracting Upterm..."

rm -rf "$UPTERM_DIR"

mkdir -p "$UPTERM_DIR"

tar -xzf \
    /tmp/upterm.tar.gz \
    -C "$UPTERM_DIR"


# ==========================================================
# FIND UPTERM BINARY
# ==========================================================

if [ ! -x "$UPTERM_BIN" ]; then

    FOUND=$(find "$UPTERM_DIR" \
        -type f \
        -name "upterm" \
        -perm -111 \
        | head -n 1)

    if [ -z "$FOUND" ]; then

        echo ""
        echo "ERROR: Upterm binary not found."
        echo ""

        find "$UPTERM_DIR" \
            -maxdepth 3 \
            -type f \
            -print || true

        exit 1
    fi

    UPTERM_BIN="$FOUND"

fi

chmod +x "$UPTERM_BIN"


# ==========================================================
# UPTERM VERSION
# ==========================================================

echo ""
echo "=========================================="
echo "          UPTERM VERSION"
echo "=========================================="
echo ""

"$UPTERM_BIN" version || \
"$UPTERM_BIN" --version || true


# ==========================================================
# CREATE SSH KEY
# ==========================================================

echo ""
echo "=========================================="
echo "           CREATE SSH KEY"
echo "=========================================="
echo ""

if [ ! -f "$PRIVATE_KEY" ]; then

    ssh-keygen \
        -t ed25519 \
        -f "$PRIVATE_KEY" \
        -N "" \
        -C "beam-upterm"

fi

chmod 600 "$PRIVATE_KEY"
chmod 644 "$PUBLIC_KEY"

touch "$KNOWN_HOSTS"

chmod 644 "$KNOWN_HOSTS"

echo "SSH public key:"
cat "$PUBLIC_KEY"


# ==========================================================
# START UPTERM
# ==========================================================

echo ""
echo "=========================================="
echo "          STARTING UPTERM"
echo "=========================================="
echo ""

rm -f /tmp/upterm.log
rm -f /tmp/upterm-session

"$UPTERM_BIN" host \
    --accept \
    > /tmp/upterm.log 2>&1 &

UPTERM_PID=$!

echo "Upterm PID: $UPTERM_PID"


# ==========================================================
# WAIT FOR SSH CONNECTION STRING
# ==========================================================

echo ""
echo "=========================================="
echo "       WAITING FOR UPTERM SSH"
echo "=========================================="
echo ""

SSH_COMMAND=""

for i in $(seq 1 60); do

    # ------------------------------------------------------
    # CHECK PROCESS
    # ------------------------------------------------------

    if ! kill -0 "$UPTERM_PID" 2>/dev/null; then

        echo ""
        echo "ERROR: UPTERM PROCESS EXITED"
        echo ""

        echo "========== UPTERM LOG =========="

        cat /tmp/upterm.log || true

        echo ""
        echo "================================"

        exit 1

    fi


    # ------------------------------------------------------
    # GET CURRENT SESSION
    # ------------------------------------------------------

    SESSION_OUTPUT=$(
        "$UPTERM_BIN" session current 2>/dev/null || true
    )

    echo "$SESSION_OUTPUT" > /tmp/upterm-session


    # ------------------------------------------------------
    # FIND SSH COMMAND
    # ------------------------------------------------------

    SSH_COMMAND=$(
        echo "$SESSION_OUTPUT" |
        grep -E '^[[:space:]]*ssh ' |
        head -n 1 |
        sed 's/^[[:space:]]*//'
    )


    # ------------------------------------------------------
    # SSH FOUND
    # ------------------------------------------------------

    if [ -n "$SSH_COMMAND" ]; then

        echo ""
        echo "=========================================="
        echo "             SSH READY"
        echo "=========================================="
        echo ""
        echo "COPY THIS COMMAND:"
        echo ""
        echo "$SSH_COMMAND"
        echo ""
        echo "=========================================="
        echo ""

        break

    fi


    echo "Waiting for Upterm... $i/60"

    sleep 2

done


# ==========================================================
# VERIFY SSH
# ==========================================================

if [ -z "$SSH_COMMAND" ]; then

    echo ""
    echo "=========================================="
    echo "       UPTERM SSH NOT AVAILABLE"
    echo "=========================================="
    echo ""

    echo "========== UPTERM LOG =========="

    cat /tmp/upterm.log || true

    echo ""
    echo "======= SESSION OUTPUT ========="

    cat /tmp/upterm-session 2>/dev/null || true

    echo ""
    echo "================================"

    exit 1

fi


# ==========================================================
# GPU STATUS
# ==========================================================

echo ""
echo "=========================================="
echo "             GPU STATUS"
echo "=========================================="
echo ""

nvidia-smi


# ==========================================================
# SYSTEM STATUS
# ==========================================================

echo ""
echo "=========================================="
echo "           SYSTEM STATUS"
echo "=========================================="
echo ""

echo "Hostname:"
hostname

echo ""

echo "CPU:"
nproc

echo ""

echo "Memory:"
free -h

echo ""

echo "Disk:"
df -h /


# ==========================================================
# CONTAINER STATUS
# ==========================================================

echo ""
echo "=========================================="
echo "       CONTAINER IS RUNNING"
echo "=========================================="
echo ""

echo "GPU       : RTX4090"
echo "CPU       : 2"
echo "RAM       : 4Gi"
echo "TIMEOUT   : 30 HOURS"
echo ""

echo "SSH access is provided by Upterm."
echo "You can disconnect SSH without stopping"
echo "the Beam container."

echo ""


# ==========================================================
# KEEP CONTAINER ALIVE
# ==========================================================

while true; do

    echo ""
    echo "=========================================="
    echo "             HEARTBEAT"
    echo "=========================================="

    date

    echo ""

    nvidia-smi \
        --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu \
        --format=csv,noheader \
        2>/dev/null || true

    echo ""

    echo "Upterm PID: $UPTERM_PID"

    if kill -0 "$UPTERM_PID" 2>/dev/null; then
        echo "Upterm status: RUNNING"
    else
        echo "Upterm status: STOPPED"
    fi

    echo ""

    # 10 menit
    sleep 600

done
"""

    # ========================================================
    # EXECUTE BASH
    # ========================================================

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print("")
    print("==========================================")
    print("       BASH PROCESS EXITED")
    print("==========================================")
    print("")
    print("Exit code:", result.returncode)

    # ========================================================
    # FINAL KEEP ALIVE
    # ========================================================

    while True:
        time.sleep(3600)
