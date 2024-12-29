#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/cd_acc/slurm-%j.out
#SBATCH --job-name="compute_cdaccfilt_mod"
#SBATCH --partition=secondary
#SBATCH --mem=64G

python compute_cd_acc_filt.py \
    --mapping data/comdet_acc/cd_acc_test_filt/mapping_test.csv \
    --output_root data/comdet_acc/cd_acc_test_filt \
    --whitelist "infomap,infomap;leiden_cpm,leiden.1;leiden_cpm,leiden.01;leiden_cpm,leiden.001;leiden_cpm,leiden.0001;leiden_mod,leidenmod"