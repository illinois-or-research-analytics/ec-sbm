#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/clusterings/slurm-%j.out
#SBATCH --job-name="compare_clustering"
#SBATCH --partition=tallis
#SBATCH --mem=8G

# python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "ABCD-MCS / SBM" \
#             "ABCD-MCS / SBM-CC" \
#             "ABCD-MCS / SBM-WCC" \
#             "ABCD-MCS / CPM(0.1)" \
#             "ABCD-MCS / CPM(0.01)" \
#             "ABCD-MCS / CPM(0.001)" \
#             "ABCD-MCS / Mod" \
#             "ABCD-MCS / CPM(0.1)+CM" \
#             "ABCD-MCS / CPM(0.01)+CM" \
#             "ABCD-MCS / CPM(0.001)+CM" \
#             "ABCD-MCS / Mod+CM" \
#             "ABCD-MCS+eV1 / SBM" \
#             "ABCD-MCS+eV1 / SBM-CC" \
#             "ABCD-MCS+eV1 / SBM-WCC" \
#             "ABCD-MCS+eV1 / CPM(0.1)" \
#             "ABCD-MCS+eV1 / CPM(0.01)" \
#             "ABCD-MCS+eV1 / CPM(0.001)" \
#             "ABCD-MCS+eV1 / Mod" \
#             "ABCD-MCS+eV1 / CPM(0.1)+CM" \
#             "ABCD-MCS+eV1 / CPM(0.01)+CM" \
#             "ABCD-MCS+eV1 / CPM(0.001)+CM" \
#             "ABCD-MCS+eV1 / Mod+CM" \
#             "SBM / SBM" \
#             "SBM / SBM-CC" \
#             "SBM / SBM-WCC" \
#             "SBM / CPM(0.1)" \
#             "SBM / CPM(0.01)" \
#             "SBM / CPM(0.001)" \
#             "SBM / Mod" \
#             "SBM / CPM(0.1)+CM" \
#             "SBM / CPM(0.01)+CM" \
#             "SBM / CPM(0.001)+CM" \
#             "SBM / Mod+CM" \
#             "SBM-MCS / SBM" \
#             "SBM-MCS / SBM-CC" \
#             "SBM-MCS / SBM-WCC" \
#             "SBM-MCS / CPM(0.1)" \
#             "SBM-MCS / CPM(0.01)" \
#             "SBM-MCS / CPM(0.001)" \
#             "SBM-MCS / Mod" \
#             "SBM-MCS / CPM(0.1)+CM" \
#             "SBM-MCS / CPM(0.01)+CM" \
#             "SBM-MCS / CPM(0.001)+CM" \
#             "SBM-MCS / Mod+CM" \
#             "SBM-MCS+eV1 / SBM" \
#             "SBM-MCS+eV1 / SBM-CC" \
#             "SBM-MCS+eV1 / SBM-WCC" \
#             "SBM-MCS+eV1 / CPM(0.1)" \
#             "SBM-MCS+eV1 / CPM(0.01)" \
#             "SBM-MCS+eV1 / CPM(0.001)" \
#             "SBM-MCS+eV1 / Mod" \
#             "SBM-MCS+eV1 / CPM(0.1)+CM" \
#             "SBM-MCS+eV1 / CPM(0.01)+CM" \
#             "SBM-MCS+eV1 / CPM(0.001)+CM" \
#             "SBM-MCS+eV1 / Mod+CM" \
#             "RECCSv1 / SBM" \
#             "RECCSv1 / SBM-CC" \
#             "RECCSv1 / SBM-WCC" \
#             "RECCSv1 / CPM(0.1)" \
#             "RECCSv1 / CPM(0.01)" \
#             "RECCSv1 / CPM(0.001)" \
#             "RECCSv1 / Mod" \
#             "RECCSv1 / CPM(0.1)+CM" \
#             "RECCSv1 / CPM(0.01)+CM" \
#             "RECCSv1 / CPM(0.001)+CM" \
#             "RECCSv1 / Mod+CM" \
#         --roots \
#             data/stats/abcdta4+o/sbm \
#             data/stats/abcdta4+o/sbm_cc \
#             data/stats/abcdta4+o/sbm_wcc \
#             data/stats/abcdta4+o/leiden_cpm \
#             data/stats/abcdta4+o/leiden_cpm \
#             data/stats/abcdta4+o/leiden_cpm \
#             data/stats/abcdta4+o/leiden_mod \
#             data/stats/abcdta4+o/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o/leiden_mod_nofiltcm \
#             data/stats/abcdta4+o+eL1/sbm \
#             data/stats/abcdta4+o+eL1/sbm_cc \
#             data/stats/abcdta4+o+eL1/sbm_wcc \
#             data/stats/abcdta4+o+eL1/leiden_cpm \
#             data/stats/abcdta4+o+eL1/leiden_cpm \
#             data/stats/abcdta4+o+eL1/leiden_cpm \
#             data/stats/abcdta4+o+eL1/leiden_mod \
#             data/stats/abcdta4+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o+eL1/leiden_mod_nofiltcm \
#             data/stats/sbm+o_/sbm \
#             data/stats/sbm+o_/sbm_cc \
#             data/stats/sbm+o_/sbm_wcc \
#             data/stats/sbm+o_/leiden_cpm \
#             data/stats/sbm+o_/leiden_cpm \
#             data/stats/sbm+o_/leiden_cpm \
#             data/stats/sbm+o_/leiden_mod \
#             data/stats/sbm+o_/leiden_cpm_nofiltcm \
#             data/stats/sbm+o_/leiden_cpm_nofiltcm \
#             data/stats/sbm+o_/leiden_cpm_nofiltcm \
#             data/stats/sbm+o_/leiden_mod_nofiltcm \
#             data/stats/sbmmcsprev1+o/sbm \
#             data/stats/sbmmcsprev1+o/sbm_cc \
#             data/stats/sbmmcsprev1+o/sbm_wcc \
#             data/stats/sbmmcsprev1+o/leiden_cpm \
#             data/stats/sbmmcsprev1+o/leiden_cpm \
#             data/stats/sbmmcsprev1+o/leiden_cpm \
#             data/stats/sbmmcsprev1+o/leiden_mod \
#             data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o/leiden_mod_nofiltcm \
#             data/stats/sbmmcsprev1+o+eL1/sbm \
#             data/stats/sbmmcsprev1+o+eL1/sbm_cc \
#             data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_mod \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_mod_nofiltcm \
#             data/stats/RECCSv1_OS1/sbm \
#             data/stats/RECCSv1_OS1/sbm_cc \
#             data/stats/RECCSv1_OS1/sbm_wcc \
#             data/stats/RECCSv1_OS1/leiden_cpm \
#             data/stats/RECCSv1_OS1/leiden_cpm \
#             data/stats/RECCSv1_OS1/leiden_cpm \
#             data/stats/RECCSv1_OS1/leiden_mod \
#             data/stats/RECCSv1_OS1/leiden_cpm_nofiltcm \
#             data/stats/RECCSv1_OS1/leiden_cpm_nofiltcm \
#             data/stats/RECCSv1_OS1/leiden_cpm_nofiltcm \
#             data/stats/RECCSv1_OS1/leiden_mod_nofiltcm \
#         --resolution \
#             sbm \
#             sbm \
#             sbm \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             sbm \
#             sbm \
#             sbm \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             sbm \
#             sbm \
#             sbm \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             sbm \
#             sbm \
#             sbm \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             sbm \
#             sbm \
#             sbm \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             sbm \
#             sbm \
#             sbm \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#         --stats \
#             pseudo_diameter \
#         --output-dir output/gt/diam/sbm/abcdmcs_abcdmcsv1_sbm_sbmmcs_sbmmcsv1_reccsv1 \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 6

