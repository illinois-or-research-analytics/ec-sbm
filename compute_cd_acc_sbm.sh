#!/bin/bash
#SBATCH --time=3-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/cd_acc/sbm/slurm-%j.out
#SBATCH --job-name="compute_cdaccsbm"
#SBATCH --partition=tallis
#SBATCH --mem=64G

python map_cd_sbm.py
split="val"
python compute_cd_acc_sbm.py \
    --mapping data/comdet_acc/cd_acc_${split}_sbm/mapping_${split}.csv \
    --output_root data/comdet_acc/cd_acc_${split}_sbm/