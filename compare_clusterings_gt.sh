#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/clusterings/slurm-%j.out
#SBATCH --job-name="compare_clustering"
#SBATCH --partition=tallis
#SBATCH --mem=8G

# python network_evaluation/compare_simulators_gt.py \
#     --names \
#         "SBM-MCS+e / SBM-WCC" \
#         "SBM-MCS+e / Mod+CM" \
#         "ABCD-MCS / SBM-WCC" \
#         "ABCD-MCS / Mod+CM" \
#         "RECCS / SBM-WCC" \
#         "RECCS / Mod+CM" \
#     --roots \
#         data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#         data/stats/sbmmcsprev1+o+eL1/leiden_mod_nofiltcm \
#         data/stats/abcdta4+o/sbm_wcc \
#         data/stats/abcdta4+o/leiden_mod_nofiltcm \
#         data/stats/RECCSv1_OS1/sbm_wcc \
#         data/stats/RECCSv1_OS1/leiden_mod_nofiltcm \
#     --resolution \
#         sbm \
#         leidenmod \
#         sbm \
#         leidenmod \
#         sbm \
#         leidenmod \
#     --stats \
#         n_edges \
#         pseudo_diameter \
#         local_ccoeff \
#         global_ccoeff \
#         char_time \
#     --output-dir output/gt/comp/sbmmcs+e_abcdmcs_reccs/sbmwcc_modcm/ \
#     --network-whitelist-fp data/networks_val.txt \
#     --num-replicates 1 \
#     --ncols 3

# for method in sbm+o sbmmcsprev1+o sbmmcsprev1+o+eL1 RECCSv1_OS1 # abcd+o abcdta4+o abcdta4+o+eL1
# do 
#     if [ $method == "sbmmcsprev1+o+eL1" ]; then
#         method_name="SBM-MCS+e"
#     elif [ $method == "sbmmcsprev1+o" ]; then
#         method_name="SBM-MCS"
#     elif [ $method == "abcdta4+o" ]; then
#         method_name="ABCD-MCS"
#     elif [ $method == "abcdta4+o+eL1" ]; then
#         method_name="ABCD-MCS+e"
#     elif [ $method == "sbm+o" ]; then
#         method_name="SBM"
#     elif [ $method == "abcd+o" ]; then
#         method_name="ABCD"
#     elif [ $method == "RECCSv1_OS1" ]; then
#         method_name="RECCS"
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
#             local_ccoeff \
#             global_ccoeff \
#             char_time \
#         --output-dir output/gt/per_sim/${method}/leiden_leidencm_sbm/ \
#         --network-whitelist-fp data/networks_val.txt \
#         --num-replicates 1 \
#         --ncols 3
# done

python network_evaluation/compare_simulators_gt.py \
    --names \
        "SBM" \
        "SBM-MCS" \
        "SBM-MCS+e" \
        "RECCS" \
    --roots \
        data/stats/sbm+o/sbm_wcc \
        data/stats/sbmmcsprev1+o/sbm_wcc \
        data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
        data/stats/RECCSv1_OS1/sbm_wcc \
    --resolution \
        sbm \
        sbm \
        sbm \
        sbm \
    --stats \
        pseudo_diameter \
        char_time \
        local_ccoeff \
        global_ccoeff \
    --output-dir output/gt/per_clustering/sbm_sbmmcs_sbmmcs+e_reccs/sbm_wcc/sbm/diam_tau/ \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 4

python network_evaluation/compare_simulators_gt.py \
    --names \
        "SBM" \
        "SBM-MCS" \
        "SBM-MCS+e" \
        "RECCS" \
    --roots \
        data/stats/sbm+o/leiden_cpm_nofiltcm \
        data/stats/sbmmcsprev1+o/leiden_cpm_nofiltcm \
        data/stats/sbmmcsprev1+o+eL1/leiden_cpm_nofiltcm \
        data/stats/RECCSv1_OS1/leiden_cpm_nofiltcm \
    --resolution \
        leiden.1 \
        leiden.1 \
        leiden.1 \
        leiden.1 \
    --stats \
        pseudo_diameter \
        char_time \
        local_ccoeff \
        global_ccoeff \
    --output-dir output/gt/per_clustering/sbm_sbmmcs_sbmmcs+e_reccs/leiden_cpm_nofiltcm/leiden.1/ccoeff/ \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 4

# for clustering in sbm sbm_cc sbm_wcc leiden_cpm leiden_cpm_nofiltcm leiden_mod leiden_mod_nofiltcm ikc_cc ikc_nofiltcm infomap_cc infomap_nofiltcm
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

#         # python network_evaluation/compare_simulators_gt.py \
#         #     --names \
#         #         "SBM" \
#         #         "ABCD" \
#         #     --roots \
#         #         data/stats/sbm+o/${clustering} \
#         #         data/stats/abcd+o/${clustering} \
#         #     --resolution \
#         #         ${resolution} \
#         #         ${resolution} \
#         #     --stats \
#         #         n_edges \
#         #         pseudo_diameter \
#         #         local_ccoeff \
#         #         global_ccoeff \
#         #         char_time \
#         #     --output-dir output/gt/per_clustering/sbm_abcd/${clustering}/${resolution}/ \
#         #     --network-whitelist-fp data/networks_val.txt \
#         #     --num-replicates 1 \
#         #     --ncols 2
        