# =====================

# for method in sbmmcsprev1+o+eL1 # sbmmcsprev1+o abcdta4+o abcdta4+o+eL1 sbm+o_ abcd+o
# do 
#     if [ $method == "sbmmcsprev1+o+eL1" ]; then
#         method_name="SBM-MCS+eV1"
#     elif [ $method == "sbmmcsprev1+o" ]; then
#         method_name="SBM-MCS"
#     elif [ $method == "abcdta4+o" ]; then
#         method_name="ABCD-MCS"
#     elif [ $method == "abcdta4+o+eL1" ]; then
#         method_name="ABCD-MCS+eV1"
#     elif [ $method == "sbm+o_" ]; then
#         method_name="SBM"
#     elif [ $method == "abcd+o" ]; then
#         method_name="ABCD"
#     elif [ $method == "RECCSv1_OS1" ]; then
#         method_name="RECCSv1"
#     else
#         echo "Error: Unknown method"
#         continue
#     fi

#     python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "${method_name} / CPM(0.1)" \
#             "${method_name} / CPM(0.01)" \
#             "${method_name} / CPM(0.001)" \
#             "${method_name} / Mod" \
#             "${method_name} / CPM(0.1) + CM" \
#             "${method_name} / CPM(0.01) + CM" \
#             "${method_name} / CPM(0.001) + CM" \
#             "${method_name} / Mod + CM" \
#             "${method_name} / SBM" \
#             "${method_name} / SBM-CC" \
#             "${method_name} / SBM-WCC" \
#         --roots \
#             data/stats/${method}/leiden_cpm \
#             data/stats/${method}/leiden_cpm \
#             data/stats/${method}/leiden_cpm \
#             data/stats/${method}/leiden_mod \
#             data/stats/${method}/leiden_cpm_nofiltcm \
#             data/stats/${method}/leiden_cpm_nofiltcm \
#             data/stats/${method}/leiden_cpm_nofiltcm \
#             data/stats/${method}/leiden_mod_nofiltcm \
#             data/stats/${method}/sbm \
#             data/stats/${method}/sbm_cc \
#             data/stats/${method}/sbm_wcc \
#         --resolution \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             sbm \
#             sbm \
#             sbm \
#         --stats \
#             pseudo_diameter \
#             tau \
#         --output-dir output/gt/diam/per_sim/${method}/leiden_leidencm_sbm/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 3
# done

