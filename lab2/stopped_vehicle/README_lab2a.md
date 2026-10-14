# Lab 2A: Stopped-Vehicle Emergency Braking

Lab 2A places a stationary vehicle ahead of the ego vehicle. The ego vehicle approaches it and applies emergency braking when the configured separation becomes small enough.

## Files

- `stopped_vehicle.py` — CARLA client, vehicle control, safety logic, and evaluation.
- `stopped_vehicle.json` — map, placement, timing, braking threshold, camera, and pass criteria.

## Run

```bash
cd ~/carla-simulator
source ~/carla-venv/bin/activate
mkdir -p outputs/lab2a

python3 lab2/stopped_vehicle/stopped_vehicle.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab2/stopped_vehicle/stopped_vehicle.json \
  --output-dir outputs/lab2a
```

## Decision logic

The script repeatedly measures the distance between the ego vehicle and the obstacle. Before the braking threshold, it applies throttle. At or below the threshold, it applies brake and records that the braking decision occurred. The decision should remain latched so later measurements do not accidentally resume throttle.

## Expected evidence

Depending on the current script configuration, the output may contain `result.json`, `telemetry.csv`, a preview image, RGB frames, and a video or video-ready frame sequence.

The scenario should pass only when braking occurs, no collision is detected, the minimum separation is safe, and the final speed is near zero.

## Configuration experiment

Change `brake_trigger_distance_m`, `initial_throttle`, `simulation_seconds`, or `pass_min_distance_m` one at a time. Explain how each change affects stopping distance and the PASS/FAIL result.
