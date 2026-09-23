# CMPE 281 CARLA Lab 2C — Traffic-Signal Compliance

This package discovers a reproducible signalized approach in `Town03_Opt`, then
runs a red-to-green compliance scenario. CARLA is started only inside a SLURM
GPU job. Town03 is loaded with `MapLayer.NONE` and its layers are added
sequentially to avoid the bulk-layer crash observed on the course HPC.

## Files

- `discover_traffic_lights.py`: discovers reproducible traffic-light candidates.
- `traffic_signal.py`: stops at red and proceeds after green.
- `traffic_signal.json`: tunable scenario and pass criteria.
- `discover_traffic_lights.sbatch`: submits the discovery job.
- `run_traffic_signal.sbatch`: submits the traffic-signal scenario.
- `traffic_signal_common.sh`: shared CARLA server launcher.

Run discovery before the scenario. Review candidate `0`; if its rendered view
is unsuitable, change `candidate_index` and rerun the scenario.
