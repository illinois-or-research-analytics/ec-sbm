test_id=cit_hepph

if [ -d "test/output/${test_id}/" ]; then
    rm -rf test/output/${test_id}/
fi

bash scripts/run_ecsbm.sh \
    test/input/${test_id}/edge.tsv \
    test/input/${test_id}/com.tsv \
    test/output/${test_id}/

# ========================
# RECCS

# if [ -d "test/output/${test_id}/" ]; then
#     rm -rf test/output/${test_id}/
# fi

# python network_evaluation/compute_stats.py \
#     --input-network test/input/${test_id}/edge.dat \
#     --input-clustering test/input/${test_id}/com.dat \
#     --output-folder test/output/${test_id}/stats/orig/

# python network_evaluation/compute_gt_stats.py \
#     --input test/input/${test_id}/edge.dat \
#     --output test/output/${test_id}/stats/orig/

# python clean_outlier.py \
#     --input-network test/input/${test_id}/edge.dat \
#     --input-clustering test/input/${test_id}/com.dat \
#     --output-folder test/output/${test_id}/networks/orig_wo_o/

# python lanne2_networks/generate_synthetic_networks/gen_SBM.py \
#     -f test/output/${test_id}/networks/orig_wo_o/edge.dat \
#     -c test/input/${test_id}/com.dat \
#     -o test/output/${test_id}/networks/RECCSv1

# python lanne2_networks/generate_synthetic_networks/reccs.py \
#     -f test/output/${test_id}/networks/RECCSv1/syn_sbm.tsv \
#     -c test/input/${test_id}/com.dat \
#     -o test/output/${test_id}/networks/RECCSv1 \
#     -ef test/output/${test_id}/networks/orig_wo_o/edge.dat

# python lanne2_networks/generate_synthetic_networks/outliers_strategy1.py \
#     -f test/input/${test_id}/edge.dat \
#     -c test/input/${test_id}/com.dat \
#     -o test/output/${test_id}/networks/RECCSv1 \
#     -s test/output/${test_id}/networks/RECCSv1/ce_plusedges_v1.tsv

# python network_evaluation/compute_stats.py \
#     --input-network test/output/${test_id}/networks/RECCSv1/syn_o_un.tsv \
#     --input-clustering test/input/${test_id}/com.dat \
#     --output-folder test/output/${test_id}/stats/RECCSv1/

# python network_evaluation/compare_stats_pair.py \
#     --network-1-folder test/output/${test_id}/stats/orig/ \
#     --network-2-folder test/output/${test_id}/stats/RECCSv1/ \
#     --output-file test/output/${test_id}/stats/RECCSv1/compare_output.csv \
#     --is-compare-sequence

# python network_evaluation/compute_gt_stats.py \
#     --input test/output/${test_id}/networks/RECCSv1/syn_o_un.tsv \
#     --output test/output/${test_id}/stats/RECCSv1/

# python network_evaluation/compare_gt_stats_pair.py \
#     --network-1-folder test/output/${test_id}/stats/orig/ \
#     --network-2-folder test/output/${test_id}/stats/RECCSv1/ \
#     --output-file test/output/${test_id}/stats/RECCSv1/compare_gt_stats.csv