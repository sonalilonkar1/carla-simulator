# CARLA live violation demo

This folder adapts the supplied reference demo for CARLA 0.9.16 on the SJSU
Ubuntu GPU workstation. It preserves the four original scenarios and adds
command-line connection settings plus reliable identification of the ego car.

Only `scenario_test.py`, `stops.py`, and `violation_monitor.py` from the
supplied files are required. `route_inspection.py` and
`global_route_planner.py` are unrelated to this four-scenario demonstration.

## Dependencies

Activate the existing environment and install NumPy if necessary:

```bash
source ~/carla-venv/bin/activate
python -m pip install numpy
```

## Run sequence

1. Start CARLA in terminal 1.
2. Run `live_spectator.py` in terminal 2.
3. Start `scenario_test.py` in terminal 3. Scenarios 1 and 2 run with an
   otherwise empty street.
4. When scenario 3 pauses, start CARLA's bundled `generate_traffic.py` in
   terminal 4, wait for its spawn summary, and press Enter in terminal 3.
5. Keep traffic running for scenario 4. Stop the traffic generator with
   Ctrl+C only after all scenarios finish.

### Terminal 2

```bash
cd ~/carla-simulator/live_demo
python live_spectator.py
```

### Terminal 3

```bash
cd ~/carla-simulator/live_demo
python scenario_test.py \
  --map Town10HD_Opt \
  --duration 20 \
  --log-file violations.txt
```

### Terminal 4, when scenario 3 pauses

```bash
python ~/CARLA_0.9.16/PythonAPI/examples/generate_traffic.py \
  --number-of-vehicles 20 \
  --number-of-walkers 50 \
  --asynch
```

The demo expects `Town10HD_Opt`, matching the supplied reference video.