# =====================

# python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "ABCD-MCS / SBM-CC" \
#             "ABCD-MCS / SBM-WCC" \
#             "ABCD-MCS+eV1 / SBM-CC" \
#             "ABCD-MCS+eV1 / SBM-WCC" \
#             "SBM-MCS / SBM-CC" \
#             "SBM-MCS / SBM-WCC" \
#             "SBM-MCS+eV1 / SBM-CC" \
#             "SBM-MCS+eV1 / SBM-WCC" \
#             "RECCSv1 / SBM-CC" \
#             "RECCSv1 / SBM-WCC" \
#         --roots \
#             data/stats/abcdta4+o/sbm_cc \
#             data/stats/abcdta4+o/sbm_wcc \
#             data/stats/abcdta4+o+eL1/sbm_cc \
#             data/stats/abcdta4+o+eL1/sbm_wcc \
#             data/stats/sbmmcsprev1+o/sbm_cc \
#             data/stats/sbmmcsprev1+o/sbm_wcc \
#             data/stats/sbmmcsprev1+o+eL1/sbm_cc \
#             data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#             data/stats/RECCSv1_OS1/sbm_cc \
#             data/stats/RECCSv1_OS1/sbm_wcc \
#         --resolution \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#         --output-dir output/gt/comp/sbm/abcd_sbm_reccs/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 5

