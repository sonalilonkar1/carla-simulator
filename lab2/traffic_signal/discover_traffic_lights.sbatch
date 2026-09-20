#!/bin/bash
#SBATCH --job-name=carla-light-scan
#SBATCH --partition=gpuqs
#SBATCH --exclude=cs002,g12
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/cmpe281-fa26/instructor/018228067/logs/light-scan-%j.out
#SBATCH --error=/scratch/cmpe281-fa26/instructor/018228067/logs/light-scan-%j.err

set -euo pipefail
MODE=discovery
source "$HOME/cmpe281-carla-dev/slurm/traffic_signal_common.sh"
