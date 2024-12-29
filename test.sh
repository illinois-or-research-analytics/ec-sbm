#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/test/slurm-%j.out
#SBATCH --job-name="test_compute"
#SBATCH --partition=secondary
#SBATCH --mem=128G

# ===================================

test_id=artist_edges
method=sbm
fixedge_method=L1

# ========================
# RECCS

rm -rf test/output/${test_id}/

python network_evaluation/compute_stats.py \
    --input-network test/input/${test_id}/edge.dat \
    --input-clustering test/input/${test_id}/com.dat \
    --output-folder test/output/${test_id}/stats/orig/

python network_evaluation/compute_gt_stats.py \
    --input test/input/${test_id}/edge.dat \
    --output test/output/${test_id}/stats/orig/

python clean_outlier.py \
    --input-network test/input/${test_id}/edge.dat \
    --input-clustering test/input/${test_id}/com.dat \
    --output-folder test/output/${test_id}/networks/orig_wo_o/

python lanne2_networks/generate_synthetic_networks/gen_SBM.py \
    -f test/output/${test_id}/networks/orig_wo_o/edge.dat \
    -c test/input/${test_id}/com.dat \
    -o test/output/${test_id}/networks/RECCSv1

python lanne2_networks/generate_synthetic_networks/reccs.py \
    -f test/output/${test_id}/networks/RECCSv1/syn_sbm.tsv \
    -c test/input/${test_id}/com.dat \
    -o test/output/${test_id}/networks/RECCSv1 \
    -ef test/output/${test_id}/networks/orig_wo_o/edge.dat

python lanne2_networks/generate_synthetic_networks/outliers_strategy1.py \
    -f test/input/${test_id}/edge.dat \
    -c test/input/${test_id}/com.dat \
    -o test/output/${test_id}/networks/RECCSv1 \
    -s test/output/${test_id}/networks/RECCSv1/ce_plusedges_v1.tsv

python network_evaluation/compute_stats.py \
    --input-network test/output/${test_id}/networks/RECCSv1/syn_o_un.tsv \
    --input-clustering test/input/${test_id}/com.dat \
    --output-folder test/output/${test_id}/stats/RECCSv1/

python network_evaluation/compare_stats_pair.py \
    --network-1-folder test/output/${test_id}/stats/orig/ \
    --network-2-folder test/output/${test_id}/stats/RECCSv1/ \
    --output-file test/output/${test_id}/stats/RECCSv1/compare_output.csv \
    --is-compare-sequence

python network_evaluation/compute_gt_stats.py \
    --input test/output/${test_id}/networks/RECCSv1/syn_o_un.tsv \
    --output test/output/${test_id}/stats/RECCSv1/

python network_evaluation/compare_gt_stats_pair.py \
    --network-1-folder test/output/${test_id}/stats/orig/ \
    --network-2-folder test/output/${test_id}/stats/RECCSv1/ \
    --output-file test/output/${test_id}/stats/RECCSv1/compare_gt_stats.csv

# ========================
# Fix edge at the end

# rm -rf test/output/${test_id}/

# python clean_outlier.py \
#     --input-network test/input/${test_id}/edge.dat \
#     --input-clustering test/input/${test_id}/com.dat \
#     --output-folder test/output/${test_id}/networks/orig_wo_o/

# python network_evaluation/compute_stats.py \
#     --input-network test/output/${test_id}/networks/orig_wo_o/edge.dat \
#     --input-clustering test/output/${test_id}/networks/orig_wo_o/com.dat \
#     --output-folder test/output/${test_id}/stats/orig_wo_o/

# python gen_${method}.py \
#     --edgelist test/output/${test_id}/networks/orig_wo_o/edge.dat \
#     --clustering test/output/${test_id}/networks/orig_wo_o/com.dat \
#     --output test/output/${test_id}/networks/${method}/

# python network_evaluation/compute_stats.py \
#     --input-network test/output/${test_id}/networks/${method}/edge.tsv \
#     --input-clustering test/output/${test_id}/networks/${method}/com.tsv \
#     --output-folder test/output/${test_id}/stats/${method}/

# python generate_outliers.py \
#     --orig-edgelist test/input/${test_id}/edge.dat \
#     --orig-clustering test/input/${test_id}/com.dat \
#     --output-folder test/output/${test_id}/networks/${method}+o/