# python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "SBM / SBM" \
#             "SBM / SBM-CC" \
#             "SBM / SBM-WCC" \
#             "SBM-MCS / SBM" \
#             "SBM-MCS / SBM-CC" \
#             "SBM-MCS / SBM-WCC" \
#             "SBM-MCS+eV1 / SBM" \
#             "SBM-MCS+eV1 / SBM-CC" \
#             "SBM-MCS+eV1 / SBM-WCC" \
#             "RECCSv1 / SBM" \
#             "RECCSv1 / SBM-CC" \
#             "RECCSv1 / SBM-WCC" \
#         --roots \
#             data/stats/sbm+o_/sbm \
#             data/stats/sbm+o_/sbm_cc \
#             data/stats/sbm+o_/sbm_wcc \
#             data/stats/sbmmcsprev1+o/sbm \
#             data/stats/sbmmcsprev1+o/sbm_cc \
#             data/stats/sbmmcsprev1+o/sbm_wcc \
#             data/stats/sbmmcsprev1+o+eL1/sbm \
#             data/stats/sbmmcsprev1+o+eL1/sbm_cc \
#             data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#             data/stats/RECCSv1_OS1/sbm \
#             data/stats/RECCSv1_OS1/sbm_cc \
#             data/stats/RECCSv1_OS1/sbm_wcc \
#         --resolution \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#         --output-dir output/gt/comp/sbm/sbm/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 4

# python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "ABCD / SBM" \
#             "ABCD / SBM-CC" \
#             "ABCD / SBM-WCC" \
#             "ABCD-MCS / SBM" \
#             "ABCD-MCS / SBM-CC" \
#             "ABCD-MCS / SBM-WCC" \
#             "ABCD-MCS+eV1 / SBM" \
#             "ABCD-MCS+eV1 / SBM-CC" \
#             "ABCD-MCS+eV1 / SBM-WCC" \
#             "RECCSv1 / SBM" \
#             "RECCSv1 / SBM-CC" \
#             "RECCSv1 / SBM-WCC" \
#         --roots \
#             data/stats/abcd+o/sbm \
#             data/stats/abcd+o/sbm_cc \
#             data/stats/abcd+o/sbm_wcc \
#             data/stats/abcdta4+o/sbm \
#             data/stats/abcdta4+o/sbm_cc \
#             data/stats/abcdta4+o/sbm_wcc \
#             data/stats/abcdta4+o+eL1/sbm \
#             data/stats/abcdta4+o+eL1/sbm_cc \
#             data/stats/abcdta4+o+eL1/sbm_wcc \
#             data/stats/RECCSv1_OS1/sbm \
#             data/stats/RECCSv1_OS1/sbm_cc \
#             data/stats/RECCSv1_OS1/sbm_wcc \
#         --resolution \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#             sbm \
#         --output-dir output/gt/comp/abcd/sbm/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 4

# python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "SBM / CPM(0.1)" \
#             "SBM / CPM(0.01)" \
#             "SBM / CPM(0.001)" \
#             "SBM / Mod" \
#             "SBM-MCS / CPM(0.1)" \
#             "SBM-MCS / CPM(0.01)" \
#             "SBM-MCS / CPM(0.001)" \
#             "SBM-MCS / Mod" \
#             "SBM-MCS+eV1 / CPM(0.1)" \
#             "SBM-MCS+eV1 / CPM(0.01)" \
#             "SBM-MCS+eV1 / CPM(0.001)" \
#             "SBM-MCS+eV1 / Mod" \
#         --roots \
#             data/stats/sbm+o_/leiden_cpm \
#             data/stats/sbm+o_/leiden_cpm \
#             data/stats/sbm+o_/leiden_cpm \
#             data/stats/sbm+o_/leiden_mod \
#             data/stats/sbmmcsprev1+o/leiden_cpm \
#             data/stats/sbmmcsprev1+o/leiden_cpm \
#             data/stats/sbmmcsprev1+o/leiden_cpm \
#             data/stats/sbmmcsprev1+o/leiden_mod \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_mod \
#         --resolution \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#         --output-dir output/gt/comp/sbm/leiden/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 3

