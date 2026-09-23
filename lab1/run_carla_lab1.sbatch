#!/bin/bash
#SBATCH --job-name=carla-lab1
#SBATCH --partition=gpuqs
#SBATCH --exclude=cs002
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/cmpe281-fa26/%u/logs/lab1-%j.out
#SBATCH --error=/scratch/cmpe281-fa26/%u/logs/lab1-%j.err

set -euo pipefail

COURSE_ROOT=/scratch/cmpe281-fa26
SIF="$COURSE_ROOT/software/carla-0.9.16.sif"
RUNTIME="$COURSE_ROOT/runtime/$USER"
REPO_ROOT="${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is not set}"
USER_ROOT="$COURSE_ROOT/$USER"
LOG_DIR="$USER_ROOT/logs"

SCRIPT="$REPO_ROOT/lab1/lab1_demo.py"
OUTPUT="$USER_ROOT/output/lab1/$SLURM_JOB_ID"
SERVER_LOG="$LOG_DIR/carla-server-$SLURM_JOB_ID.log"
SERVER_PID=""

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
  echo "ERROR: Submit this file with sbatch; never run CARLA on a head node." >&2
  exit 2
fi

case "$(hostname -s)" in
  g17|coe-hpc1*)
    echo "ERROR: Refusing to run CARLA on head node $(hostname)." >&2
    exit 2
    ;;
esac

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Stopping disposable CARLA server process group $SERVER_PID"
    # CARLA 0.9.16/UE4 segfaults in its exit handler with SIGTERM and SIGINT
    # on this headless A100 environment. All actors and outputs are already
    # cleaned up, so terminate the isolated server process group directly.
    kill -KILL -- "-$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

mkdir -p \
  "$RUNTIME/home" \
  "$RUNTIME/vulkan" \
  "$RUNTIME/wheels" \
  "$OUTPUT" \
  "$LOG_DIR"
umask 0002

if [[ ! -r "$SIF" ]]; then
  echo "ERROR: CARLA image is missing or unreadable: $SIF" >&2
  exit 3
fi

sed 's#/usr/lib64/libGLX_nvidia.so.0#libGLX_nvidia.so.0#' \
  /usr/share/vulkan/icd.d/nvidia_icd.x86_64.json \
  > "$RUNTIME/vulkan/nvidia_icd.json"

WHEEL="$RUNTIME/wheels/carla-0.9.16-cp311-cp311-manylinux_2_31_x86_64.whl"
if [[ ! -f "$WHEEL" ]]; then
  apptainer exec --cleanenv --bind "$RUNTIME:/course-runtime" "$SIF" \
    cp /workspace/PythonAPI/carla/dist/carla-0.9.16-cp311-cp311-manylinux_2_31_x86_64.whl \
    /course-runtime/wheels/
fi

if [[ ! -x "$RUNTIME/venv311/bin/python" ]]; then
  python3.11 -m venv "$RUNTIME/venv311"
fi
"$RUNTIME/venv311/bin/python" -m pip install --no-index --quiet "$WHEEL"

export APPTAINERENV_CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?No GPU assigned by SLURM}"
export APPTAINERENV_VK_ICD_FILENAMES=/course-runtime/vulkan/nvidia_icd.json

echo "Job: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Assigned GPU: $CUDA_VISIBLE_DEVICES"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader -i "$CUDA_VISIBLE_DEVICES"

setsid apptainer exec \
  --nv \
  --cleanenv \
  --bind "$RUNTIME:/course-runtime" \
  --home "$RUNTIME/home" \
  --pwd /workspace \
  "$SIF" \
  bash CarlaUE4.sh \
    -RenderOffScreen \
    -nosound \
    -quality-level=Low \
    -carla-port=2000 \
    -stdout \
    -FullStdOutLogOutput \
  > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
echo "CARLA server process group: $SERVER_PID"

echo "Waiting for CARLA port 2000..."
ready=0
for attempt in $(seq 1 90); do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "ERROR: CARLA exited during startup. Last server log lines:" >&2
    tail -n 80 "$SERVER_LOG" >&2
    exit 4
  fi
  if "$RUNTIME/venv311/bin/python" -c \
    'import socket; s=socket.create_connection(("127.0.0.1",2000),1); s.close()' \
    >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done

if [[ "$ready" -ne 1 ]]; then
  echo "ERROR: CARLA did not open port 2000 within 90 seconds." >&2
  tail -n 80 "$SERVER_LOG" >&2
  exit 5
fi

echo "CARLA is ready; running Lab 1 scenario."
"$RUNTIME/venv311/bin/python" "$SCRIPT" \
  --host 127.0.0.1 \
  --port 2000 \
  --output-dir "$OUTPUT"

file "$OUTPUT/rgb-camera.png"
echo "Captured sequence:"
find "$OUTPUT" -maxdepth 1 -type f -name 'rgb-[0-9][0-9]-frame-*.png' -print | sort
echo "Batch output: $OUTPUT"
echo "SLURM LAB 1 JOB: PASS"
