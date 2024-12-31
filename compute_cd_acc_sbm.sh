#!/bin/bash
#SBATCH --time=1-12:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/cd_acc/sbm/slurm-%j.out
#SBATCH --job-name="compute_cdaccsbm"
#SBATCH --partition=tallis
#SBATCH --mem=32G

# python map_cd_sbm.py
split="val"
gt_clustering="leiden_cpm_nofiltcm"
gt_resolution="leiden.1"

python compute_cd_acc_sbm.py \
    --mapping data/comdet_acc/cd_acc_${split}_sbm/mapping_${split}_${gt_clustering}_${gt_resolution}.csv \
    --output_root data/comdet_acc/cd_acc_${split}_sbm/