# python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "ABCD / CPM(0.1)" \
#             "ABCD / CPM(0.01)" \
#             "ABCD / CPM(0.001)" \
#             "ABCD / Mod" \
#             "ABCD-MCS / CPM(0.1)" \
#             "ABCD-MCS / CPM(0.01)" \
#             "ABCD-MCS / CPM(0.001)" \
#             "ABCD-MCS / Mod" \
#             "ABCD-MCS+eV1 / CPM(0.1)" \
#             "ABCD-MCS+eV1 / CPM(0.01)" \
#             "ABCD-MCS+eV1 / CPM(0.001)" \
#             "ABCD-MCS+eV1 / Mod" \
#         --roots \
#             data/stats/abcd+o/leiden_cpm \
#             data/stats/abcd+o/leiden_cpm \
#             data/stats/abcd+o/leiden_cpm \
#             data/stats/abcd+o/leiden_mod \
#             data/stats/abcdta4+o/leiden_cpm \
#             data/stats/abcdta4+o/leiden_cpm \
#             data/stats/abcdta4+o/leiden_cpm \
#             data/stats/abcdta4+o/leiden_mod \
#             data/stats/abcdta4+o+eL1/leiden_cpm \
#             data/stats/abcdta4+o+eL1/leiden_cpm \
#             data/stats/abcdta4+o+eL1/leiden_cpm \
#             data/stats/abcdta4+o+eL1/leiden_mod \
#         --resolution \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#         --output-dir output/gt/comp/abcd/leiden/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 3

# python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "SBM / CPM(0.1)+CM" \
#             "SBM / CPM(0.01)+CM" \
#             "SBM / CPM(0.001)+CM" \
#             "SBM / Mod+CM" \
#             "SBM-MCS / CPM(0.1)+CM" \
#             "SBM-MCS / CPM(0.01)+CM" \
#             "SBM-MCS / CPM(0.001)+CM" \
#             "SBM-MCS / Mod+CM" \
#             "SBM-MCS+eV1 / CPM(0.1)+CM" \
#             "SBM-MCS+eV1 / CPM(0.01)+CM" \
#             "SBM-MCS+eV1 / CPM(0.001)+CM" \
#             "SBM-MCS+eV1 / Mod+CM" \
#         --roots \
#             data/stats/sbm+o_/leiden_cpm_nofiltcm \
#             data/stats/sbm+o_/leiden_cpm_nofiltcm \
#             data/stats/sbm+o_/leiden_cpm_nofiltcm \
#             data/stats/sbm+o_/leiden_mod_nofiltcm \
#             data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o/leiden_mod_nofiltcm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/sbmmcsprev1+o+eL1/leiden_mod_nofiltcm \
#         --resolution \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#         --output-dir output/gt/comp/sbm/leidencm/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 3

# python network_evaluation/compare_simulators_gt.py \
#         --names \
#             "ABCD / CPM(0.1)+CM" \
#             "ABCD / CPM(0.01)+CM" \
#             "ABCD / CPM(0.001)+CM" \
#             "ABCD / Mod+CM" \
#             "ABCD-MCS / CPM(0.1)+CM" \
#             "ABCD-MCS / CPM(0.01)+CM" \
#             "ABCD-MCS / CPM(0.001)+CM" \
#             "ABCD-MCS / Mod+CM" \
#             "ABCD-MCS+eV1 / CPM(0.1)+CM" \
#             "ABCD-MCS+eV1 / CPM(0.01)+CM" \
#             "ABCD-MCS+eV1 / CPM(0.001)+CM" \
#             "ABCD-MCS+eV1 / Mod+CM" \
#         --roots \
#             data/stats/abcd+o/leiden_cpm_nofiltcm \
#             data/stats/abcd+o/leiden_cpm_nofiltcm \
#             data/stats/abcd+o/leiden_cpm_nofiltcm \
#             data/stats/abcd+o/leiden_mod_nofiltcm \
#             data/stats/abcdta4+o/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o/leiden_mod_nofiltcm \
#             data/stats/abcdta4+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o+eL1/leiden_cpm_nofiltcm \
#             data/stats/abcdta4+o+eL1/leiden_mod_nofiltcm \
#         --resolution \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#             leiden.1 \
#             leiden.01 \
#             leiden.001 \
#             leidenmod \
#         --output-dir output/gt/comp/abcd/leidencm/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 3


