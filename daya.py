import os
import sys
import time

from daytona import Daytona, CreateSandboxFromImageParams, Resources


# ============================================================
# CONFIG
# ============================================================

WALLET = "ltc1qwae89dljtedxyvgrgl5ug8rk7xeqaruh5utxrg"
WORKER = "daytona-ltc-01"

CPU = 4
RAM = 8
DISK = 10

ALGO = "randomx"
POOL = "rx.unmineable.com:443"

SRB_VERSION = "3.6.2"
SANDBOX_NAME = "ltc-randomx-worker"

SESSION = "srbminer-ltc"


# ============================================================
# CHECK API KEY
# ============================================================

if not os.getenv("DAYTONA_API_KEY"):
    print("ERROR: DAYTONA_API_KEY belum diset.")
    print()
    print('Jalankan:')
    print('export DAYTONA_API_KEY="API_KEY_KAMU"')
    sys.exit(1)


# ============================================================
# DAYTONA
# ============================================================

daytona = Daytona()

print()
print("=" * 60)
print(" Daytona - SRBMiner RandomX / unMineable LTC")
print("=" * 60)


# ============================================================
# GET OR CREATE SANDBOX
# ============================================================

print()
print("[+] Checking sandbox...")

sandbox = None

try:
    sandbox = daytona.get(SANDBOX_NAME)

    print("[+] Sandbox sudah ada.")
    print(f"[+] Sandbox : {sandbox.id}")

except Exception as e:

    print("[+] Sandbox belum ditemukan.")
    print("[+] Membuat sandbox baru...")

    try:
        sandbox = daytona.create(
            CreateSandboxFromImageParams(
                image="ubuntu:22.04",
                name=SANDBOX_NAME,
                resources=Resources(
                    cpu=CPU,
                    memory=RAM,
                    disk=DISK,
                ),
                env_vars={
                    "WALLET": WALLET,
                    "WORKER": WORKER,
                },
                auto_stop_interval=0,
            ),
            timeout=120,
        )

        print("[+] Sandbox baru berhasil dibuat.")
        print(f"[+] Sandbox : {sandbox.id}")

    except Exception as e:
        print()
        print("[!] Gagal membuat sandbox.")
        print(e)
        sys.exit(1)


print(f"[+] CPU     : {CPU} vCPU")
print(f"[+] RAM     : {RAM} GB")
print(f"[+] Disk    : {DISK} GB")


# ============================================================
# EXEC HELPER WITH RETRY
# ============================================================

def exec_retry(command, description, timeout=120, retries=4):

    print()
    print(f"[+] {description}")

    last_error = None

    for attempt in range(1, retries + 1):

        print(f"    Attempt {attempt}/{retries}")

        try:

            result = sandbox.process.exec(
                command,
                timeout=timeout,
            )

            if result.exit_code == 0:

                if result.result:
                    print(result.result)

                print(f"[OK] {description}")
                return result

            else:

                print(f"[!] Exit code: {result.exit_code}")

                if result.result:
                    print(result.result)

                last_error = result

        except Exception as e:

            last_error = e

            print(f"[!] Error: {e}")

        if attempt < retries:
            print("    Menunggu 10 detik sebelum retry...")
            time.sleep(10)

    print()
    print("=" * 60)
    print(f"[ERROR] Gagal: {description}")
    print("=" * 60)

    if last_error:
        print(last_error)

    sys.exit(1)


# ============================================================
# CHECK SANDBOX
# ============================================================

exec_retry(
    "echo 'Sandbox OK' && uname -a",
    "Checking sandbox",
    timeout=30,
)


# ============================================================
# UPDATE APT
# ============================================================

exec_retry(
    "apt-get update -y",
    "Updating package list",
    timeout=300,
)


# ============================================================
# INSTALL DEPENDENCIES
# ============================================================

exec_retry(
    """
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    wget \
    ca-certificates \
    tar \
    procps \
    curl
""",
    "Installing dependencies",
    timeout=300,
)


# ============================================================
# CLEAN OLD SRBMINER FILES
# ============================================================

exec_retry(
    """
rm -rf /tmp/SRBMiner-Multi-*
rm -f /tmp/srbminer.tar.gz
rm -f /usr/local/bin/SRBMiner-MULTI
""",
    "Cleaning old SRBMiner files",
    timeout=30,
)


# ============================================================
# DOWNLOAD SRBMINER
# ============================================================

VERSION_URL = SRB_VERSION.replace(".", "-")

DOWNLOAD_URL = (
    f"https://github.com/doktor83/SRBMiner-Multi/releases/download/"
    f"{SRB_VERSION}/"
    f"SRBMiner-Multi-{VERSION_URL}-Linux.tar.gz"
)

exec_retry(
    f"""
cd /tmp

wget -q --show-progress \
    "{DOWNLOAD_URL}" \
    -O /tmp/srbminer.tar.gz
""",
    "Downloading SRBMiner-Multi",
    timeout=300,
)


