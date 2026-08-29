from beam import function, Image
import subprocess

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

srbminer_url = (
    "https://github.com/doktor83/SRBMiner-Multi/releases/"
    "download/3.5.4/"
    "SRBMiner-Multi-3-5-4-Linux.tar.gz"
)


def run_test(command, name):
    print()
    print("=" * 60)
    print(name)
    print("=" * 60)
    print("COMMAND:")
    print(" ".join(command))
    print("-" * 60)

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    print("EXIT CODE:", result.returncode)

    print()
    print("STDOUT:")
    print("-" * 60)

    if result.stdout.strip():
        print(result.stdout[:12000])
    else:
        print("(empty)")

    print()
    print("STDERR:")
    print("-" * 60)

    if result.stderr.strip():
        print(result.stderr[:12000])
    else:
        print("(empty)")

    return result


@function(
    name="hama",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=30 * 60,
)
def run_pearl():

    workdir = "/workspace/srbminer"
    archive = f"{workdir}/srbminer.tar.gz"

    print("=" * 60)
    print("SRBMINER V7 DIAGNOSTIC")
    print("=" * 60)

    print()
    print("[1] GPU")
    print("-" * 60)

    subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total",
            "--format=csv,noheader",
        ],
        check=False,
    )

    print()
    print("[2] DOWNLOAD")
    print("-" * 60)

    subprocess.run(
        ["mkdir", "-p", workdir],
        check=True,
    )

    result = subprocess.run(
        [
            "wget",
            "-q",
            "--tries=3",
            "--timeout=60",
            "-O",
            archive,
            srbminer_url,
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError("gagal download SRBMiner")

    print("download selesai")

    print()
    print("[3] EXTRACT")
    print("-" * 60)

    result = subprocess.run(
        [
            "tar",
            "-xzf",
            archive,
            "-C",
            workdir,
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError("gagal extract SRBMiner")

    result = subprocess.run(
        [
            "bash",
            "-lc",
            f'find "{workdir}" -type f -name "SRBMiner-MULTI" | head -n 1',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    miner = result.stdout.strip()

    if not miner:
        raise RuntimeError(
            "SRBMiner-MULTI tidak ditemukan"
        )

    subprocess.run(
        ["chmod", "+x", miner],
        check=False,
    )

    print("MINER:")
    print(miner)

    run_test(
        [miner],
        "TEST 1 - SRBMINER TANPA ARGUMEN",
    )

    run_test(
        [miner, "--help"],
        "TEST 2 - SRBMINER HELP",
    )

    run_test(
        [miner, "-h"],
        "TEST 3 - SHORT HELP",
    )

    run_test(
        [miner, "--algorithm", "pearlhash"],
        "TEST 4 - PEARLHASH SAJA",
    )

    run_test(
        [
            miner,
            "--disable-cpu",
            "--algorithm",
            "pearlhash",
        ],
        "TEST 5 - PEARLHASH + GPU",
    )

    print()
    print("=" * 60)
    print("V7 DIAGNOSTIC SELESAI")
    print("=" * 60)
    print()
    print("Mining belum dijalankan.")
