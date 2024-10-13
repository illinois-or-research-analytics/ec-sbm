#!/bin/bash
#SBATCH --time=15-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/benchmark/slurm-%j.out
#SBATCH --job-name="benchmark_oc"
#SBATCH --partition=tallis
#SBATCH --mem=512G

# ===================================

method="sbmmcsprev1"
network="oc"
clustering="leiden_cpm_cm"
resolution="leiden.001"

orig_edgelist_fp="data/benchmark/input/${network}/S1_${network}_cleanup.tsv"
edgelist_fp="data/benchmark/input/${network}/${clustering}/${resolution}/edge.dat"
clustering_fp="data/benchmark/input/${network}/${clustering}/${resolution}/com.dat"

clustered_output_dir="data/benchmark/output/${network}/${clustering}/${resolution}/${method}/"
outlier_output_dir="data/benchmark/output/${network}/${clustering}/${resolution}/${method}+o/"

# python gen_${method}.py \
#     --edgelist ${edgelist_fp} \
#     --clustering ${clustering_fp} \
#     --output-folder ${clustered_output_dir}

# python generate_outliers.py \
#     --orig-edgelist ${orig_edgelist_fp} \
#     --orig-clustering ${clustering_fp} \
#     --output-folder ${outlier_output_dir}

# python combine_clustered_outliers.py \
#     --clustered-edgelist ${clustered_output_dir}/edge.tsv \
#     --clustered-clustering ${clustered_output_dir}/com.tsv \
#     --outlier-edgelist ${outlier_output_dir}/outlier_edge.tsv \
#     --output-folder ${outlier_output_dir}

fixedge_method="L1"
fixedge_output_dir="data/benchmark/output/${network}/${clustering}/${resolution}/${method}+o+e${fixedge_method}/"

python fix_degree_${fixedge_method}.py \
    --orig-edgelist ${orig_edgelist_fp} \
    --orig-clustering ${clustering_fp} \
    --exist-edgelist ${outlier_output_dir}/edge.tsv \
    --output-folder ${fixedge_output_dir}