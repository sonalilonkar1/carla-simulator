# CMPE 281 CARLA Lab 2C — Traffic-Signal Compliance

This package discovers a reproducible signalized approach in `Town03_Opt`, then
runs a red-to-green compliance scenario. CARLA is started only inside a SLURM
GPU job. Town03 is loaded with `MapLayer.NONE` and its layers are added
sequentially to avoid the bulk-layer crash observed on the course HPC.

## Files

- `pedestrian_crossing.py`: CARLA client and pedestrian-crossing emergency-braking logic.
- `pedestrian_crossing.json`: tunable scenario and pass criteria.
- `run_pedestrian_crossing.sbatch`: GPU allocation and CARLA server lifecycle.

Run discovery before the scenario. Review candidate `0`; if its rendered view
is unsuitable, change `candidate_index` and rerun the scenario.
