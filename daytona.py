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


# ============================================================
# DAYTONA
# ============================================================

if not os.getenv("DAYTONA_API_KEY"):
    print("ERROR: DAYTONA_API_KEY belum diset.")
    sys.exit(1)

daytona = Daytona()

print("\n" + "=" * 55)
print(" Daytona - SRBMiner RandomX / unMineable LTC")
print("=" * 55)


# ============================================================
# CREATE SANDBOX
# ============================================================

print("[+] Creating sandbox...")

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

print(f"[+] Sandbox : {sandbox.id}")
print(f"[+] CPU     : {CPU} vCPU")
print(f"[+] RAM     : {RAM} GB")
print(f"[+] Disk    : {DISK} GB")


# ============================================================
# INSTALL DEPENDENCIES
# ============================================================

print("\n[+] Installing dependencies...")

result = sandbox.process.exec(
    """
    apt-get update -y &&
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        wget \
        ca-certificates \
        tar \
        procps \
        curl
    """,
    timeout=300,
)

if result.exit_code != 0:
    print(result.result)
    sys.exit(1)


# ============================================================
# INSTALL SRBMINER
# ============================================================

print("[+] Installing SRBMiner-Multi...")

version_url = SRB_VERSION.replace(".", "-")

cmd = f"""
cd /tmp &&
rm -rf SRBMiner-Multi-* srbminer.tar.gz &&
wget -q \
"https://github.com/doktor83/SRBMiner-Multi/releases/download/{SRB_VERSION}/SRBMiner-Multi-{version_url}-Linux.tar.gz" \
-O srbminer.tar.gz &&
tar -xzf srbminer.tar.gz &&
find /tmp -type f -name SRBMiner-MULTI \
    -exec cp {{}} /usr/local/bin/SRBMiner-MULTI \\; &&
chmod +x /usr/local/bin/SRBMiner-MULTI &&
/usr/local/bin/SRBMiner-MULTI --version
"""

result = sandbox.process.exec(cmd, timeout=300)

if result.exit_code != 0:
    print("\n[!] Gagal memasang SRBMiner.")
    print(result.result)
    sys.exit(1)

print(result.result)


# ============================================================
# CREATE MINER SCRIPT
# ============================================================

print("[+] Creating miner script...")

miner = f"""#!/bin/bash

exec /usr/local/bin/SRBMiner-MULTI \\
    --algorithm {ALGO} \\
    --pool {POOL} \\
    --wallet "{WALLET}.{WORKER}" \\
    --cpu-threads {CPU}
"""

result = sandbox.process.exec(
    f"""
cat > /root/start-miner.sh <<'EOF'
{miner}
EOF

chmod +x /root/start-miner.sh
""",
    timeout=30,
)

if result.exit_code != 0:
    print("[!] Gagal membuat start-miner.sh")
    print(result.result)
    sys.exit(1)


# ============================================================
# START SESSION
# ============================================================

SESSION = "srbminer-ltc"

print("[+] Starting miner session...")

try:
    sandbox.process.create_session(SESSION)
except Exception:
    pass

session = sandbox.process.get_session(SESSION)

session.execute_command(
    "/root/start-miner.sh",
    timeout=30,
)


# ============================================================
# STATUS
# ============================================================

print("\n" + "=" * 55)
print(" MINER STARTED")
print("=" * 55)

print(f"Sandbox  : {sandbox.id}")
print(f"Worker   : {WORKER}")
print(f"CPU      : {CPU} vCPU")
print(f"Algorithm: {ALGO}")
print(f"Pool     : {POOL}")
print(f"Wallet   : {WALLET}")
print(f"Session  : {SESSION}")

print("=" * 55)
print("Sandbox akan tetap berjalan.")
print("Tekan Ctrl+C untuk keluar dari controller.")
print("=" * 55)


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

        if status.result.strip():
            print("[OK] SRBMiner masih berjalan.")
        else:
            print("[!] SRBMiner tidak ditemukan.")

except KeyboardInterrupt:
    print("\n[+] Controller dihentikan.")
    print("[+] Sandbox tetap berjalan.")