# for clustering in leiden_mod # sbm sbm_cc sbm_wcc leiden_cpm leiden_cpm_nofiltcm leiden_mod leiden_mod_nofiltcm ikc_cc ikc_nofiltcm infomap_cc infomap_nofiltcm
# do
#     for resolution in sbm leiden.001 leiden.01 leiden.1 leidenmod k10 infomap
#     do
#         # Matching clustering with resolution
#         if [ $clustering = "leiden_cpm_cm" ] || [ $clustering = "leiden_cpm" ] || [ $clustering = "leiden_cpm_nofiltcm" ]; then
#             if [ ! $resolution = "leiden.001" ] && [ ! $resolution = "leiden.01" ] && [ ! $resolution = "leiden.1" ]; then
#                 continue
#             fi
#         elif [ $clustering = "leiden_mod_cm" ] || [ $clustering = "leiden_mod" ] || [ $clustering = "leiden_mod_nofiltcm" ]; then
#             if [ ! $resolution = "leidenmod" ]; then
#                 continue
#             fi
#         elif [ $clustering = "ikc_cm" ] || [ $clustering = "ikc_cc" ] || [ $clustering = "ikc_nofiltcm" ]; then
#             if [ ! $resolution = "k10" ]; then
#                 continue
#             fi
#         elif [ $clustering = "infomap_cc" ] || [ $clustering = "infomap_nofiltcm" ]; then
#             if [ ! $resolution = "infomap" ]; then
#                 continue
#             fi
#         elif [ $clustering = "sbm_cc" ] || [ $clustering = "sbm_wcc" ] || [ $clustering = "sbm" ]; then
#             if [ ! $resolution = "sbm" ]; then
#                 continue
#             fi
#         fi

#         python network_evaluation/compare_simulators_gt.py \
#             --names \
#                 "SBM" \
#                 "SBM-MCS" \
#                 "SBM-MCS+eV1" \
#                 "ABCD" \
#                 "ABCD-MCS" \
#                 "ABCD-MCS+eV1" \
#                 "RECCSv1" \
#             --roots \
#                 data/stats/sbm+o_/${clustering} \
#                 data/stats/sbmmcsprev1+o/${clustering} \
#                 data/stats/sbmmcsprev1+o+eL1/${clustering} \
#                 data/stats/abcd+o/${clustering} \
#                 data/stats/abcdta4+o/${clustering} \
#                 data/stats/abcdta4+o+eL1/${clustering} \
#                 data/stats/RECCSv1_OS1/${clustering} \
#             --resolution \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#             --output-dir output/gt/val_sim/sbm_abcd_reccs/${clustering}/${resolution}/ \
#             --network-whitelist-fp data/networks_val.txt \
#             --num-replicates 1 \
#             --ncols 3

#         python network_evaluation/compare_simulators_gt.py \
#             --names \
#                 "SBM" \
#                 "ABCD" \
#             --roots \
#                 data/stats/sbm+o_/${clustering} \
#                 data/stats/abcd+o/${clustering} \
#             --resolution \
#                 ${resolution} \
#                 ${resolution} \
#             --output-dir output/gt/val_sim/sbm_abcd/${clustering}/${resolution}/ \
#             --network-whitelist-fp data/networks_val.txt \
#             --num-replicates 1 \
#             --ncols 2
        
#         python network_evaluation/compare_simulators_gt.py \
#             --names \
#                 "ABCD" \
#                 "ABCD-MCS" \
#                 "ABCD-MCS+eV1" \
#             --roots \
#                 data/stats/abcd+o/${clustering} \
#                 data/stats/abcdta4+o/${clustering} \
#                 data/stats/abcdta4+o+eL1/${clustering} \
#             --resolution \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#             --output-dir output/gt/val_sim/abcd/${clustering}/${resolution}/ \
#             --network-whitelist-fp data/networks_val.txt \
#             --num-replicates 1 \
#             --ncols 3
        
