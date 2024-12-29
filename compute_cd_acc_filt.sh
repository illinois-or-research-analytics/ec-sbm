#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --output=slurm_output/cd_acc/slurm-%j.out
#SBATCH --job-name="compute_cdaccfilt_1cm_all"
#SBATCH --partition=tallis
#SBATCH --mem=32G

split="val"
gt_clustering="leiden_cpm_nofiltcm"
gt_resolution="leiden.1"

python compute_cd_acc_filt.py \
    --mapping data/comdet_acc/cd_acc_${split}_filt/mapping_${split}_${gt_clustering}_${gt_resolution}.csv \
    --output_root data/comdet_acc/cd_acc_${split}_filt \
    --whitelist "infomap,infomap;leiden_cpm,leiden.1;leiden_cpm,leiden.01;leiden_cpm,leiden.001;leiden_cpm,leiden.0001;leiden_mod,leidenmod"