# python combine_clustered_outliers.py \
#     --clustered-edgelist test/output/${test_id}/networks/${method}/edge.tsv \
#     --clustered-clustering test/output/${test_id}/networks/${method}/com.tsv \
#     --outlier-edgelist test/output/${test_id}/networks/${method}+o/outlier_edge.tsv \
#     --output-folder test/output/${test_id}/networks/${method}+o/

# python network_evaluation/compute_stats.py \
#     --input-network test/output/${test_id}/networks/${method}+o/edge.tsv \
#     --input-clustering test/output/${test_id}/networks/${method}+o/com.tsv \
#     --output-folder test/output/${test_id}/stats/${method}+o/

# # 

# python fix_degree_${fixedge_method}.py \
#     --orig-edgelist test/input/${test_id}/edge.dat \
#     --orig-clustering test/input/${test_id}/com.dat \
#     --exist-edgelist test/output/${test_id}/networks/${method}+o/edge.tsv \
#     --output-folder test/output/${test_id}/networks/${method}+o+e${fixedge_method}/

# python combine_clustered_outliers.py \
#     --clustered-edgelist test/output/${test_id}/networks/${method}+o/edge.tsv \
#     --clustered-clustering test/output/${test_id}/networks/${method}+o/com.tsv \
#     --outlier-edgelist test/output/${test_id}/networks/${method}+o+e${fixedge_method}/fix_edge.tsv \
#     --output-folder test/output/${test_id}/networks/${method}+o+e${fixedge_method}/

# python network_evaluation/compute_stats.py \
#     --input-network test/output/${test_id}/networks/${method}+o+e${fixedge_method}/edge.tsv \
#     --input-clustering test/output/${test_id}/networks/${method}+o+e${fixedge_method}/com.tsv \
#     --output-folder test/output/${test_id}/stats/${method}+o+e${fixedge_method}/

# # 

# python network_evaluation/compute_stats.py \
#     --input-network test/input/${test_id}/edge.dat \
#     --input-clustering test/input/${test_id}/com.dat \
#     --output-folder test/output/${test_id}/stats/orig/

# python network_evaluation/compare_stats_pair.py \
#     --network-1-folder test/output/${test_id}/stats/orig/ \
#     --network-2-folder test/output/${test_id}/stats/${method}+o/ \
#     --output-file test/output/${test_id}/stats/${method}+o/compare_output.csv \
#     --is-compare-sequence

# python network_evaluation/compare_stats_pair.py \
#     --network-1-folder test/output/${test_id}/stats/orig/ \
#     --network-2-folder test/output/${test_id}/stats/${method}+o+e${fixedge_method}/ \
#     --output-file test/output/${test_id}/stats/${method}+o+e${fixedge_method}/compare_output.csv \
#     --is-compare-sequence

# ========================
# Fix edge after clustered network

# rm -rf test/output/${test_id}/

# python clean_outlier.py \
#     --input-network test/input/${test_id}/edge.dat \
#     --input-clustering test/input/${test_id}/com.dat \
#     --output-folder test/output/${test_id}/orig_wo_o/

# python gen_sbmmcsprev1.py \
#     --edgelist test/output/${test_id}/orig_wo_o/edge.dat \
#     --clustering test/output/${test_id}/orig_wo_o/com.dat \
#     --output test/output/${test_id}/${method}/

# python fix_edge.py \
#     --orig-edgelist test/output/${test_id}/orig_wo_o/edge.dat \
#     --orig-clustering test/output/${test_id}/orig_wo_o/com.dat \
#     --exist-edgelist test/output/${test_id}/${method}/edge.tsv \
#     --output-folder test/output/${test_id}/${method}+e/

# python combine_clustered_outliers.py \
#     --clustered-edgelist test/output/${test_id}/${method}/edge.tsv \
#     --clustered-clustering test/output/${test_id}/${method}/com.tsv \
#     --outlier-edgelist test/output/${test_id}/${method}+e/fix_edge.tsv \
#     --output-folder test/output/${test_id}/${method}+e/

# python generate_outliers.py \
#     --orig-edgelist test/input/${test_id}/edge.dat \
#     --orig-clustering test/input/${test_id}/com.dat \
#     --output-folder test/output/${test_id}/${method}+o/

# python combine_clustered_outliers.py \
#     --clustered-edgelist test/output/${test_id}/${method}+e/edge.tsv \
#     --clustered-clustering test/output/${test_id}/${method}+e/com.tsv \
#     --outlier-edgelist test/output/${test_id}/${method}+o/outlier_edge.tsv \
#     --output-folder test/output/${test_id}/${method}+e+o/