from beam import function, Image
import subprocess
import time

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
    print("SRBMINER V6 DIAGNOSTIC")
    print("=" * 60)

    print()
    print("[1] NVIDIA GPU")
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
    print("[2] Downloading SRBMiner 3.5.4")
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
        raise RuntimeError(
            "gagal download SRBMiner"
        )

    print("download selesai")

    print()
    print("[3] Extracting SRBMiner")
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
        raise RuntimeError(
            "gagal extract SRBMiner"
        )

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
            "binary SRBMiner-MULTI tidak ditemukan"
        )

    subprocess.run(
        ["chmod", "+x", miner],
        check=False,
    )

    print("binary:")
    print(miner)

    print()
    print("[4] SRBMiner VERSION")
    print("-" * 60)

    result = subprocess.run(
        [
            miner,
            "--version",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    version_output = (
        result.stdout + "\n" + result.stderr
    ).strip()

    if version_output:
        print(version_output)
    else:
        print(
            "SRBMiner tidak memberikan output dari --version"
        )

    print()
    print("[5] SRBMiner HELP")
    print("-" * 60)

    result = subprocess.run(
        [
            miner,
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    help_output = (
        result.stdout + "\n" + result.stderr
    ).strip()

    print(help_output[:12000])

    print()
    print("[6] SUPPORTED ALGORITHMS")
    print("-" * 60)

    result = subprocess.run(
        [
            miner,
            "--list-algorithms",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    algorithm_output = (
        result.stdout + "\n" + result.stderr
    ).strip()

    if algorithm_output:
        print(algorithm_output[:12000])
    else:
        print(
            "Tidak ada output dari --list-algorithms"
        )

    print()
    print("[7] PEARL-RELATED SEARCH")
    print("-" * 60)

    pearl_lines = []

    for line in algorithm_output.splitlines():

        lower = line.lower()

        if (
            "pearl" in lower
            or "prl" in lower
            or "hash" in lower
        ):
            pearl_lines.append(line)

    if pearl_lines:
        for line in pearl_lines:
            print(line)
    else:
        print(
            "Tidak ditemukan baris yang mengandung "
            "pearl / prl / hash."
        )

    print()
    print("[8] GPU DETECTION BY SRBMINER")
    print("-" * 60)

    gpu_test = subprocess.run(
        [
            miner,
            "--list-gpu-devices",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    gpu_output = (
        gpu_test.stdout + "\n" + gpu_test.stderr
    ).strip()

    if gpu_output:
        print(gpu_output[:12000])
    else:
        print(
            "SRBMiner tidak memberikan output "
            "dari --list-gpu-devices."
        )

    print()
    print("=" * 60)
    print("DIAGNOSTIC SELESAI")
    print("=" * 60)
    print()
    print(
        "Tidak ada proses mining yang dijalankan."
    )
    print(
        "Gunakan hasil diagnostic ini untuk "
        "menentukan parameter Pearl yang benar."
    )

    time.sleep(2)
