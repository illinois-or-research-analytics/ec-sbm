#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/clusterings/slurm-%j.out
#SBATCH --job-name="compare_clustering"
#SBATCH --partition=secondary
#SBATCH --mem=8G

python network_evaluation/compare_simulators_all.py \
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
        global_ccoeff \
        char_time \
        degree \
    --output-dir output/compare/val/per_clustering/sbm_reccs_sbmmcs+e/best_2ndbest \
    --prefix network \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 3

python network_evaluation/compare_simulators_all.py \
    --names \
        "SBM / SBM" \
        "SBM / SBM-WCC" \
        "SBM / Leiden-Mod+CM" \
        "RECCS / SBM" \
        "RECCS / SBM-WCC" \
        "RECCS / Leiden-Mod+CM" \
        "Chambana / SBM" \
        "Chambana / SBM-WCC" \
        "Chambana / Leiden-Mod+CM" \
    --roots \
        data/stats/sbm+o/sbm \
        data/stats/sbm+o/sbm_wcc \
        data/stats/sbm+o/leiden_mod_nofiltcm \
        data/stats/RECCSv1_OS1/sbm \
        data/stats/RECCSv1_OS1/sbm_wcc \
        data/stats/RECCSv1_OS1/leiden_mod_nofiltcm \
        data/stats/sbmmcsprev1+o+eL1/sbm \
        data/stats/sbmmcsprev1+o+eL1/sbm_wcc \
        data/stats/sbmmcsprev1+o+eL1/leiden_mod_nofiltcm \
    --resolution \
        sbm \
        sbm \
        leidenmod \
        sbm \
        sbm \
        leidenmod \
        sbm \
        sbm \
        leidenmod \
    --stats \
        pseudo_diameter \
        global_ccoeff \
        char_time \
        degree \
    --output-dir output/compare/val/per_clustering/sbm_reccs_sbmmcs+e/best_2ndbest_sbm \
    --prefix network \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 3

python network_evaluation/compare_simulators_all.py \
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
        mincuts \
        c_edges \
        mixing_mus \
        o_deg \
    --output-dir output/compare/val/per_clustering/sbm_reccs_sbmmcs+e/best \
    --prefix cluster \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 3

python network_evaluation/compare_simulators_all.py \
    --names \
        "SBM / Leiden-Mod+CM" \
        "RECCS / Leiden-Mod+CM" \
        "Chambana / Leiden-Mod+CM" \
    --roots \
        data/stats/sbm+o/leiden_mod_nofiltcm \
        data/stats/RECCSv1_OS1/leiden_mod_nofiltcm \
        data/stats/sbmmcsprev1+o+eL1/leiden_mod_nofiltcm \
    --resolution \
        leidenmod \
        leidenmod \
        leidenmod \
    --stats \
        mincuts \
        c_edges \
        mixing_mus \
        o_deg \
    --output-dir output/compare/val/per_clustering/sbm_reccs_sbmmcs+e/2ndbest \
    --prefix cluster \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 3

python network_evaluation/compare_simulators_all.py \
    --names \
        "SBM / SBM" \
        "RECCS / SBM" \
        "Chambana / SBM" \
    --roots \
        data/stats/sbm+o/sbm \
        data/stats/RECCSv1_OS1/sbm \
        data/stats/sbmmcsprev1+o+eL1/sbm \
    --resolution \
        sbm \
        sbm \
        sbm \
    --stats \
        mincuts \
        c_edges \
        mixing_mus \
        o_deg \
    --output-dir output/compare/val/per_clustering/sbm_reccs_sbmmcs+e/sbm \
    --prefix cluster \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 3

for split in val
do
    for method in sbm+o sbmmcsprev1+o+eL1 RECCSv1_OS1 # abcd+o abcdta4+o abcdta4+o+eL1
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

        python network_evaluation/compare_simulators_all.py \
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
                global_ccoeff \
                char_time \
                degree \
            --output-dir output/compare/${split}/per_sim/${method}/leiden_leidencm_sbm \
            --prefix network \
            --network-whitelist-fp data/networks_${split}.txt \
            --num-replicates 1 \
            --ncols 3

        python network_evaluation/compare_simulators_all.py \
            --names \
                "Leiden-CPM(0.1)" \
                "Leiden-CPM(0.01)" \
                "Leiden-CPM(0.001)" \
                "Leiden-Mod" \
                "Leiden-CPM(0.1)+CM" \
                "Leiden-CPM(0.01)+CM" \
                "Leiden-CPM(0.001)+CM" \
                "Leiden-Mod+CM" \
                "InfoMap-CC" \
                "InfoMap+CM" \
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
                data/stats/${method}/infomap_cc \
                data/stats/${method}/infomap_nofiltcm \
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
                infomap \
                infomap \
                sbm \
                sbm \
            --stats \
                pseudo_diameter \
                global_ccoeff \
                char_time \
                degree \
            --output-dir output/compare/${split}/per_sim/${method}/leiden_leidencm_infomap_sbm \
            --prefix network \
            --network-whitelist-fp data/networks_${split}.txt \
            --num-replicates 1 \
            --ncols 3
    done
done

echo "Done"
