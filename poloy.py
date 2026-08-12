from beam import function, Image
import subprocess

image = Image(
    base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    python_version="python3.10",
)


@function(
    name="t4x3-runner",
    image=image,
    gpu="RTX4090",
    cpu=4,
    memory="8Gi",
    timeout=10 * 60,
)
def run_script():
    print("=== GPU TEST STARTED ===", flush=True)

    result = subprocess.run(
        ["nvidia-smi"],
        capture_output=True,
        text=True,
    )

    print(result.stdout, flush=True)

    if result.returncode != 0:
        print(result.stderr, flush=True)
        raise RuntimeError("nvidia-smi failed")

    print("=== GPU TEST PASSED ===", flush=True)


if __name__ == "__main__":
    run_script.remote()
