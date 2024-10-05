test_id=discogs_label
method=sbmmcsprev1

# ========================
# Fix edge at the end

rm -rf test/output/${test_id}/

python clean_outlier.py \
    --input-network test/input/${test_id}/edge.dat \
    --input-clustering test/input/${test_id}/com.dat \
    --output-folder test/output/${test_id}/orig_wo_o/

python gen_sbmmcsprev1.py \
    --edgelist test/output/${test_id}/orig_wo_o/edge.dat \
    --clustering test/output/${test_id}/orig_wo_o/com.dat \
    --output test/output/${test_id}/${method}/

python generate_outliers.py \
    --orig-edgelist test/input/${test_id}/edge.dat \
    --orig-clustering test/input/${test_id}/com.dat \
    --output-folder test/output/${test_id}/${method}+o/

python combine_clustered_outliers.py \
    --clustered-edgelist test/output/${test_id}/${method}/edge.tsv \
    --clustered-clustering test/output/${test_id}/${method}/com.tsv \
    --outlier-edgelist test/output/${test_id}/${method}+o/outlier_edge.tsv \
    --output-folder test/output/${test_id}/${method}+o/

python fix_edge.py \
    --orig-edgelist test/input/${test_id}/edge.dat \
    --orig-clustering test/input/${test_id}/com.dat \
    --exist-edgelist test/output/${test_id}/${method}+o/edge.tsv \
    --output-folder test/output/${test_id}/${method}+o+e/

python combine_clustered_outliers.py \
    --clustered-edgelist test/output/${test_id}/${method}+o/edge.tsv \
    --clustered-clustering test/output/${test_id}/${method}+o/com.tsv \
    --outlier-edgelist test/output/${test_id}/${method}+o+e/fix_edge.tsv \
    --output-folder test/output/${test_id}/${method}+o+e/

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