#!/usr/bin/env bash
set -euo pipefail

CARLA_ROOT="${CARLA_ROOT:-$HOME/CARLA_0.9.16}"
CARLA_BIN="$CARLA_ROOT/CarlaUE4.sh"

if [[ ! -x "$CARLA_BIN" ]]; then
    echo "CARLA executable not found:"
    echo "$CARLA_BIN"
    echo "Set CARLA_ROOT if necessary."
    exit 1
fi

if ss -ltn 2>/dev/null | grep -q ':2000'; then
    echo "CARLA is already running on port 2000."
    exit 0
fi

echo "Starting CARLA 0.9.16..."
echo "The Python scenario will load Town03_Opt."

exec "$CARLA_BIN" \
    -quality-level=Low \
    -windowed \
    -ResX=1280 \
    -ResY=720 \
    -nosound
