# start=0
# end=0

# for network_id in $(cat data/networks_val.txt)
# do
#     echo "============================================"
#     echo $network_id
#     for seed in $(seq ${start} ${end})
#     do
#         python network_evaluation/compare_stats_pair.py \
#             --network-1-folder data/stats/sbmmcsprev1+o+eL1/sbm_wcc/${network_id}/sbm/${seed} \
#             --network-2-folder data/stats/sbmmcsprev1+o+eL1/leiden_mod_nofiltcm/${network_id}/leidenmod/${seed} \
#             --output-file output/sbmwcc_leidenmodcm/${network_id}/${seed}/compare_output.csv \
#             --is-compare-sequence

#         python network_evaluation/compare_gt_stats_pair.py \
#             --network-1-folder data/stats/sbmmcsprev1+o+eL1/sbm_wcc/${network_id}/sbm/${seed} \
#             --network-2-folder data/stats/sbmmcsprev1+o+eL1/leiden_mod_nofiltcm/${network_id}/leidenmod/${seed} \
#             --output-file output/sbmwcc_leidenmodcm/${network_id}/${seed}/compare_gt_stats.csv
#     done
# done

python network_evaluation/compare_simulators_gt.py \
    --names \
        "SBM-MCS+e / Leiden-Mod+CM" \
    --roots \
        output/sbmwcc_leidenmodcm/ \
    --resolution \
        "" \
    --stats \
        pseudo_diameter \
        local_ccoeff \
        global_ccoeff \
        char_time \
    --output-dir output/sbmwcc_leidenmodcm_comp/ \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 1

python network_evaluation/compare_simulators_clstats.py \
    --names \
        "SBM-MCS+e / Leiden-Mod+CM" \
    --roots \
        output/sbmwcc_leidenmodcm/ \
    --resolution \
        "" \
    --stats \
        mincuts \
        c_edges \
        degree \
        mixing_mus \
    --output-dir output/sbmwcc_leidenmodcm_comp/ \
    --network-whitelist-fp data/networks_val.txt \
    --num-replicates 1 \
    --ncols 1