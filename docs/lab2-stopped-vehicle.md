# CMPE 281 — Lab 2A: Stopped-Vehicle Emergency Braking

This instructor-only package runs a deterministic CARLA 0.9.16 scenario on an
SJSU HPC GPU compute node. An ego Tesla approaches a stationary Audi, brakes at
a configured distance, records a chase-camera sequence, and reports measurable
pass/fail results.

## Files

- `lab2/stopped_vehicle/stopped_vehicle.py`: CARLA client and scenario logic
- `lab2/stopped_vehicle/stopped_vehicle.json`: map, timing, camera, and pass thresholds
- `lab2/stopped_vehicle/run_stopped_vehicle.sbatch`: GPU allocation and CARLA server lifecycle

## Expected results

The output directory contains:

- `result.json`: pass/fail result and safety metrics
- `telemetry.csv`: distance, speed, and action at every simulation tick
- `preview.png`: first camera frame
- `frames/`: continuous 800x600 RGB sequence at 20 FPS
- `scenario.mp4`: generated when `ffmpeg` is available on the compute node

The scenario passes only when braking occurs, no collision is recorded, the
minimum separation remains at least 2 meters, the final speed is at most 2
km/h, and camera frames are produced.

## Safety

Submit the SLURM file from `g17`. Never execute CARLA or this scenario directly
on `g17` or `coe-hpc1`; the batch script also refuses to run there.
