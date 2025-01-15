#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/clusterings/slurm-%j.out
#SBATCH --job-name="compare_clustering"
#SBATCH --partition=secondary
#SBATCH --mem=8G

python network_evaluation/compare_simulators_gt.py \
    --names \
        "SBM / SBM-WCC" \
        "RECCS / SBM-WCC" \
        "Chambana / SBM-WCC" \
    --roots \
        data/stats/sbm+o/sbm_wcc \
        data/stats/RECCSv1_OS1/sbm_wcc \
        data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
    --resolution \
        sbm \
        sbm \
        sbm \
    --stats \
        pseudo_diameter \
        local_ccoeff \
        global_ccoeff \
        char_time \
    --output-dir output/compare/val/per_clustering/sbm_reccs_sbmmcs+e/best \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 3

python network_evaluation/compare_simulators_gt.py \
    --names \
        "SBM / SBM-WCC" \
        "SBM / Leiden-Mod+CM" \
        "RECCS / SBM-WCC" \
        "RECCS / Leiden-Mod+CM" \
        "Chambana / SBM-WCC" \
        "Chambana / Leiden-Mod+CM" \
    --roots \
        data/stats/sbm+o/sbm_wcc \
        data/stats/sbm+o/leiden_mod_nofiltcm \
        data/stats/RECCSv1_OS1/sbm_wcc \
        data/stats/RECCSv1_OS1/leiden_mod_nofiltcm \
        data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
        data/stats/sbmmcsprev1+o+eL1/leiden_mod_nofiltcm \
    --resolution \
        sbm \
        leidenmod \
        sbm \
        leidenmod \
        sbm \
        leidenmod \
    --stats \
        pseudo_diameter \
        local_ccoeff \
        global_ccoeff \
        char_time \
    --output-dir output/compare/val/per_clustering/sbm_reccs_sbmmcs+e/best_2ndbest \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 3

# python network_evaluation/compare_simulators_gt.py \
#     --names \
#         "SBM / SBM-WCC" \
#         "SBM-MCS / SBM-WCC" \
#         "SBM-MCS+e / SBM-WCC" \
#         "RECCS / SBM-WCC" \
#     --roots \
#         data/stats/sbm+o/sbm_wcc \
#         data/stats/sbmmcsprev1+o/sbm_wcc \
#         data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#         data/stats/RECCSv1_OS1/sbm_wcc \
#     --resolution \
#         sbm \
#         sbm \
#         sbm \
#         sbm \
#     --stats \
#         pseudo_diameter \
#         local_ccoeff \
#         global_ccoeff \
#         char_time \
#     --output-dir output/compare/val_small/per_clustering/sbm_sbmmcs_sbmmcs+e_reccs/best \
#     --network-whitelist-fp data/networks_val_small.txt \
#     --num-replicates 1 \
#     --ncols 2

# python network_evaluation/compare_simulators_gt.py \
#     --names \
#         "SBM / SBM-CC" \
#         "SBM / SBM-WCC" \
#         "SBM-MCS / SBM-WCC" \
#         "SBM-MCS+e / SBM-WCC" \
#         "RECCS / SBM-WCC" \
#     --roots \
#         data/stats/sbm+o/sbm_cc \
#         data/stats/sbm+o/sbm_wcc \
#         data/stats/sbmmcsprev1+o/sbm_wcc \
#         data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#         data/stats/RECCSv1_OS1/sbm_wcc \
#     --resolution \
#         sbm \
#         sbm \
#         sbm \
#         sbm \
#         sbm \
#     --stats \
#         pseudo_diameter \
#         local_ccoeff \
#         global_ccoeff \
#         char_time \
#     --output-dir output/compare/val_medium/per_clustering/sbm_sbmmcs_sbmmcs+e_reccs/best/ \
#     --network-whitelist-fp data/networks_val_medium.txt \
#     --num-replicates 1 \
#     --ncols 3

# python network_evaluation/compare_simulators_gt.py \
#     --names \
#         "SBM / Leiden-Mod+CM" \
#         "SBM / SBM-WCC" \
#         "SBM-MCS / Leiden-Mod+CM" \
#         "SBM-MCS / SBM-WCC" \
#         "SBM-MCS+e / SBM-WCC" \
#         "RECCS / Leiden-Mod+CM" \
#     --roots \
#         data/stats/sbm+o/leiden_mod_nofiltcm \
#         data/stats/sbm+o/sbm_wcc \
#         data/stats/sbmmcsprev1+o/leiden_mod_nofiltcm \
#         data/stats/sbmmcsprev1+o/sbm_wcc \
#         data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
#         data/stats/RECCSv1_OS1/leiden_mod_nofiltcm \
#     --resolution \
#         leidenmod \
#         sbm \
#         leidenmod \
#         sbm \
#         sbm \
#         leidenmod \
#     --stats \
#         pseudo_diameter \
#         local_ccoeff \
#         global_ccoeff \
#         char_time \
#     --output-dir output/compare/val_large/per_clustering/sbm_sbmmcs_sbmmcs+e_reccs/best/ \
#     --network-whitelist-fp data/networks_val_large.txt \
#     --num-replicates 1 \
#     --ncols 3

for split in val
do
    for method in sbm+o sbmmcsprev1+o sbmmcsprev1+o+eL1 RECCSv1_OS1 # abcd+o abcdta4+o abcdta4+o+eL1
    do 
        if [ $method == "sbmmcsprev1+o+eL1" ]; then
            method_name="SBM-MCS+e"
        elif [ $method == "sbmmcsprev1+o" ]; then
            method_name="SBM-MCS"
        elif [ $method == "abcdta4+o" ]; then
            method_name="ABCD-MCS"
        elif [ $method == "abcdta4+o+eL1" ]; then
            method_name="ABCD-MCS+e"
        elif [ $method == "sbm+o" ]; then
            method_name="SBM"
        elif [ $method == "abcd+o" ]; then
            method_name="ABCD"
        elif [ $method == "RECCSv1_OS1" ]; then
            method_name="RECCS"
        else
            echo "Error: Unknown method"
            continue
        fi

        python network_evaluation/compare_simulators_gt.py \
            --names \
                "Leiden-CPM(0.1)" \
                "Leiden-CPM(0.01)" \
                "Leiden-CPM(0.001)" \
                "Leiden-Mod" \
                "Leiden-CPM(0.1)+CM" \
                "Leiden-CPM(0.01)+CM" \
                "Leiden-CPM(0.001)+CM" \
                "Leiden-Mod+CM" \
                "SBM" \
                "SBM-CC" \
                "SBM-WCC" \
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
            --stats \
                pseudo_diameter \
                local_ccoeff \
                global_ccoeff \
                char_time \
            --output-dir output/compare/${split}/per_sim/${method}/leiden_leidencm_sbm/ \
            --network-whitelist-fp data/networks_${split}.txt \
            --num-replicates 1 \
            --ncols 3
    done

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
    #                 pseudo_diameter \
    #                 local_ccoeff \
    #                 global_ccoeff \
    #                 char_time \
    #             --output-dir output/compare/${split}/per_clustering/sbm_sbmmcs_sbmmcs+e_reccs/${clustering}/${resolution}/ \
    #             --network-whitelist-fp data/networks_${split}.txt \
    #             --num-replicates 1 \
    #             --ncols 4
    #     done
    # done
done

echo "Done"
