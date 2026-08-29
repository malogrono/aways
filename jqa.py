from beam import function, Image
import subprocess
import time

============================================================
BEAM IMAGE
============================================================

image = (
Image(
base_image="nvidia/cuda:12.4.1-runtime-ubuntu22.04",
)
.add_commands([
"apt-get update -y",
"apt-get install -y wget ca-certificates tar",
"rm -rf /var/lib/apt/lists/*",
])
)

============================================================
CONFIGURATION
============================================================

SRB_VERSION = "3.5.4"

SRB_URL = (
"https://github.com/doktor83/SRBMiner-Multi/releases/"
"download/3.5.4/"
"SRBMiner-Multi-3-5-4-Linux.tar.gz"
)

PEARL_POOL = "prl.kryptex.network:7048"

PEARL_WALLET = (
"prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

WORKER_NAME = "beam-4090"

============================================================
BEAM FUNCTION
============================================================

@function(
name="hama",
image=image,
gpu="RTX4090",
cpu=2,
memory="4Gi",
timeout=27 * 60 * 60,
)
def run_pearl():

print("=" * 60)
print("       PEARL SRBMINER - BEAM RTX 4090")
print("=" * 60)

# --------------------------------------------------------
# 1. GPU CHECK
# --------------------------------------------------------

print("\n[1] Checking GPU...")

gpu_result = subprocess.run(
    ["bash", "-lc", "nvidia-smi"],
    check=False,
)

if gpu_result.returncode != 0:
    raise RuntimeError(
        "NVIDIA GPU tidak terdeteksi."
    )

# --------------------------------------------------------
# 2. PREPARE DIRECTORY
# --------------------------------------------------------

workdir = "/workspace/srbminer"

subprocess.run(
    [
        "bash",
        "-lc",
        f"mkdir -p {workdir}",
    ],
    check=True,
)

archive = f"{workdir}/srbminer.tar.gz"

# --------------------------------------------------------
# 3. DOWNLOAD SRBMINER
# --------------------------------------------------------

print("\n[2] Downloading SRBMiner-MULTI...")
print("Version:", SRB_VERSION)

download_cmd = (
    f'wget --tries=3 --timeout=30 '
    f'-O "{archive}" '
    f'"{SRB_URL}"'
)

result = subprocess.run(
    ["bash", "-lc", download_cmd],
    check=False,
)

if result.returncode != 0:
    raise RuntimeError(
        "Gagal mendownload SRBMiner-MULTI."
    )

# --------------------------------------------------------
# 4. EXTRACT
# --------------------------------------------------------

print("\n[3] Extracting SRBMiner...")

extract_cmd = (
    f'tar -xzf "{archive}" '
    f'-C "{workdir}"'
)

result = subprocess.run(
    ["bash", "-lc", extract_cmd],
    check=False,
)

if result.returncode != 0:
    raise RuntimeError(
        "Gagal extract SRBMiner."
    )

# --------------------------------------------------------
# 5. FIND BINARY
# --------------------------------------------------------

print("\n[4] Finding SRBMiner binary...")

find_cmd = (
    f'find "{workdir}" '
    f'-type f -name "SRBMiner-MULTI" '
    f'| head -n 1'
)

result = subprocess.run(
    ["bash", "-lc", find_cmd],
    capture_output=True,
    text=True,
    check=False,
)

miner = result.stdout.strip()

if not miner:
    raise RuntimeError(
        "Binary SRBMiner-MULTI tidak ditemukan."
    )

subprocess.run(
    ["bash", "-lc", f'chmod +x "{miner}"'],
    check=False,
)

print("Miner:", miner)

# --------------------------------------------------------
# 6. DISPLAY CONFIG
# --------------------------------------------------------

print("\n[5] Mining configuration")
print("--------------------------------------------")
print("GPU       : RTX 4090")
print("Miner     : SRBMiner-MULTI", SRB_VERSION)
print("Algorithm : pearlhash")
print("Pool      :", PEARL_POOL)
print("Worker    :", WORKER_NAME)
print("Wallet    : configured")
print("--------------------------------------------")

# --------------------------------------------------------
# 7. START MINER
# --------------------------------------------------------

print("\n[6] Starting PearlHash miner...\n")

wallet_worker = (
    f"{PEARL_WALLET}.{WORKER_NAME}"
)

command = [
    miner,
    "--disable-cpu",
    "--algorithm",
    "pearlhash",
    "--pool",
    PEARL_POOL,
    "--wallet",
    wallet_worker,
    "--password",
    "x",
]

print(
    "Starting SRBMiner-MULTI..."
)

process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)

# --------------------------------------------------------
# 8. STREAM MINER LOG
# --------------------------------------------------------

try:

    while True:

        line = process.stdout.readline()

        if line:
            print(
                "[SRB]",
                line.rstrip(),
                flush=True,
            )

        if process.poll() is not None:
            break

        time.sleep(0.1)

except KeyboardInterrupt:

    print(
        "\nStopping SRBMiner..."
    )

    process.terminate()

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()

finally:

    print()
    print("=" * 60)
    print("SRBMiner STOPPED")
    print("Exit code:", process.poll())
    print("=" * 60)
============================================================
ENTRYPOINT
============================================================

if name == "main":

print("=" * 60)
print("Deploying PearlHash SRBMiner to Beam")
print("=" * 60)
print()
print("GPU   : RTX4090")
print("Pool  :", PEARL_POOL)
print("Worker:", WORKER_NAME)
print()

run_pearl.remote()
