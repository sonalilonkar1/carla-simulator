# CARLA Installation and Environment

The course uses CARLA 0.9.16 in an Apptainer image. Students do not need to compile Unreal Engine or install CARLA system-wide.

```bash
export SHARED=/scratch/cmpe281-fa26
export CARLA_SIF="$SHARED/software/carla-0.9.16.sif"
export CARLA_RUNTIME="$SHARED/runtime/$USER"
mkdir -p "$CARLA_RUNTIME"/home "$CARLA_RUNTIME"/logs "$CARLA_RUNTIME"/vulkan
```

The SIF image is shared and read-only. Runtime configuration, logs, Python environments, and outputs belong in writable storage.

## Verify the image

```bash
apptainer --version
ls -lh "$CARLA_SIF"
apptainer inspect "$CARLA_SIF"
```

Only inside a GPU allocation, verify GPU access inside the image:

```bash
export APPTAINERENV_CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES"
apptainer exec --nv --cleanenv "$CARLA_SIF" nvidia-smi
```

`--nv` exposes the allocated NVIDIA driver and GPU libraries inside the container.

## Python API

The wheel must match the Python version. The course examples use Python 3.11:

```bash
python3.11 -m venv "$CARLA_RUNTIME/venv311"
source "$CARLA_RUNTIME/venv311/bin/activate"
python -m pip install --no-index /path/to/carla-0.9.16-cp311-*.whl
python -c 'import carla; print("CARLA Python API import succeeded")'
```

AI navigation additionally requires NumPy, Shapely, and NetworkX. The versions are listed in [`requirements-ai.txt`](../requirements-ai.txt). Because compute nodes may not have Internet access, the instructor or administrator must stage matching wheels in the approved shared software directory. Install them with `pip --no-index --find-links ...`; do not use `sudo`.

## Town03

Use `Town03_Opt` for course scenarios. When needed, load layers sequentially: Ground, Buildings, Walls, Props, StreetLights, Decals, ParkedVehicles, Foliage, and Particles. Staged loading reduces Unreal render-thread failures.
