# CMPE 281 CARLA Lab 3 — Accident Detection and Reporting

This single SLURM job runs a controlled rear-end collision in `Town03_Opt`.
It detects the collision with CARLA's collision sensor, records camera frames
and per-tick telemetry, and writes both `result.json` and an evidence-oriented
`incident_report.json`.

The scenario is intentionally a ground-truth safety exercise. Students should
later extend it with camera/LiDAR perception, accident classification, richer
reports, or an AI response policy.

Outputs:

- `frames/`: RGB evidence before and after impact
- `preview.png`: representative frame
- `telemetry.csv`: simulation time, phase, distance, speed and collision count
- `result.json`: pass/fail summary
- `incident_report.json`: collision actor, location, impulse and speed details
