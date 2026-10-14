# Lab 1: Vehicle Control and RGB Camera

Lab 1 is the smallest complete CARLA experiment. It verifies the GPU workstation, Python environment, CARLA connection, actor spawning, direct vehicle control, RGB sensing, simulation ticks, and evidence output.

## Learning objectives

- connect to CARLA 0.9.16 on `127.0.0.1:2000`;
- select a vehicle blueprint and spawn point;
- apply `carla.VehicleControl`;
- attach an RGB camera to the ego vehicle;
- advance the world with `world.tick()`;
- record basic telemetry and determine whether the run completed successfully.

## Run

Start CARLA in Terminal 1, then use Terminal 2:

```bash
cd ~/carla-simulator
source ~/carla-venv/bin/activate
export CARLA_ROOT="$HOME/CARLA_0.9.16"
export PYTHONPATH="$CARLA_ROOT/PythonAPI/carla:$CARLA_ROOT/PythonAPI/carla/agents:$PYTHONPATH"

mkdir -p outputs/lab1

python3 lab1/lab1_demo.py \
  --host 127.0.0.1 \
  --port 2000 \
  --output-dir outputs/lab1
```

Use `python3 lab1/lab1_demo.py --help` to see the available duration, frame-count, and output options.

## Expected evidence

- successful client/server connection;
- selected map and vehicle model;
- vehicle actor and camera actor;
- start and end positions;
- distance moved;
- RGB image or camera evidence, depending on the selected options;
- telemetry or result output;
- clean actor destruction at the end of the run.

## Code concepts

The script follows the common CARLA pattern: create a `Client`, obtain the `world`, choose a blueprint, spawn the vehicle, attach the camera, apply control, call `world.tick()`, and destroy actors in cleanup code. A direct-control command normally contains throttle, steering, and braking values.

## Extend the lab

Change one value at a time: vehicle blueprint, spawn-point index, camera resolution, map, throttle, steering, or drive duration. Keep the original working version so that changes can be compared.