# ============================================================
# CHECK DOWNLOAD
# ============================================================

exec_retry(
    """
test -s /tmp/srbminer.tar.gz
ls -lh /tmp/srbminer.tar.gz
""",
    "Checking SRBMiner download",
    timeout=30,
)


# ============================================================
# EXTRACT SRBMINER
# ============================================================

exec_retry(
    """
cd /tmp
tar -xzf /tmp/srbminer.tar.gz
""",
    "Extracting SRBMiner-Multi",
    timeout=120,
)


# ============================================================
# FIND BINARY
# ============================================================

exec_retry(
    """
BINARY=$(find /tmp -type f -name SRBMiner-MULTI | head -n 1)

if [ -z "$BINARY" ]; then
    echo "SRBMiner-MULTI binary tidak ditemukan."
    find /tmp -maxdepth 3 -type f | head -100
    exit 1
fi

echo "Binary ditemukan:"
echo "$BINARY"
""",
    "Finding SRBMiner binary",
    timeout=60,
)


# ============================================================
# INSTALL BINARY
# ============================================================

exec_retry(
    """
BINARY=$(find /tmp -type f -name SRBMiner-MULTI | head -n 1)

if [ -z "$BINARY" ]; then
    echo "Binary tidak ditemukan."
    exit 1
fi

cp "$BINARY" /usr/local/bin/SRBMiner-MULTI
chmod +x /usr/local/bin/SRBMiner-MULTI

ls -lh /usr/local/bin/SRBMiner-MULTI
""",
    "Installing SRBMiner binary",
    timeout=60,
)


# ============================================================
# TEST SRBMINER
# ============================================================

exec_retry(
    """
/usr/local/bin/SRBMiner-MULTI --version
""",
    "Testing SRBMiner-Multi",
    timeout=60,
)


# ============================================================
# CREATE MINER SCRIPT
# ============================================================

print()
print("[+] Creating miner script...")

miner_script = f"""#!/bin/bash

exec /usr/local/bin/SRBMiner-MULTI \\
    --algorithm {ALGO} \\
    --pool {POOL} \\
    --wallet "{WALLET}.{WORKER}" \\
    --cpu-threads {CPU}
"""


exec_retry(
    f"""
cat > /root/start-miner.sh <<'EOF'
{miner_script}
EOF

chmod +x /root/start-miner.sh

echo "===== /root/start-miner.sh ====="
cat /root/start-miner.sh
echo "================================"
""",
    "Creating miner script",
    timeout=30,
)


# ============================================================
# CHECK MINER FILES
# ============================================================

exec_retry(
    """
test -x /root/start-miner.sh
test -x /usr/local/bin/SRBMiner-MULTI
""",
    "Checking miner files",
    timeout=30,
)


# ============================================================
# CREATE / GET SESSION
# ============================================================

print()
print("[+] Checking miner session...")

try:

    sandbox.process.create_session(SESSION)

    print(f"[+] Session baru dibuat: {SESSION}")

except Exception as e:

    print(f"[+] Session mungkin sudah ada: {SESSION}")
    print(f"    {e}")


try:

    session = sandbox.process.get_session(SESSION)

except Exception as e:

    print("[!] Gagal mendapatkan session.")
    print(e)
    sys.exit(1)


# ============================================================
# START MINER
# ============================================================

print()
print("[+] Starting SRBMiner...")

try:

    session.execute_command(
        "/root/start-miner.sh",
        timeout=30,
    )

    print("[OK] Command miner sudah dikirim.")

except Exception as e:

    print("[!] Gagal menjalankan miner session.")
    print(e)
    sys.exit(1)


# ============================================================
# STATUS
# ============================================================

print()
print("=" * 60)
print(" MINER STARTED")
print("=" * 60)

print(f"Sandbox  : {sandbox.id}")
print(f"Name     : {SANDBOX_NAME}")
print(f"Worker   : {WORKER}")
print(f"CPU      : {CPU} vCPU")
print(f"RAM      : {RAM} GB")
print(f"Algorithm: {ALGO}")
print(f"Pool     : {POOL}")
print(f"Wallet   : {WALLET}")
print(f"Session  : {SESSION}")

print("=" * 60)
print("Sandbox akan tetap berjalan.")
print("Controller VPS boleh dihentikan.")
print("=" * 60)


# ============================================================
# MONITOR
# ============================================================

try:

    while True:

        time.sleep(30)

        status = sandbox.process.exec(
            "pgrep -af SRBMiner-MULTI || true",
            timeout=10,
        )

        output = (status.result or "").strip()

        if output:

            print()
            print("[OK] SRBMiner masih berjalan.")
            print(output)

        else:

            print()
            print("[!] SRBMiner tidak ditemukan.")

except KeyboardInterrupt:

    print()
    print("[+] Controller dihentikan.")
    print("[+] Sandbox tetap berjalan.")