#         python network_evaluation/compare_simulators_gt.py \
#             --names \
#                 "SBM" \
#                 "SBM-MCS" \
#                 "SBM-MCS+eV1" \
#             --roots \
#                 data/stats/sbm+o_/${clustering} \
#                 data/stats/sbmmcsprev1+o/${clustering} \
#                 data/stats/sbmmcsprev1+o+eL1/${clustering} \
#             --resolution \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#             --output-dir output/gt/val_sim/sbm/${clustering}/${resolution}/ \
#             --network-whitelist-fp data/networks_val.txt \
#             --num-replicates 1 \
#             --ncols 3

#         python network_evaluation/compare_simulators_gt.py \
#             --names \
#                 "SBM-MCS" \
#                 "SBM-MCS+eV1" \
#                 "ABCD-MCS" \
#                 "ABCD-MCS+eV1" \
#             --roots \
#                 data/stats/sbmmcsprev1+o/${clustering} \
#                 data/stats/sbmmcsprev1+o+eL1/${clustering} \
#                 data/stats/abcdta4+o/${clustering} \
#                 data/stats/abcdta4+o+eL1/${clustering} \
#             --resolution \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#             --output-dir output/gt/val_sim/new/sbm_abcd/${clustering}/${resolution}/ \
#             --network-whitelist-fp data/networks_val.txt \
#             --num-replicates 1 \
#             --ncols 2

#         python network_evaluation/compare_simulators_gt.py \
#             --names \
#                 "SBM-MCS" \
#                 "SBM-MCS+eV1" \
#                 "ABCD-MCS" \
#                 "ABCD-MCS+eV1" \
#                 "RECCSv1" \
#             --roots \
#                 data/stats/sbmmcsprev1+o/${clustering} \
#                 data/stats/sbmmcsprev1+o+eL1/${clustering} \
#                 data/stats/abcdta4+o/${clustering} \
#                 data/stats/abcdta4+o+eL1/${clustering} \
#                 data/stats/RECCSv1_OS1/${clustering} \
#             --resolution \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#             --output-dir output/gt/val_sim/new/sbm_abcd_reccs/${clustering}/${resolution}/ \
#             --network-whitelist-fp data/networks_val.txt \
#             --num-replicates 1 \
#             --ncols 3
#     done
# done

