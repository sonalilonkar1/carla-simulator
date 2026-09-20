# CMPE 281 CARLA Lab 2C — Traffic-Signal Compliance

This package discovers a reproducible signalized approach in `Town03_Opt`, then
runs a red-to-green compliance scenario. CARLA is started only inside a SLURM
GPU job. Town03 is loaded with `MapLayer.NONE` and its layers are added
sequentially to avoid the bulk-layer crash observed on the course HPC.

## Files

- `scripts/discover_traffic_lights.py`: writes candidate stop-waypoint metadata.
- `scripts/traffic_signal.py`: stops at red and proceeds after green.
- `configs/traffic_signal.json`: tunable scenario and pass criteria.
- `slurm/*.sbatch`: discovery and scenario submissions.
- `slurm/traffic_signal_common.sh`: shared safe CARLA launcher.

Run discovery before the scenario. Review candidate `0`; if its rendered view
is unsuitable, change `candidate_index` and rerun the scenario.
