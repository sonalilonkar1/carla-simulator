# CLI Command Reference

## Inspect files and storage

```bash
pwd
ls -la
find . -maxdepth 2 -type f
df -h /scratch/cmpe281-fa26
```

## SLURM

```bash
sinfo
squeue -u "$USER"
squeue -j JOB_ID
sbatch path/to/job.sbatch
scancel JOB_ID
```

`sbatch` submits a non-interactive batch job. `srun --pty /bin/bash` opens an interactive allocation. `squeue` shows pending and running jobs.

## Apptainer

```bash
apptainer exec --nv --cleanenv IMAGE.sif nvidia-smi
apptainer shell --nv IMAGE.sif
apptainer inspect IMAGE.sif
```

`--nv` exposes NVIDIA libraries. `--cleanenv` avoids incompatible host variables. `--bind HOST:CONTAINER` exposes writable course storage inside the image.

## Verify a transfer

```bash
sha256sum file.tar
```

Compare checksums before and after transfer. Matching SHA-256 values indicate that the file contents are identical with extremely high confidence.

## Inspect results

```bash
cat output/result.json
head telemetry.csv
find frames -name '*.png' | wc -l
```

## Copy output to your Mac

Run `scp` from the Mac, not from the HPC compute node:

```bash
scp -r YOUR_ID@coe-hpc1.sjsu.edu:/scratch/cmpe281-fa26/path/to/output ~/CARLA-results/
```
