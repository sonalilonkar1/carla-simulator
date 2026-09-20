#!/bin/bash

COURSE_ROOT=/scratch/cmpe281-fa26
SIF="$COURSE_ROOT/software/carla-0.9.16.sif"
RUNTIME="$COURSE_ROOT/runtime/$USER"
DEV_ROOT="$HOME/cmpe281-carla-dev"
PRIVATE_ROOT="$COURSE_ROOT/instructor/$USER"
OUTPUT="$PRIVATE_ROOT/output/traffic_signal/$SLURM_JOB_ID"
SERVER_LOG="$PRIVATE_ROOT/logs/carla-server-signal-$SLURM_JOB_ID.log"
SERVER_PID=""
CARLA_PORT=$((20000 + SLURM_JOB_ID % 20000))

if [[ -z "${SLURM_JOB_ID:-}" ]]; then echo "ERROR: Submit with sbatch" >&2; exit 2; fi
case "$(hostname -s)" in g17|coe-hpc1*) echo "ERROR: Refusing head node" >&2; exit 2;; esac
cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Stopping disposable CARLA process group $SERVER_PID"
    kill -KILL -- "-$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

mkdir -p "$RUNTIME/home" "$RUNTIME/vulkan" "$RUNTIME/wheels" "$OUTPUT" "$PRIVATE_ROOT/logs"
umask 0002
sed 's#/usr/lib64/libGLX_nvidia.so.0#libGLX_nvidia.so.0#' \
  /usr/share/vulkan/icd.d/nvidia_icd.x86_64.json > "$RUNTIME/vulkan/nvidia_icd.json"
WHEEL="$RUNTIME/wheels/carla-0.9.16-cp311-cp311-manylinux_2_31_x86_64.whl"
[[ -x "$RUNTIME/venv311/bin/python" ]] || python3.11 -m venv "$RUNTIME/venv311"
"$RUNTIME/venv311/bin/python" -m pip install --no-index --quiet "$WHEEL"
export APPTAINERENV_CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?No GPU assigned}"
export APPTAINERENV_VK_ICD_FILENAMES=/course-runtime/vulkan/nvidia_icd.json
echo "Job: $SLURM_JOB_ID"; echo "Node: $(hostname)"; echo "CARLA port: $CARLA_PORT"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader -i "$CUDA_VISIBLE_DEVICES"

setsid apptainer exec --nv --cleanenv --bind "$RUNTIME:/course-runtime" \
  --home "$RUNTIME/home" --pwd /workspace "$SIF" bash CarlaUE4.sh \
  -RenderOffScreen -nosound -quality-level=Low -carla-port="$CARLA_PORT" \
  -stdout -FullStdOutLogOutput > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
echo "Waiting for CARLA port $CARLA_PORT..."
ready=0
for attempt in $(seq 1 90); do
  kill -0 "$SERVER_PID" 2>/dev/null || { tail -n 80 "$SERVER_LOG" >&2; exit 4; }
  if "$RUNTIME/venv311/bin/python" -c \
    "import socket; s=socket.create_connection(('127.0.0.1',$CARLA_PORT),1); s.close()" \
    >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
[[ "$ready" -eq 1 ]] || { echo "ERROR: CARLA startup timeout" >&2; exit 5; }

if [[ "$MODE" == discovery ]]; then
  "$RUNTIME/venv311/bin/python" "$DEV_ROOT/scripts/discover_traffic_lights.py" \
    --port "$CARLA_PORT" --output "$OUTPUT/traffic-light-candidates.json"
  echo "TRAFFIC-LIGHT DISCOVERY: PASS"
else
  "$RUNTIME/venv311/bin/python" "$DEV_ROOT/scripts/traffic_signal.py" \
    --port "$CARLA_PORT" --config "$DEV_ROOT/configs/traffic_signal.json" --output-dir "$OUTPUT"
  if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -y -loglevel error -framerate 20 -i "$OUTPUT/frames/frame-%06d.png" \
      -c:v libx264 -pix_fmt yuv420p "$OUTPUT/scenario.mp4"
  else
    echo "NOTE: ffmpeg unavailable; create video from PNG frames on Mac."
  fi
  echo "SLURM LAB 2C JOB: PASS"
fi
echo "Output: $OUTPUT"