for method in sbmmcsprev1+o+eL1 abcdta4+o RECCSv1_OS1
do 
    if [ $method == "sbmmcsprev1+o+eL1" ]; then
        method_name="SBM-MCS+eV1"
    elif [ $method == "sbmmcsprev1+o" ]; then
        method_name="SBM-MCS"
    elif [ $method == "abcdta4+o" ]; then
        method_name="ABCD-MCS"
    elif [ $method == "abcdta4+o+eL1" ]; then
        method_name="ABCD-MCS+eV1"
    elif [ $method == "sbm+o_" ]; then
        method_name="SBM"
    elif [ $method == "abcd+o" ]; then
        method_name="ABCD"
    elif [ $method == "RECCSv1_OS1" ]; then
        method_name="RECCS"
    else
        echo "Error: Unknown method"
        continue
    fi

    # python network_evaluation/compare_simulators_gt.py \
    #     --names \
    #         "${method_name} / SBM" \
    #         "${method_name} / SBM-CC" \
    #         "${method_name} / SBM-WCC" \
    #     --roots \
    #         data/stats/${method}/sbm \
    #         data/stats/${method}/sbm_cc \
    #         data/stats/${method}/sbm_wcc \
    #     --resolution \
    #         sbm \
    #         sbm \
    #         sbm \
    #     --stats \
    #         pseudo_diameter \
    #         local_ccoeff \
    #         global_ccoeff \
    #     --output-dir output/gt/diam/val_cl/${method}/sbm/ \
    #     --network-whitelist-fp data/networks_val.txt \
    #     --num-replicates 1 \
    #     --ncols 3

    # python network_evaluation/compare_simulators_gt.py \
    #     --names \
    #         "${method_name} / CPM(0.1)" \
    #         "${method_name} / CPM(0.01)" \
    #         "${method_name} / CPM(0.001)" \
    #         "${method_name} / Mod" \
    #     --roots \
    #         data/stats/${method}/leiden_cpm \
    #         data/stats/${method}/leiden_cpm \
    #         data/stats/${method}/leiden_cpm \
    #         data/stats/${method}/leiden_mod \
    #     --resolution \
    #         leiden.1 \
    #         leiden.01 \
    #         leiden.001 \
    #         leidenmod \
    #     --stats \
    #         pseudo_diameter \
    #         local_ccoeff \
    #         global_ccoeff \
    #     --output-dir output/gt/diam/val_cl/${method}/leiden/ \
    #     --network-whitelist-fp data/networks_val.txt \
    #     --num-replicates 1 \
    #     --ncols 4

    # python network_evaluation/compare_simulators_gt.py \
    #     --names \
    #         "${method_name} / CPM(0.1)+CM" \
    #         "${method_name} / CPM(0.01)+CM" \
    #         "${method_name} / CPM(0.001)+CM" \
    #         "${method_name} / Mod+CM" \
    #     --roots \
    #         data/stats/${method}/leiden_cpm_nofiltcm \
    #         data/stats/${method}/leiden_cpm_nofiltcm \
    #         data/stats/${method}/leiden_cpm_nofiltcm \
    #         data/stats/${method}/leiden_mod_nofiltcm \
    #     --resolution \
    #         leiden.1 \
    #         leiden.01 \
    #         leiden.001 \
    #         leidenmod \
    #     --stats \
    #         pseudo_diameter \
    #         local_ccoeff \
    #         global_ccoeff \
    #     --output-dir output/gt/diam/val_cl/${method}/leidencm/ \
    #     --network-whitelist-fp data/networks_val.txt \
    #     --num-replicates 1 \
    #     --ncols 4

    # python network_evaluation/compare_simulators_gt.py \
    #     --names \
    #         "${method_name} / CPM(0.1)" \
    #         "${method_name} / CPM(0.01)" \
    #         "${method_name} / CPM(0.001)" \
    #         "${method_name} / Mod" \
    #         "${method_name} / CPM(0.1) + CM" \
    #         "${method_name} / CPM(0.01) + CM" \
    #         "${method_name} / CPM(0.001) + CM" \
    #         "${method_name} / Mod + CM" \
    #         "${method_name} / SBM" \
    #         "${method_name} / SBM-CC" \
    #         "${method_name} / SBM-WCC" \
    #     --roots \
    #         data/stats/${method}/leiden_cpm \
    #         data/stats/${method}/leiden_cpm \
    #         data/stats/${method}/leiden_cpm \
    #         data/stats/${method}/leiden_mod \
    #         data/stats/${method}/leiden_cpm_nofiltcm \
    #         data/stats/${method}/leiden_cpm_nofiltcm \
    #         data/stats/${method}/leiden_cpm_nofiltcm \
    #         data/stats/${method}/leiden_mod_nofiltcm \
    #         data/stats/${method}/sbm \
    #         data/stats/${method}/sbm_cc \
    #         data/stats/${method}/sbm_wcc \
    #     --resolution \
    #         leiden.1 \
    #         leiden.01 \
    #         leiden.001 \
    #         leidenmod \
    #         leiden.1 \
    #         leiden.01 \
    #         leiden.001 \
    #         leidenmod \
    #         sbm \
    #         sbm \
    #         sbm \
    #     --stats \
    #         pseudo_diameter \
    #         local_ccoeff \
    #         global_ccoeff \
    #     --output-dir output/gt/diam/val_cl/${method}/leiden_leidencm_sbm/ \
    #     --network-whitelist-fp data/networks_val.txt \
    #     --num-replicates 1 \
    #     --ncols 3

    python network_evaluation/compare_simulators_gt.py \
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
            "${method_name} / IKC(10)" \
            "${method_name} / IKC(10)+CM" \
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
            k10 \
            k10 \
        --stats \
            pseudo_diameter \
            local_ccoeff \
            global_ccoeff \
        --output-dir output/gt/diam/val_cl/${method}/leiden_leidencm_sbm/ \
        --network-whitelist-fp data/networks_val.txt \
        --num-replicates 1 \
        --ncols 4
done

echo "Done"
