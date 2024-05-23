#!/bin/bash
#SBATCH --time=72:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="gen_network"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

network_id=cit_hepph
resolution=.001
method=abcd
based_on=leiden_cpm_cm
seed=0

edgelist_fn="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/edge.dat"
clustering_fn="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/com.dat"
output_dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/${seed}/"

python gen_${method}.py \
    --edgelist ${edgelist_fn} \
    --clustering ${clustering_fn} \
    --output-folder ${output_dir} \
    --seed ${seed}

python network_evaluation/compute_stats.py \
    --input-network ${output_dir}/edge.tsv \
    --input-clustering ${output_dir}/com.tsv \
    --output-folder ${output_dir} \
    --overwrite

python compute_connectivity.py \
    --network-folder ${output_dir} \
    --output-folder ${output_dir}

python compute_degree_dist.py \
    --network-folder ${output_dir} \
    --output-folder ${output_dir}

if [ $method = "abcdta4" ]; then
    python compute_cluster_stats.py \
        --network-folder ${output_dir} \
        --output-folder ${output_dir} \
        --is-with-bijection
else
    python compute_cluster_stats.py \
        --network-folder ${output_dir} \
        --output-folder ${output_dir}
fi

# ===================================

# for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
# do
#     for network_id in wiki_topcats #cit_hepph cit_patents wiki_topcats wiki_talk orkut
#     do
#         for resolution in .0001 .001 .01 #.0001 .001 .01
#         do
#             for method in abcdta4 abcd #abcd abcdta4
#             do
#                 seed=0

#                 dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/${seed}/"

#                 echo "=================================="
#                 echo $dir

#                 python gen_${method}.py \
#                     --network-id ${network_id} \
#                     --resolution $resolution \
#                     --method ${method} \
#                     --based_on ${based_on} \
#                     --seed ${seed}

#                 # python compute_stats.py \
#                 #     --network-id ${network_id} \
#                 #     --resolution $resolution \
#                 #     --method ${method} \
#                 #     --based_on ${based_on} \
#                 #     --seed ${seed}
#                 # python emulate-real-nets/estimate_properties_networkit.py \
#                 #     -n "${dir}/edge.tsv" \
#                 #     -c "${dir}/com.tsv" \
#                 #     -o "${dir}/stats.json"

#                 python compute_degree_dist.py \
#                     --network-id ${network_id} \
#                     --resolution $resolution \
#                     --method ${method} \
#                     --based_on ${based_on} \
#                     --seed ${seed}
                    
#                 python compute_cluster_stats.py \
#                     --network-id ${network_id} \
#                     --resolution $resolution \
#                     --method ${method} \
#                     --based_on ${based_on} \
#                     --seed ${seed}

#                 echo "=================================="
#                 echo ""
#             done
#         done
#     done
# done

# ===================================