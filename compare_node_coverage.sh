#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/node_coverage/slurm-%j.out
#SBATCH --job-name="compare_clustering"
#SBATCH --partition=tallis
#SBATCH --mem=8G

# python network_evaluation/compare_simulators_4.py \
#     --names \
#         "SBM / Leiden-CPM(0.1)" \
#         "SBM / Leiden-CPM(0.01)" \
#         "SBM / Leiden-CPM(0.001)" \
#     --roots \
#         data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#         data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#         data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#     --resolution \
#         leiden.1 \
#         leiden.01 \
#         leiden.001 \
#     --output-dir output/val_nc/sbm/cpm/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

python network_evaluation/compare_simulators_4.py \
    --names \
        "SBM / Leiden-CPM(0.01)" \
        "SBM / IKC(10)+CC" \
        "SBM / InfoMap+CC" \
    --roots \
        data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
        data/stats/sbmmcsprev1+o+eL1/ikc_cc \
        data/stats/sbmmcsprev1+o+eL1/infomap_cc \
    --resolution \
        leiden.01 \
        k10 \
        infomap \
    --output-dir output/val_nc/sbm/leiden.01_k10_infomap/ \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1

echo "Job complete"