#         # python network_evaluation/compare_simulators_gt.py \
#         #     --names \
#         #         "ABCD" \
#         #         "ABCD-MCS" \
#         #         "ABCD-MCS+e" \
#         #     --roots \
#         #         data/stats/abcd+o/${clustering} \
#         #         data/stats/abcdta4+o/${clustering} \
#         #         data/stats/abcdta4+o+eL1/${clustering} \
#         #     --resolution \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #     --stats \
#         #         n_edges \
#         #         pseudo_diameter \
#         #         local_ccoeff \
#         #         global_ccoeff \
#         #         char_time \
#         #     --output-dir output/gt/per_clustering/abcd_abcdmcs_abcdmcs+e/${clustering}/${resolution}/ \
#         #     --network-whitelist-fp data/networks_val.txt \
#         #     --num-replicates 1 \
#         #     --ncols 3
        
#         # python network_evaluation/compare_simulators_gt.py \
#         #     --names \
#         #         "SBM" \
#         #         "SBM-MCS" \
#         #         "SBM-MCS+e" \
#         #     --roots \
#         #         data/stats/sbm+o/${clustering} \
#         #         data/stats/sbmmcsprev1+o/${clustering} \
#         #         data/stats/sbmmcsprev1+o+eL1/${clustering} \
#         #     --resolution \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #     --stats \
#         #         n_edges \
#         #         pseudo_diameter \
#         #         local_ccoeff \
#         #         global_ccoeff \
#         #         char_time \
#         #     --output-dir output/gt/per_clustering/sbm_sbmmcs_sbmmcs+e/${clustering}/${resolution}/ \
#         #     --network-whitelist-fp data/networks_val.txt \
#         #     --num-replicates 1 \
#         #     --ncols 3

#         python network_evaluation/compare_simulators_gt.py \
#             --names \
#                 "SBM" \
#                 "SBM-MCS" \
#                 "SBM-MCS+e" \
#                 "RECCS" \
#             --roots \
#                 data/stats/sbm+o/${clustering} \
#                 data/stats/sbmmcsprev1+o/${clustering} \
#                 data/stats/sbmmcsprev1+o+eL1/${clustering} \
#                 data/stats/RECCSv1_OS1/${clustering} \
#             --resolution \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#                 ${resolution} \
#             --stats \
#                 n_edges \
#                 pseudo_diameter \
#                 local_ccoeff \
#                 global_ccoeff \
#                 char_time \
#             --output-dir output/gt/per_clustering/sbm_sbmmcs_sbmmcs+e_reccs/${clustering}/${resolution}/ \
#             --network-whitelist-fp data/networks_val.txt \
#             --num-replicates 1 \
#             --ncols 4

#         # python network_evaluation/compare_simulators_gt.py \
#         #     --names \
#         #         "SBM-MCS" \
#         #         "SBM-MCS+e" \
#         #         "ABCD-MCS" \
#         #         "ABCD-MCS+e" \
#         #         "RECCS" \
#         #     --roots \
#         #         data/stats/sbmmcsprev1+o/${clustering} \
#         #         data/stats/sbmmcsprev1+o+eL1/${clustering} \
#         #         data/stats/abcdta4+o/${clustering} \
#         #         data/stats/abcdta4+o+eL1/${clustering} \
#         #         data/stats/RECCSv1_OS1/${clustering} \
#         #     --resolution \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #     --stats \
#         #         n_edges \
#         #         pseudo_diameter \
#         #         local_ccoeff \
#         #         global_ccoeff \
#         #         char_time \
#         #     --output-dir output/gt/per_clustering/sbmmcs_sbmmcs+e_abcdmcs_abcdmcs+e_reccs/${clustering}/${resolution}/ \
#         #     --network-whitelist-fp data/networks_val.txt \
#         #     --num-replicates 1 \
#         #     --ncols 3

#         # python network_evaluation/compare_simulators_gt.py \
#         #     --names \
#         #         "SBM-MCS+e" \
#         #         "ABCD-MCS" \
#         #         "RECCS" \
#         #     --roots \
#         #         data/stats/sbmmcsprev1+o+eL1/${clustering} \
#         #         data/stats/abcdta4+o/${clustering} \
#         #         data/stats/RECCSv1_OS1/${clustering} \
#         #     --resolution \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #     --stats \
#         #         n_edges \
#         #         pseudo_diameter \
#         #         local_ccoeff \
#         #         global_ccoeff \
#         #         char_time \
#         #     --output-dir output/gt/per_clustering/sbmmcs+e_abcdmcs_reccs/${clustering}/${resolution}/ \
#         #     --network-whitelist-fp data/networks_val.txt \
#         #     --num-replicates 1 \
#         #     --ncols 3

#         # python network_evaluation/compare_simulators_gt.py \
#         #     --names \
#         #         "SBM" \
#         #         "SBM-MCS+e" \
#         #         "ABCD" \
#         #         "ABCD-MCS" \
#         #         "RECCS" \
#         #     --roots \
#         #         data/stats/sbm+o/${clustering} \
#         #         data/stats/sbmmcsprev1+o+eL1/${clustering} \
#         #         data/stats/abcd+o/${clustering} \
#         #         data/stats/abcdta4+o/${clustering} \
#         #         data/stats/RECCSv1_OS1/${clustering} \
#         #     --resolution \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #         ${resolution} \
#         #     --stats \
#         #         n_edges \
#         #         pseudo_diameter \
#         #         local_ccoeff \
#         #         global_ccoeff \
#         #         char_time \
#         #     --output-dir output/gt/per_clustering/sbm_sbmmcs+e_abcd_abcdmcs_reccs/${clustering}/${resolution}/ \
#         #     --network-whitelist-fp data/networks_val.txt \
#         #     --num-replicates 1 \
#         #     --ncols 3
#     done
# done

echo "Done"
