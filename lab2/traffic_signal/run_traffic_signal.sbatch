#!/bin/bash
#SBATCH --job-name=carla-lab2-signal
#SBATCH --partition=gpuqs
#SBATCH --exclude=cs002,g12
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:25:00
#SBATCH --output=/scratch/cmpe281-fa26/instructor/018228067/logs/lab2-signal-%j.out
#SBATCH --error=/scratch/cmpe281-fa26/instructor/018228067/logs/lab2-signal-%j.err

set -euo pipefail
MODE=scenario
source "$HOME/cmpe281-carla-dev/slurm/traffic_signal_common.sh"
