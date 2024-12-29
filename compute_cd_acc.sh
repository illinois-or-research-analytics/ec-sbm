#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/cd_acc/slurm-%j.out
#SBATCH --job-name="compute_cdacc_mod"
#SBATCH --partition=secondary
#SBATCH --mem=64G

python compute_cd_acc.py \
    --mapping data/comdet_acc/cd_acc_test/mapping_test.csv \
    --output_root data/comdet_acc/cd_acc_test \
    --whitelist leiden_mod,leidenmod