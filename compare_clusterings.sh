#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/clusterings/slurm-%j.out
#SBATCH --job-name="compare_clustering"
#SBATCH --partition=tallis
#SBATCH --mem=8G

for method in sbmmcsprev1+o+eL1 abcdta4+o sbm+o abcd+o
do 
    if [ $method == "sbmmcsprev1+o+eL1" ]; then
        method_name="SBM-MCS"
    elif [ $method == "abcdta4+o" ]; then
        method_name="ABCD-MCS"
    elif [ $method == "sbm+o" ]; then
        method_name="SBM"
    elif [ $method == "abcd+o" ]; then
        method_name="ABCD"
    fi

    python network_evaluation/compare_simulators_3.py \
        --names \
            "${method_name} / SBM" \
            "${method_name} / SBM-CC" \
            "${method_name} / SBM-WCC" \
        --roots \
            data/stats/${method}/sbm \
            data/stats/${method}/sbm_cc \
            data/stats/${method}/sbm_wcc \
        --resolution \
            sbm \
            sbm \
            sbm \
        --output-dir output/val_cl/${method}/sbm/ \
        --network-whitelist-fp data/networks_val.txt \
        --num-replicates 1

    python network_evaluation/compare_simulators_3.py \
        --names \
            "${method_name} / CPM(0.1)" \
            "${method_name} / CPM(0.01)" \
            "${method_name} / CPM(0.001)" \
        --roots \
            data/stats/${method}/leiden_cpm \
            data/stats/${method}/leiden_cpm \
            data/stats/${method}/leiden_cpm \
        --resolution \
            leiden.1 \
            leiden.01 \
            leiden.001 \
        --output-dir output/val_cl/${method}/cpm/ \
        --network-whitelist-fp data/networks_val.txt \
        --num-replicates 1

    python network_evaluation/compare_simulators_3.py \
        --names \
            "${method_name} / CPM(0.1) + CM" \
            "${method_name} / CPM(0.01) + CM" \
            "${method_name} / CPM(0.001) + CM" \
        --roots \
            data/stats/${method}/leiden_cpm_nofiltcm \
            data/stats/${method}/leiden_cpm_nofiltcm \
            data/stats/${method}/leiden_cpm_nofiltcm \
        --resolution \
            leiden.1 \
            leiden.01 \
            leiden.001 \
        --output-dir output/val_cl/${method}/cpmcm/ \
        --network-whitelist-fp data/networks_val.txt \
        --num-replicates 1

    python network_evaluation/compare_simulators_3.py \
        --names \
            "${method_name} / CPM(0.1)" \
            "${method_name} / CPM(0.01)" \
            "${method_name} / CPM(0.001)" \
            "${method_name} / Mod" \
            "${method_name} / CPM(0.1) + CM" \
            "${method_name} / CPM(0.01) + CM" \
            "${method_name} / CPM(0.001) + CM" \
            "${method_name} / Mod + CM" \
            "${method_name} / SBM" \
            "${method_name} / SBM-CC" \
            "${method_name} / SBM-WCC" \
        --roots \
            data/stats/${method}/leiden_cpm \
            data/stats/${method}/leiden_cpm \
            data/stats/${method}/leiden_cpm \
            data/stats/${method}/leiden_mod \
            data/stats/${method}/leiden_cpm_nofiltcm \
            data/stats/${method}/leiden_cpm_nofiltcm \
            data/stats/${method}/leiden_cpm_nofiltcm \
            data/stats/${method}/leiden_mod_nofiltcm \
            data/stats/${method}/sbm \
            data/stats/${method}/sbm_cc \
            data/stats/${method}/sbm_wcc \
        --resolution \
            leiden.1 \
            leiden.01 \
            leiden.001 \
            leidenmod \
            leiden.1 \
            leiden.01 \
            leiden.001 \
            leidenmod \
            sbm \
            sbm \
            sbm \
        --output-dir output/val_cl/${method}/cpm_cpmcm_sbm_mod/ \
        --network-whitelist-fp data/networks_val.txt \
        --num-replicates 1
done

# python network_evaluation/compare_simulators_3.py \
#     --names \
#         "SBM-MCS / CPM(0.1)" \
#         "SBM-MCS / CPM(0.01)" \
#         "SBM-MCS / CPM(0.001)" \
#     --roots \
#         data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#         data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#         data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#     --resolution \
#         leiden.1 \
#         leiden.01 \
#         leiden.001 \
#     --output-dir output/val_cl/sbmmcs/cpm/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

