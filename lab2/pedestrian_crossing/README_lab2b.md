# Lab 2B: Pedestrian-Crossing Emergency Braking

Lab 2B introduces a moving pedestrian and tests whether the ego vehicle recognizes a pedestrian entering its path, brakes, and avoids a collision.

## Files

- `pedestrian_crossing.py` — pedestrian placement, hazard detection, vehicle control, and evaluation.
- `pedestrian_crossing.json` — pedestrian position, speed, hazard corridor, timing, camera, and pass criteria.

## Run

```bash
cd ~/carla-simulator
source ~/carla-venv/bin/activate
mkdir -p outputs/lab2b

python3 lab2/pedestrian_crossing/pedestrian_crossing.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab2/pedestrian_crossing/pedestrian_crossing.json \
  --output-dir outputs/lab2b
```

## Decision logic

The script compares the pedestrian's location with the ego vehicle's path. A pedestrian is a hazard when it is sufficiently ahead of the ego vehicle and within the configured lateral corridor. When the condition is true, the vehicle applies emergency braking.

This is more precise than stopping whenever any pedestrian exists in the world. It teaches students to define a geometric safety condition using longitudinal and lateral distance.

## Expected evidence

- hazard detected;
- pedestrian movement across the path;
- braking action;
- no collision;
- safe final position and speed;
- result and telemetry files.

## Configuration experiment

Change `pedestrian_speed_mps`, `brake_trigger_longitudinal_m`, `hazard_lateral_half_width_m`, or the pedestrian start position. Predict the result before running the experiment, then compare the prediction with the telemetry and PASS/FAIL result.
