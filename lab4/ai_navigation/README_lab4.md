# Lab 4: AI-Based Route Navigation

Lab 4 uses CARLA's bundled `BasicAgent` navigation package. The agent receives a destination and produces vehicle-control commands while the scenario records route progress, RGB camera data, LiDAR data, collisions, and evaluation metrics.

## Required environment

Activate the virtual environment and expose CARLA's Python API and navigation agents:

```bash
cd ~/carla-simulator
source ~/carla-venv/bin/activate

export CARLA_ROOT="$HOME/CARLA_0.9.16"
export PYTHONPATH="$CARLA_ROOT/PythonAPI/carla:$CARLA_ROOT/PythonAPI/carla/agents:$PYTHONPATH"

python3 -m pip install shapely
python3 -m pip install -r requirements-ai.txt
```

If `from agents.navigation.basic_agent import BasicAgent` fails, check that `CARLA_ROOT` points to the actual CARLA directory and that the `agents` path is included in `PYTHONPATH`.

## Run

```bash
mkdir -p outputs/lab4

python3 lab4/ai_navigation/ai_navigation.py \
  --host 127.0.0.1 \
  --port 2000 \
  --config lab4/ai_navigation/ai_navigation.json \
  --output-dir outputs/lab4
```

## Control loop

The script creates a `BasicAgent`, sets a destination, and repeatedly calls `agent.run_step()`. The returned `VehicleControl` is applied to the ego vehicle. When `agent.done()` becomes true, the vehicle is stopped and the route is evaluated.

## Expected evidence

- route progress and final distance to the goal;
- `result.json` with navigation evaluation;
- `telemetry.csv` with speed, route state, and collisions;
- RGB camera evidence;
- LiDAR point-cloud output;
- collision status.

## Project extensions

Students can compare BasicAgent with a manual controller, add obstacle-distance metrics from LiDAR, detect lane departure from camera images, vary target speed, or compare several destinations and spawn points.
