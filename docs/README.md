# CMPE 281 CARLA Documentation

Student entry point for CARLA 0.9.16 on the SJSU COE HPC cluster.

## Start here

1. Read [HPC setup](hpc-setup.md).
2. Read [CARLA installation](carla-installation.md).
3. Run the [Lab 1 example](../lab1/README.md).
4. Read [Student workflow](student-workflow.md).
5. Use the [CLI reference](cli-command-reference.md) when troubleshooting.

## Guides

- [HPC setup](hpc-setup.md) — SSH, storage, SLURM, and safety rules.
- [CARLA installation](carla-installation.md) — Apptainer image and Python API.
- [Student workflow](student-workflow.md) — scenario to reproducible results.
- [Sensors and video](sensors-and-video.md) — RGB, LiDAR, telemetry, and MP4.
- [CLI reference](cli-command-reference.md) — commands used in the tutorial.
- [Run all labs](run-all-labs.md) — submission commands for Labs 1–4.
- [Job execution command sequence](CARLA-Job-Commands.pdf) — Job execution commands for Lab 3 from class demo.

## Repository layout

```text
lab1/                 introductory vehicle and camera example
lab2/                 emergency braking and traffic-signal scenarios
lab3/                 collision detection and incident reporting
lab4/                 BasicAgent route navigation with RGB/LiDAR
docs/                 student documentation
```

All CARLA and GPU workloads must be submitted through SLURM. Never run CARLA directly on `g17` or another login/head node.
