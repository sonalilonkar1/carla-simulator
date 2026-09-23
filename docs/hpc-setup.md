# HPC Setup

## Safety rule

`g17` is a login/submission node. Do not start CARLA or run GPU workloads there. Use it only to inspect files and submit jobs. CARLA must run on a node allocated by SLURM.

## Login

From your local computer:

```bash
ssh YOUR_SJSU_ID@coe-hpc1.sjsu.edu
ssh -X coe-hpc3
```

The second connection normally places you on the COE-HPC3 login node (`g17`).

## Shared storage

```bash
SHARED=/scratch/cmpe281-fa26
mkdir -p "$SHARED/$USER/logs" "$SHARED/$USER/output"
test -w "$SHARED" && echo "Shared storage is writable"
```

Keep personal experiments in a user-specific directory.

## Interactive GPU allocation

```bash
srun \
  --partition=gpuqs \
  --gres=gpu:1 \
  --nodes=1 \
  --ntasks=1 \
  --cpus-per-task=4 \
  --mem=16G \
  --time=00:30:00 \
  --pty /bin/bash
```

After the prompt changes to a compute node:

```bash
hostname
echo "$SLURM_JOB_ID"
echo "$CUDA_VISIBLE_DEVICES"
nvidia-smi
```

Use `srun` for short tests and `sbatch` for repeatable or long experiments.

## Release the allocation

```bash
exit
```
