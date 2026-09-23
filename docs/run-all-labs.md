# Running Labs 1–4

This is the command sequence for the current tutorial. Run these commands from the repository root on the HPC login node. CARLA itself runs only on the GPU node allocated by SLURM.

## One-time preparation

```bash
cd ~/carla-simulator
mkdir -p /scratch/cmpe281-fa26/$USER/logs /scratch/cmpe281-fa26/$USER/output
```

Confirm that the shared CARLA image exists:

```bash
ls -lh /scratch/cmpe281-fa26/software/carla-0.9.16.sif
```

## Lab 1 — vehicle and RGB camera

```bash
sbatch lab1/run_carla_lab1.sbatch
```

## Lab 2A — stopped vehicle

```bash
sbatch lab2/stopped_vehicle/run_stopped_vehicle.sbatch
```

## Lab 2B — pedestrian crossing

```bash
sbatch lab2/pedestrian_crossing/run_pedestrian_crossing.sbatch
```

## Lab 2C — traffic signal

Run discovery first:

```bash
sbatch lab2/traffic_signal/discover_traffic_lights.sbatch
```

Then run the scenario:

```bash
sbatch lab2/traffic_signal/run_traffic_signal.sbatch
```

## Lab 3 — accident report

```bash
sbatch lab3/accident_report/run_accident_report.sbatch
```

## Lab 4 — BasicAgent navigation with RGB and LiDAR

The AI navigation environment requires the CARLA Python wheel and offline dependencies such as NumPy, Shapely, and NetworkX. The instructor must first make the wheels listed in `requirements-ai.txt` available in the shared software area. Confirm the dependencies are installed before submitting:

```bash
source /scratch/cmpe281-fa26/runtime/$USER/venv311/bin/activate
python -c 'import carla, numpy, shapely, networkx; print("AI dependencies ready")'
```

Then submit:

```bash
sbatch lab4/ai_navigation/run_ai_navigation.sbatch
```

## Monitor jobs

```bash
squeue -u "$USER"
```

Inspect the user-specific output directory after completion:

```bash
find /scratch/cmpe281-fa26/$USER/output -maxdepth 3 -type f | sort
```

Every lab should produce logs plus structured results. Do not judge success only from whether the Slurm job starts; inspect `result.json`, the error log, and the generated sensor evidence.
