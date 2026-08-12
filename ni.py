from beam import function, Image
import subprocess
import time

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y curl ca-certificates dnsutils",
    ])
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
    print("=== GPU TEST ===")
    subprocess.run(["nvidia-smi"], check=False)

    cmd = r"""
echo "=== DNS TEST ==="
getent hosts github.com || true

echo "=== NSLOOKUP TEST ==="
nslookup github.com || true

echo "=== CURL TEST ==="
curl -v --connect-timeout 15 https://github.com/ -o /tmp/github.html

echo "=== CURL EXIT CODE ==="
echo $?

echo "=== RESULT ==="
ls -lh /tmp/github.html || true

echo "=== TEST FINISHED ==="
"""

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print("Process exited with:", result.returncode)


if __name__ == "__main__":
    run_script.remote()
