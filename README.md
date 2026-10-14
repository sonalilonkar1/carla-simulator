# CARLA GPU Workstation Tutorial

This repository contains a CARLA 0.9.16 tutorial for GPU workstations. It teaches students how to start CARLA, connect to it with Python, run scenario-based experiments, collect evidence, and extend one scenario into a final project.

The examples use CARLA's built-in maps, including `Town03_Opt`. The repository is designed for a local GPU workstation and does not require SLURM or HPC job-submission scripts.

## Course materials

The demonstration videos, student instructions, and presentation are available in the shared Drive folder:

[CARLA demo videos, instructions, and presentation](https://drive.google.com/drive/folders/1T1vytaZXpTSqYCbUHWaLb6Lk970z5pxr?usp=drive_link)

The folder contains:

- Demonstration videos for the individual labs and combined demonstrations
- GPU workstation setup instructions
- Student tutorial presentation
- Additional presentation or recording materials, when available

## Repository structure

```text
carla-simulator/
├── README.md
├── requirements-ai.txt
├── .gitignore
│
├── docs/
│   ├── README.md
│   ├── sensors-and-video.md
│   └── lab2-stopped-vehicle.md
│
├── lab1/
│   ├── README.md
│   └── lab1_demo.py
│
├── lab2/
│   ├── stopped_vehicle/
│   │   ├── README.md
│   │   ├── stopped_vehicle.py
│   │   └── stopped_vehicle.json
│   ├── pedestrian_crossing/
│   │   ├── README.md
│   │   ├── pedestrian_crossing.py
│   │   └── pedestrian_crossing.json
│   └── traffic_signal/
│       ├── README.md
│       ├── traffic_signal.py
│       ├── traffic_signal.json
│       └── discover_traffic_lights.py
│
├── lab3/
│   └── accident_report/
│       ├── README.md
│       ├── accident_report.py
│       └── accident_report.json
│
├── lab4/
│   └── ai_navigation/
│       ├── README.md
│       ├── ai_navigation.py
│       └── ai_navigation.json
│
├── scripts/
│   ├── start_carla.sh
│   ├── generate_traffic.py
│   ├── follow_ego.py
│   ├── follow_traffic.py
│   └── birdseyeview.py
│
└── outputs/
    ├── lab1/
    ├── lab2a/
    ├── lab2b/
    ├── lab2c/
    ├── lab3/
    └── lab4/
```

The CARLA installation and Python virtual environment are kept outside this repository:

```text
~/CARLA_0.9.16/
~/carla-venv/
```

The `outputs/` directory is intentionally empty in Git. Scenario outputs can contain large videos, images, LiDAR files, CSV files, and point clouds, so they should be stored locally or uploaded separately to the shared Drive folder.

## Requirements

- Linux GPU workstation
- NVIDIA GPU and working NVIDIA driver
- CARLA 0.9.16
- Python 3.10, 3.11, or 3.12 matching the CARLA wheel
- Python virtual environment
- `carla` Python package from the CARLA distribution
- `shapely` for the AI-navigation lab
- CARLA navigation agents for Lab 4

## First-time setup

Start a terminal and clone the repository:

```bash
cd ~
git clone https://github.com/sonalilonkar1/carla-simulator.git
cd ~/carla-simulator
```

Activate the Python environment:

```bash
source ~/carla-venv/bin/activate
```

Set the CARLA paths for the current terminal:

```bash
export CARLA_ROOT="$HOME/CARLA_0.9.16"
export PYTHONPATH="$CARLA_ROOT/PythonAPI/carla:$CARLA_ROOT/PythonAPI/carla/agents:$PYTHONPATH"
```

If the environment does not already contain the required packages, install them inside the virtual environment:

```bash
python3 -m pip install shapely
python3 -m pip install -r requirements-ai.txt
```

Verify the installation:

```bash
python3 - <<'PY'
import carla

client = carla.Client("127.0.0.1", 2000)
client.set_timeout(10.0)
print("Client:", client.get_client_version())
print("Server:", client.get_server_version())
print("Map:", client.get_world().get_map().name)
PY
```

## Starting CARLA

Use the helper script if it has been configured for the workstation:

```bash
bash scripts/start_carla.sh
```

Alternatively, start CARLA directly:

```bash
cd ~/CARLA_0.9.16
./CarlaUE4.sh \
  -quality-level=Low \
  -windowed \
  -ResX=1280 \
  -ResY=720 \
  -nosound
```

Keep CARLA running in one terminal. Run Python clients from another terminal. CARLA normally listens on port `2000`.

## Running the labs

Create local output directories:

```bash
mkdir -p outputs/lab1 outputs/lab2a outputs/lab2b outputs/lab2c outputs/lab3 outputs/lab4
```

### Lab 1: Vehicle control and RGB camera

```bash
python3 lab1/lab1_demo.py \
  --host 127.0.0.1 \
  --port 2000 \
  --output-dir outputs/lab1
```

This lab creates an ego vehicle, applies direct `VehicleControl`, attaches an RGB camera, advances the simulation, and records basic telemetry.

### Lab 2A: Stopped-vehicle emergency braking

```bash
python3 lab2/stopped_vehicle/stopped_vehicle.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab2/stopped_vehicle/stopped_vehicle.json \
  --output-dir outputs/lab2a
```

The JSON file controls the obstacle distance, braking threshold, throttle, simulation duration, and pass criteria.

### Lab 2B: Pedestrian-crossing emergency braking

```bash
python3 lab2/pedestrian_crossing/pedestrian_crossing.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab2/pedestrian_crossing/pedestrian_crossing.json \
  --output-dir outputs/lab2b
```

The script evaluates whether a pedestrian enters the ego vehicle's hazard corridor and whether the vehicle stops safely.

### Lab 2C: Traffic-signal compliance

```bash
python3 lab2/traffic_signal/traffic_signal.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab2/traffic_signal/traffic_signal.json \
  --output-dir outputs/lab2c
```

The vehicle approaches a traffic signal, stops during red, waits, and proceeds after the signal becomes green.

### Lab 3: Collision detection and accident reporting

```bash
python3 lab3/accident_report/accident_report.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab3/accident_report/accident_report.json \
  --output-dir outputs/lab3
```

This lab attaches `sensor.other.collision`, records collision events, identifies the other actor, and writes an accident report.

### Lab 4: AI route navigation

```bash
python3 lab4/ai_navigation/ai_navigation.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab4/ai_navigation/ai_navigation.json \
  --output-dir outputs/lab4
```

Lab 4 uses CARLA's `BasicAgent` to calculate steering and throttle commands while collecting RGB camera and LiDAR evidence.

## Optional scripts in `scripts/`

These scripts are workstation utilities for live demonstrations. They are not replacements for the six lab scripts and should be treated as supporting tools.

### `start_carla.sh`

Starts the CARLA simulator with the workstation's preferred display, resolution, quality, and sound options.

```bash
bash scripts/start_carla.sh
```

If the script contains workstation-specific paths, update those paths before sharing it with students. It should not be used from a head node or a login node.

### `generate_traffic.py`

Creates additional traffic actors in the current CARLA world. Run it only after CARLA is running:

```bash
python3 scripts/generate_traffic.py --help
python3 scripts/generate_traffic.py
```

Use this utility when a demonstration needs background vehicles. For controlled safety labs, run the scenario without extra traffic first so the result is repeatable. Destroy generated actors before running another scenario if the script does not clean them up automatically.

### `follow_ego.py`

Moves the spectator camera to follow the vehicle identified as the ego vehicle. The scenario script must assign the agreed `role_name` before spawning the vehicle, for example:

```python
ego_bp.set_attribute("role_name", "hero")
ego = world.try_spawn_actor(ego_bp, transform)
```

Run:

```bash
python3 scripts/follow_ego.py --help
python3 scripts/follow_ego.py
```

Run it only while the scenario vehicle is alive. If it follows the wrong vehicle, destroy old actors and confirm that the scenario vehicle has `role_name=hero` before spawning.

### `follow_traffic.py`

Follows a selected background traffic vehicle for a live demonstration:

```bash
python3 scripts/follow_traffic.py --help
python3 scripts/follow_traffic.py
```

This is useful for demonstrating traffic behavior, but it is not required for the lab evaluation.

### `birdseyeview.py`

Moves the spectator above the map to provide a top-down view of the road network, vehicles, and scenario area:

```bash
python3 scripts/birdseyeview.py --help
python3 scripts/birdseyeview.py
```

Use the bird's-eye view for demonstrations and the follow-ego view for showing what the ego vehicle sees while driving. These utilities normally run in separate terminals and do not replace the scenario client.

## Recommended live-demo arrangement

Use the minimum number of terminals:

1. Terminal 1: start CARLA with `scripts/start_carla.sh`.
2. Terminal 2: run one scenario script.
3. Optional Terminal 3: run either `follow_ego.py` or `birdseyeview.py`.

Do not run multiple scenario scripts at the same time unless they were specifically designed to share the same world. Multiple clients can create competing vehicles, sensors, and cleanup problems.

## Outputs

Scenario outputs may include:

- `result.json` — PASS/FAIL and summary metrics
- `telemetry.csv` — speed, location, distance, and state per tick
- RGB camera images or video frames
- LiDAR point-cloud files
- Collision or accident reports
- Logs and diagnostic text

Inspect an output directory with:

```bash
find outputs/lab1 -maxdepth 2 -type f -print
cat outputs/lab1/result.json
```

The generated files are intentionally excluded from Git because videos and sensor data can be very large. Keep them locally or upload selected demonstrations to the shared Drive folder.

## Video recording

The labs can be run as live-rendering demonstrations without saving camera frames. If a video is required, use the workstation's screen recorder or save camera frames and convert them afterward. The playback frame rate must match the capture rate; for example, use 20 FPS for a camera with `sensor_tick=0.05`.

## Development workflow

1. Start CARLA and confirm the Python connection.
2. Run an existing lab without changing the code.
3. Read its JSON configuration and identify the controlled variables.
4. Change one configuration value at a time.
5. Run multiple trials and compare `result.json` and telemetry.
6. Modify the Python controller or add a sensor.
7. Define a measurable PASS/FAIL rule.
8. Document the experiment, limitations, and evidence in the project README.

Students should build on an existing lab pattern instead of creating an entire simulator from scratch. A strong final project includes a scenario, controller, sensor data, evaluation metrics, reproducible commands, and a short technical explanation.

## HPC note

This cleaned repository targets a dedicated GPU workstation. The current workflow does not use `sbatch`, SLURM, Apptainer, or HPC output paths. Those tools are needed only when running CARLA through a separate SLURM-managed cluster workflow.

## License and attribution

CARLA is an open-source simulator distributed under its own license. Students should review the CARLA license and the licenses of any external assets or Python packages used in their projects.
