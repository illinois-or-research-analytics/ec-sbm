#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/fix_edge/slurm-%j.out
#SBATCH --job-name="test_compute"
#SBATCH --partition=secondary
#SBATCH --mem=128G

# ===================================

python network_evaluation/compute_stats.py \
    --input-network data/networks/sbmmcsprev1+o/leiden_cpm_cm/cit_hepph/leiden.01/0/edge.tsv \
    --input-clustering data/networks/sbmmcsprev1+o/leiden_cpm_cm/cit_hepph/leiden.01/0/com.tsv \
    --output-folder test/output/stats/sbmmcsprev1+o/leiden_cpm_cm/cit_hepph/leiden.01/0/