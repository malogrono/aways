from beam import function, Image
import subprocess

image = Image(
    base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
)

@function(
    name="gpu-test-4090",
    image=image,
    gpu="RTX4090",
    cpu=2,
    memory="4Gi",
    timeout=10 * 60,
)
def test_gpu():
    result = subprocess.run(
        ["nvidia-smi"],
        capture_output=True,
        text=True,
        check=False,
    )

    print(result.stdout)
    print("exit code:", result.returncode)
