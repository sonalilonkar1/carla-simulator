# Lab 1: Vehicle Control and RGB Camera

This introductory lab verifies the complete path from a SLURM GPU allocation to a CARLA Python client.

## Learning objectives

- request a GPU safely;
- connect to CARLA 0.9.16;
- inspect the current map;
- spawn and control a vehicle;
- attach an RGB camera;
- save a camera frame and measurable output.

## Run

Submit the batch script from the HPC login node:

```bash
cd /scratch/cmpe281-fa26
sbatch /path/to/lab1/run_carla_lab1.sbatch
```

Monitor it:

```bash
squeue -u "$USER"
```

Inspect the generated log and output directory after completion. The exact output path is printed by the job.

## Expected evidence

- successful CARLA server connection;
- vehicle model and actor ID;
- start/end positions and distance moved;
- RGB image, normally 800x600;
- empty error log;
- a clear pass/fail result.

## Extend the lab

Change one parameter at a time: vehicle blueprint, spawn-point index, camera resolution, map, or motion duration. Keep the original working version as a reference.
