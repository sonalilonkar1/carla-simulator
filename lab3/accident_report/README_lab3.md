# Lab 3: Accident Detection and Reporting

Lab 3 demonstrates event-driven sensing. A collision sensor is attached to the ego vehicle, and a callback records the collision frame, other actor, location, and impulse information.

## Run

```bash
cd ~/carla-simulator
source ~/carla-venv/bin/activate
mkdir -p outputs/lab3

python3 lab3/accident_report/accident_report.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab3/accident_report/accident_report.json \
  --output-dir outputs/lab3
```

## Core API pattern

The script finds `sensor.other.collision`, spawns it attached to the ego vehicle, and registers a callback with `sensor.listen(...)`. CARLA invokes the callback when contact occurs. The main simulation loop continues collecting state while the callback appends structured event data.

## Expected evidence

Depending on the current script configuration, the output may include:

- `result.json` — PASS/FAIL summary;
- `incident_report.json` — collision actor, location, frame, impulse, and speed;
- `telemetry.csv` — per-tick state;
- preview image or RGB evidence;
- saved frames or video-ready output.

## Project extensions

Students can add RGB or LiDAR-based evidence, classify collision severity, calculate impact thresholds, or implement a response policy. The important distinction is between the sensor event, the stored evidence, and the final interpretation.
