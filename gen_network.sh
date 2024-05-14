#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="gen_network"
#SBATCH --partition=eng-research-gpu
#SBATCH --mem=64G
#SBATCH --dependency=afterok:11131429

# ===================================

# network_id=cit_hepph
# resolution=.001
# method=abcdta4
# based_on=leiden_cpm_cm
# seed=0

# dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/${seed}/"

# python gen_${method}.py \
#     --network-id ${network_id} \
#     --resolution $resolution \
#     --method ${method} \
#     --based_on ${based_on} \
#     --seed ${seed}
# python compute_stats.py \
#     --network-id ${network_id} \
#     --resolution $resolution \
#     --method ${method} \
#     --based_on ${based_on} \
#     --seed ${seed}
# python emulate-real-nets/estimate_properties_networkit.py \
#     -n "${dir}/edge.tsv" \
#     -c "${dir}/com.tsv" \
#     -o "${dir}/stats.json"
# python compute_degree_dist.py \
#     --network-id ${network_id} \
#     --resolution $resolution \
#     --method ${method} \
#     --based_on ${based_on} \
#     --seed ${seed}
# python compute_cluster_stats.py \
#     --network-id ${network_id} \
#     --resolution $resolution \
#     --method ${method} \
#     --based_on ${based_on} \
#     --seed ${seed}

# ===================================

for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
do
    for network_id in wiki_topcats #cit_hepph cit_patents wiki_topcats wiki_talk orkut
    do
        for resolution in .0001 .001 .01 #.0001 .001 .01
        do
            for method in abcdta4 abcd #abcd abcdta4
            do
                seed=0

                dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/${seed}/"

                echo "=================================="
                echo $dir

                python gen_${method}.py \
                    --network-id ${network_id} \
                    --resolution $resolution \
                    --method ${method} \
                    --based_on ${based_on} \
                    --seed ${seed}

                # python compute_stats.py \
                #     --network-id ${network_id} \
                #     --resolution $resolution \
                #     --method ${method} \
                #     --based_on ${based_on} \
                #     --seed ${seed}
                # python emulate-real-nets/estimate_properties_networkit.py \
                #     -n "${dir}/edge.tsv" \
                #     -c "${dir}/com.tsv" \
                #     -o "${dir}/stats.json"

                python compute_degree_dist.py \
                    --network-id ${network_id} \
                    --resolution $resolution \
                    --method ${method} \
                    --based_on ${based_on} \
                    --seed ${seed}
                    
                python compute_cluster_stats.py \
                    --network-id ${network_id} \
                    --resolution $resolution \
                    --method ${method} \
                    --based_on ${based_on} \
                    --seed ${seed}

                echo "=================================="
                echo ""
            done
        done
    done
done

# ===================================