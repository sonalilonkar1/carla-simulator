# Lab 2C: Traffic-Signal Compliance

Lab 2C implements a small state machine for approaching a traffic signal, stopping at red, waiting without crossing the stop line, and proceeding when the signal becomes green.

## Files

- `discover_traffic_lights.py` — optional utility for inspecting traffic-light candidates.
- `traffic_signal.py` — traffic-signal state machine and vehicle control.
- `traffic_signal.json` — map, signal choice, timing, stop-line tolerance, and pass criteria.

## Run

```bash
cd ~/carla-simulator
source ~/carla-venv/bin/activate
mkdir -p outputs/lab2c

python3 lab2/traffic_signal/traffic_signal.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab2/traffic_signal/traffic_signal.json \
  --output-dir outputs/lab2c
```

Inspect the discovery utility before using it:

```bash
python3 lab2/traffic_signal/discover_traffic_lights.py --help
```

## State machine

The scenario normally moves through these states:

1. `APPROACH_RED` — drive toward the selected stop line.
2. `STOP_RED` — brake and hold while the signal is red.
3. `PROCEED_GREEN` — resume only after the signal turns green.

The evaluation checks that the vehicle stopped at red, did not cross the line while red, proceeded after green, and avoided collisions.

## GPU workstation note

This version runs directly against the CARLA server already running on the workstation. It does not use discovery or scenario `.sbatch` files. If a traffic signal is not found, inspect the current map and configuration rather than assuming every CARLA map has the same signal layout.
