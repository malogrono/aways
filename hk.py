from beam import function, Image
import subprocess
import os
import time
import urllib.request

# ============================================================
# IMAGE
# ============================================================

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y wget ca-certificates xz-utils tar gzip python3",
    ])
)


# ============================================================
# CONFIG
# ============================================================

BZ_VERSION = "25.0.0b9"

# GitHub Release langsung
BZ_URL = (
    "https://github.com/bzminer/bzminer/releases/download/"
    f"v{BZ_VERSION}/bzminer_v{BZ_VERSION}_linux.tar.gz"
)

POOL = "stratum+tcp://prl.kryptex.network:7048"

WALLET = (
    "prl1pg28ldvmyg8wkudfm3naexd0l3sun7xmz5hl8vrpdmazpzcwnf5vs6ftdcs"
)

WORKER = "beam-4090"


# ============================================================
# HELPER
# ============================================================

def run_cmd(cmd, timeout=None):
    print("COMMAND:")
    print(cmd)
    print("-" * 60)

    p = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )

    if p.stdout:
        print(p.stdout)

    print("EXIT CODE:", p.returncode)
    print("-" * 60)

    return p.returncode, p.stdout


# ============================================================
# MAIN
# ============================================================

@function(
    name="pearl-bzminer-v12",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60 * 60,
)
def run_pearl():

    print("=" * 60)
    print("PEARL MINING - BZMINER V12")
    print("=" * 60)

    # --------------------------------------------------------
    # GPU CHECK
    # --------------------------------------------------------

    print()
    print("checking gpu...")
    print("=" * 60)

    rc, gpu_output = run_cmd(
        "nvidia-smi",
        timeout=30,
    )

    if rc != 0:
        raise RuntimeError("NVIDIA GPU tidak terdeteksi.")

    # --------------------------------------------------------
    # WORKSPACE
    # --------------------------------------------------------

    workspace = "/workspace/bzminer"
    archive = f"/workspace/bzminer_v{BZ_VERSION}_linux.tar.gz"
    extract_dir = f"/workspace/bzminer_v{BZ_VERSION}_linux"

    os.makedirs(workspace, exist_ok=True)

    # --------------------------------------------------------
    # CLEAN OLD FILE
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CLEANUP")
    print("=" * 60)

    subprocess.run(
        f"rm -f '{archive}'",
        shell=True,
        check=False,
    )

    subprocess.run(
        f"rm -rf '{extract_dir}'",
        shell=True,
        check=False,
    )

    # --------------------------------------------------------
    # DOWNLOAD FROM GITHUB
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("DOWNLOAD BZMINER")
    print("=" * 60)

    print("version:")
    print(BZ_VERSION)

    print()
    print("source:")
    print(BZ_URL)

    print()

    download_cmd = (
        f"wget "
        f"--server-response "
        f"--progress=dot:giga "
        f"--tries=1 "
        f"--timeout=60 "
        f"-O '{archive}' "
        f"'{BZ_URL}'"
    )

    rc = subprocess.run(
        download_cmd,
        shell=True,
        check=False,
    ).returncode

    if rc != 0:
        print()
        print("DOWNLOAD GAGAL")
        print("exit code:", rc)
        print()
        print("BzMiner tidak di-download dari bzminer.com.")
        print("URL yang digunakan adalah GitHub Release.")
        raise RuntimeError(
            "Gagal download BzMiner dari GitHub Release."
        )

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CHECK DOWNLOADED FILE")
    print("=" * 60)

    if not os.path.exists(archive):
        raise RuntimeError(
            "File BzMiner tidak ditemukan setelah download."
        )

    size = os.path.getsize(archive)

    print("archive:")
    print(archive)

    print()
    print("size:")
    print(size, "bytes")

    if size < 1000000:
        print()
        print("Isi file terlalu kecil.")
        print("Kemungkinan yang didownload bukan archive BzMiner.")

        run_cmd(
            f"file '{archive}'",
            timeout=30,
        )

        raise RuntimeError(
            "Archive BzMiner tidak valid."
        )

    # --------------------------------------------------------
    # VERIFY TAR
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("VERIFY ARCHIVE")
    print("=" * 60)

    rc, _ = run_cmd(
        f"tar -tzf '{archive}' >/dev/null",
        timeout=60,
    )

    if rc != 0:
        raise RuntimeError(
            "Archive BzMiner rusak atau bukan tar.gz."
        )

    print("archive valid.")

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("EXTRACTING")
    print("=" * 60)

    rc, _ = run_cmd(
        f"tar -xzf '{archive}' -C /workspace",
        timeout=120,
    )

    if rc != 0:
        raise RuntimeError(
            "Gagal extract BzMiner."
        )

    # --------------------------------------------------------
    # FIND BINARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SEARCH BZMINER BINARY")
    print("=" * 60)

    find_cmd = (
        "find /workspace "
        "-type f "
        "-name bzminer "
        "-perm -111 "
        "| head -1"
    )

    result = subprocess.run(
        find_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    miner = result.stdout.strip()

    print("miner:")
    print(miner)

    if not miner:
        raise RuntimeError(
            "Binary bzminer tidak ditemukan setelah extract."
        )

    os.chmod(miner, 0o755)

    # --------------------------------------------------------
    # VERSION
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("BZMINER VERSION")
    print("=" * 60)

    rc, version_output = run_cmd(
        f"'{miner}' --version",
        timeout=30,
    )

    # Jangan langsung gagal kalau --version punya perilaku berbeda.
    if not version_output.strip():
        print("Tidak ada output version.")

    # --------------------------------------------------------
    # PEARL CHECK
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CHECK PEARL SUPPORT")
    print("=" * 60)

    rc, help_output = run_cmd(
        f"'{miner}' --help",
        timeout=30,
    )

    combined_help = (help_output or "").lower()

    if "pearl" not in combined_help:
        print()
        print("PERINGATAN:")
        print("String 'pearl' tidak terlihat pada --help.")
        print("Tetapi kita tetap lanjutkan test algoritma pearl.")
    else:
        print()
        print("PEARL TERDETEKSI PADA HELP.")

    # --------------------------------------------------------
    # GPU TEST BY BZMINER
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("BZMINER GPU TEST")
    print("=" * 60)

    test_cmd = (
        f"'{miner}' "
        f"-a pearl "
        f"--nvidia 1 "
        f"--amd 0 "
        f"--intel 0 "
        f"--igpu 0 "
        f"--cpu 0 "
        f"--cpu_threads 0 "
        f"--nc 1"
    )

    print("Melakukan test singkat GPU...")
    print()

    test_process = subprocess.Popen(
        test_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    start = time.time()

    gpu_lines = []

    while time.time() - start < 15:

        line = test_process.stdout.readline()

        if not line:
            if test_process.poll() is not None:
                break
            time.sleep(0.1)
            continue

        line = line.rstrip()

        print("[bzminer-test]", line)

        gpu_lines.append(line)

    # Stop test process
    if test_process.poll() is None:
        test_process.terminate()

        try:
            test_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            test_process.kill()

    test_text = "\n".join(gpu_lines).lower()

    print()
    print("=" * 60)
    print("GPU TEST SELESAI")
    print("=" * 60)

    if "4090" in test_text:
        print("RTX 4090 TERDETEKSI OLEH BZMINER.")
    else:
        print(
            "RTX 4090 belum terlihat jelas pada output test."
        )

    # --------------------------------------------------------
    # MINING CONFIG
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("MINING CONFIGURATION")
    print("=" * 60)

    print("GPU       : RTX 4090")
    print("Miner     : BzMiner")
    print("Version   :", BZ_VERSION)
    print("Algorithm : pearl")
    print("Pool      :", POOL)
    print("Worker    :", WORKER)
    print("Wallet    : configured")

    print("=" * 60)

    # --------------------------------------------------------
    # FINAL MINING COMMAND
    # --------------------------------------------------------

    command = (
        f"'{miner}' "
        f"-a pearl "
        f"-p '{POOL}' "
        f"-w '{WALLET}' "
        f"--worker '{WORKER}' "
        f"--nvidia 1 "
        f"--amd 0 "
        f"--intel 0 "
        f"--igpu 0 "
        f"--cpu 0 "
        f"--cpu_threads 0 "
        f"--nc 1 "
        f"--pearl_opt auto"
    )

    print()
    print("=" * 60)
    print("STARTING PEARL MINER")
    print("=" * 60)

    print("command:")
    print(command)

    print()
    print("=" * 60)
    print("MINER OUTPUT")
    print("=" * 60)

    # --------------------------------------------------------
    # START REAL MINER
    # --------------------------------------------------------

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    start_time = time.time()

    connected = False
    hashing = False
    share_found = False

    try:

        while True:

            line = process.stdout.readline()

            if line:
                line = line.rstrip()

                print("[bzminer]", line)

                low = line.lower()

                # Connection detection
                if any(x in low for x in [
                    "connected",
                    "connection established",
                    "subscribed",
                    "authorized",
                    "login successful",
                ]):
                    connected = True

                # Hashing detection
                if any(x in low for x in [
                    "hashrate",
                    "hash rate",
                    "h/s",
                    "kh/s",
                    "mh/s",
                    "gh/s",
                    "hashing",
                    "gpu hashrate",
                ]):
                    hashing = True

                # Share detection
                if any(x in low for x in [
                    "share accepted",
                    "accepted",
                    "share found",
                    "accepted share",
                    "yay",
                ]):
                    share_found = True

            else:

                if process.poll() is not None:
                    break

                time.sleep(0.1)

            # Status after 30 seconds
            elapsed = time.time() - start_time

            if int(elapsed) == 30:

                print()
                print("=" * 60)
                print("STATUS 30 DETIK")
                print("=" * 60)

                print(
                    "Pool connected :",
                    "YES" if connected else "BELUM TERDETEKSI"
                )

                print(
                    "Hashing        :",
                    "YES" if hashing else "BELUM TERDETEKSI"
                )

                print(
                    "Share          :",
                    "YES" if share_found else "BELUM ADA"
                )

                print("=" * 60)

    except KeyboardInterrupt:

        print()
        print("Keyboard interrupt.")

    finally:

        if process.poll() is None:
            print()
            print("Stopping BzMiner...")
            process.terminate()

            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    exit_code = process.returncode

    print()
    print("=" * 60)
    print("FINAL STATUS")
    print("=" * 60)

    print("Pool connected :", connected)
    print("Hashing        :", hashing)
    print("Share detected :", share_found)
    print("Exit code      :", exit_code)

    print("=" * 60)

    if not connected:
        print(
            "BELUM BISA MEMASTIKAN POOL TERHUBUNG."
        )

    if not hashing:
        print(
            "BELUM BISA MEMASTIKAN HASHING."
        )

    if not share_found:
        print(
            "BELUM ADA SHARE TERDETEKSI."
        )

    print()
    print("=" * 60)
    print("PEARL MINING V12 SELESAI")
    print("=" * 60)
