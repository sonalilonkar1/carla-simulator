# CMPE 281 CARLA Lab 4 — AI-Based Navigation

This single SLURM job uses CARLA's `BasicAgent` navigation stack. The agent
receives a destination waypoint, plans a route, and produces vehicle controls.
The job records RGB camera frames, LiDAR point clouds, collision events, and
telemetry. It passes only if the goal is reached without collision and with
both RGB and LiDAR evidence.

The launcher copies CARLA's bundled `agents` package from the SIF into the
user's scratch runtime. No internet access or system installation is needed.

Outputs:

- `frames/`: RGB navigation video frames
- `lidar/`: point-cloud scans in PLY format
- `telemetry.csv`: route distance, speed, phase and collisions
- `result.json`: machine-readable navigation evaluation
- `preview.png`: representative RGB frame
