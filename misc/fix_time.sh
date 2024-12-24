#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/fix/slurm-%j.out
#SBATCH --job-name="fix_time"
#SBATCH --partition=tallis
#SBATCH --mem=8G

python fix_time.py