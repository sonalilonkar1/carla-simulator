#!/usr/bin/env bash
set -euo pipefail

CARLA_ROOT="${CARLA_ROOT:-$HOME/CARLA_0.9.16}"
PYTHON="${PYTHON:-python3}"
HOST="${CARLA_HOST:-127.0.0.1}"
PORT="${CARLA_PORT:-2000}"
TM_PORT="${CARLA_TM_PORT:-8000}"

TRAFFIC_SCRIPT="$CARLA_ROOT/PythonAPI/examples/generate_traffic.py"

if [[ ! -f "$TRAFFIC_SCRIPT" ]]; then
    echo "Traffic script not found:"
    echo "$TRAFFIC_SCRIPT"
    exit 1
fi

echo "Starting background traffic on Town03_Opt..."
echo "Vehicles: ${VEHICLES:-25}"
echo "Walkers: ${WALKERS:-40}"
echo "Press Ctrl+C to stop traffic."

exec "$PYTHON" "$TRAFFIC_SCRIPT" \
    --host "$HOST" \
    --port "$PORT" \
    --tm-port "$TM_PORT" \
    --number-of-vehicles "${VEHICLES:-25}" \
    --number-of-walkers "${WALKERS:-40}" \
    --safe \
    --asynch