# python network_evaluation/compare_simulators_3.py \
#     --names \
#         "SBM-MCS / SBM" \
#         "SBM-MCS / SBM+CC" \
#         "SBM-MCS / SBM+WCC" \
#     --roots \
#         data/stats/sbmmcsprev1+o+eL1/sbm \
#         data/stats/sbmmcsprev1+o+eL1/sbm_cc \
#         data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#     --resolution \
#         sbm \
#         sbm \
#         sbm \
#     --output-dir output/val_cl/sbmmcs/sbm/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

# # ABCD-MCS
# python network_evaluation/compare_simulators_3.py \
#     --names \
#         "ABCD-MCS / SBM" \
#         "ABCD-MCS / SBM-CC" \
#         "ABCD-MCS / SBM-WCC" \
#     --roots \
#         data/stats/abcdta4+o/sbm \
#         data/stats/abcdta4+o/sbm_cc \
#         data/stats/abcdta4+o/sbm_wcc \
#     --resolution \
#         sbm \
#         sbm \
#         sbm \
#     --output-dir output/val_cl/abcdmcs/sbm/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

# python network_evaluation/compare_simulators_3.py \
#     --names \
#         "ABCD-MCS / CPM(0.1)" \
#         "ABCD-MCS / CPM(0.01)" \
#         "ABCD-MCS / CPM(0.001)" \
#     --roots \
#         data/stats/abcdta4+o/leiden_cpm \
#         data/stats/abcdta4+o/leiden_cpm \
#         data/stats/abcdta4+o/leiden_cpm \
#     --resolution \
#         leiden.1 \
#         leiden.01 \
#         leiden.001 \
#     --output-dir output/val_cl/abcdmcs/cpm/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

# python network_evaluation/compare_simulators_3.py \
#     --names \
#         "SBM / Leiden-CPM(0.1)+CM(no-filter)" \
#         "SBM / Leiden-CPM(0.001)" \
#         "ABCD / Leiden-CPM(0.001)+CM(no-filter)" \
#         "ABCD / Leiden-CPM(0.001)" \
#     --roots \
#         data/stats/sbmmcsprev1+o+eL1/leiden_cpm_nofiltcm \
#         data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#         data/stats/abcdta4+o/leiden_cpm_nofiltcm \
#         data/stats/abcdta4+o/leiden_cpm \
#     --resolution \
#         leiden.1 \
#         leiden.001 \
#         leiden.001 \
#         leiden.001 \
#     --output-dir output/val_cl/sbm_abcd/cpm_ikc_mod_infomap/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1

# for method in sbmmcsprev1+o sbmmcsprev1+o+eL1 abcdta4+o abcdta4+o+eL2 RECCSv1_OS1 RECCSv2_OS1 # sbmmcsprev1+o+eL1 abcdta4+o
# do
#     python network_evaluation/compare_simulators_3.py \
#         --names \
#             "InfoMap+CM(no-filter)" \
#             "IKC(10)+CM(no-filter)" \
#             "Leiden-CPM(0.1)+CM(no-filter)" \
#             "Leiden-CPM(0.01)+CM(no-filter)" \
#             "Leiden-CPM(0.001)+CM(no-filter)" \
#             "Leiden-Mod+CM(no-filter)" \
#             "InfoMap+CC" \
#             "IKC(10)+CC" \
#             "Leiden-CPM(0.1)" \
#             "Leiden-CPM(0.01)" \
#             "Leiden-CPM(0.001)" \
#             "Leiden-Mod" \
#         --roots \
#             data/stats/${method}/infomap_nofiltcm \
#             data/stats/${method}/ikc_nofiltcm \
#             data/stats/${method}/leiden_cpm_nofiltcm \
#             data/stats/${method}/leiden_cpm_nofiltcm \
#             data/stats/${method}/leiden_cpm_nofiltcm \
#             data/stats/${method}/leiden_mod_nofiltcm \
#             data/stats/${method}/infomap_cc \
#             data/stats/${method}/ikc_cc \
#             data/stats/${method}/leiden_cpm \
#             data/stats/${method}/leiden_cpm \
#             data/stats/${method}/leiden_cpm \
#             data/stats/${method}/leiden_mod \
#         --resolution \
#             infomap \
#             k10 \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             infomap \
#             k10 \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#         --output-dir output/val_cl/${method}/cpm_ikc_mod_infomap/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1
# done



echo "Done"
