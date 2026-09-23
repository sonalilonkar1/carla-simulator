# Student Workflow

## Define the experiment

Document the map, map variant, ego vehicle, spawn location or index, other actors, sensors, control/AI method, and measurable pass/fail conditions.

## Use a configuration file

Keep scenario parameters in JSON instead of hard-coding them throughout Python. This makes experiments repeatable and supports comparisons.

## Submit through SLURM

The batch script should allocate a GPU, start CARLA on a unique port, wait for the server, run the Python client, write logs, and clean up the CARLA process.

## Connect through the Python API

```python
import carla

client = carla.Client("127.0.0.1", 2000)
client.set_timeout(30.0)
world = client.get_world()
print(world.get_map().name)
```

## Build incrementally

1. Connect to the server.
2. Load the map.
3. Spawn one vehicle.
4. Move the vehicle.
5. Add an RGB camera.
6. Add LiDAR or collision sensing.
7. Add pedestrians, traffic, or signals.
8. Define assertions and save results.

Every experiment should save its configuration, source code, SLURM output, telemetry, sensor frames, and structured result file.
