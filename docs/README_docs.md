# CARLA GPU Workstation Documentation

This documentation is for running CARLA 0.9.16 directly on a Linux GPU workstation. It does not use SLURM, `sbatch`, Apptainer, or HPC scratch paths.

## Start here

1. Read the root [`README.md`](../README.md) for workstation setup and the overall workflow.
2. Start CARLA using `scripts/start_carla.sh` or `CarlaUE4.sh`.
3. Verify the Python connection on port `2000`.
4. Run Lab 1 first.
5. Continue with Labs 2A, 2B, 2C, 3, and 4.
6. Read [`sensors-and-video.md`](sensors-and-video.md) when working with RGB, LiDAR, telemetry, or recordings.

## Documentation files

- [`sensors-and-video.md`](sensors-and-video.md) — sensors, evidence, and video guidance.
- [`lab2-stopped-vehicle.md`](lab2-stopped-vehicle.md) — emergency-braking concepts.
- The README inside each lab folder — lab-specific commands, configuration, and expected evidence.

## Repository layout

```text
lab1/                 vehicle control and RGB camera
lab2/                 emergency braking and traffic-signal scenarios
lab3/                 collision detection and incident reporting
lab4/                 BasicAgent route navigation with RGB/LiDAR
scripts/              optional live-demonstration utilities
docs/                 supporting documentation
outputs/              local generated results; not committed to Git
```

## GPU workstation rule

Start CARLA on the GPU workstation and run Python clients from another terminal. Confirm that `nvidia-smi` shows the NVIDIA GPU before starting the simulator. SLURM scripts are not part of this workstation workflow; they are only needed for a separate HPC cluster deployment.

## Course materials

Videos, student instructions, and the presentation are available in the [shared Drive folder](https://drive.google.com/drive/folders/1T1vytaZXpTSqYCbUHWaLb6Lk970z5pxr?usp=drive_link).
