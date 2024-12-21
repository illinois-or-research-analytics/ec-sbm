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

# python network_evaluation/compare_simulators_node_coverage.py \
#     --names \
#         "SBM-MCS+eV1 / SBM" \
#         "SBM-MCS+eV1 / SBM+CC" \
#         "SBM-MCS+eV1 / SBM+WCC" \
#     --roots \
#         data/stats/sbmmcsprev1+o+eL1/sbm \
#         data/stats/sbmmcsprev1+o+eL1/sbm_cc \
#         data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#     --resolution \
#         sbm \
#         sbm \
#         sbm \
#     --output-dir output/node_coverage/sbm/sbm/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

# python network_evaluation/compare_simulators_node_coverage.py \
#     --names \
#         "SBM-MCS+eV1 / CPM(0.1)" \
#         "SBM-MCS+eV1 / CPM(0.01)" \
#         "SBM-MCS+eV1 / CPM(0.001)" \
#         "SBM-MCS+eV1 / Mod" \
#     --roots \
#         data/stats/sbmmcsprev1+o/leiden_cpm \
#         data/stats/sbmmcsprev1+o/leiden_cpm \
#         data/stats/sbmmcsprev1+o/leiden_cpm \
#         data/stats/sbmmcsprev1+o/leiden_mod \
#     --resolution \
#         leiden.1 \
#         leiden.01 \
#         leiden.001 \
#         leidenmod \
#     --output-dir output/node_coverage/sbm/leiden/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

# python network_evaluation/compare_simulators_node_coverage.py \
#     --names \
#         "SBM-MCS+eV1 / CPM(0.1)+CM" \
#         "SBM-MCS+eV1 / CPM(0.01)+CM" \
#         "SBM-MCS+eV1 / CPM(0.001)+CM" \
#         "SBM-MCS+eV1 / Mod+CM" \
#     --roots \
#         data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#         data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#         data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#         data/stats/sbmmcsprev1+o/leiden_mod_nofiltcm \
#     --resolution \
#         leiden.1 \
#         leiden.01 \
#         leiden.001 \
#         leidenmod \
#     --output-dir output/node_coverage/sbm/leidencm/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

echo "Done"