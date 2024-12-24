#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/cd_acc/slurm-%j.out
#SBATCH --job-name="compute_cdaccfilt_mod"
#SBATCH --partition=tallis
#SBATCH --mem=64G

python compute_cd_acc_filt.py \
    --whitelist leiden_mod,leidenmod