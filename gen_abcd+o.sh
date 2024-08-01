#!/bin/bash
#SBATCH --time=336:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="10_k10_abcd+o"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=1
end=10

for based_on in ikc_cm #leiden_cpm_cm leiden_cpm ikc
do
    for network_id in cit_hepph cit_patents wiki_topcats wiki_talk orkut cen # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
    do
        # skip epinions
        if [ ${network_id} == "epinions" ]; then
            continue
        fi
        
        for resolution in k10 # .0001 .001 .01
        do
            orig_dir="data/networks/orig/${based_on}/${network_id}/${resolution}/"

            edgelist_fn="${orig_dir}/edge.dat"
            clustering_fn="${orig_dir}/com.dat"

            echo ${orig_dir}
            echo "============================================"

            echo "Computing original stats"

            orig_stats_outdir="data/stats/orig/${based_on}/${network_id}/${resolution}/"

            if [ ! -d ${orig_stats_outdir} ]; then
                python network_evaluation/compute_stats.py \
                    --input-network ${edgelist_fn} \
                    --input-clustering ${clustering_fn} \
                    --output-folder ${orig_stats_outdir}
            fi

            echo "============================"
            echo ""
            
            for method in abcd+o #abcd abcdta4 sbm sbmmcspre
            do
                reps_dir="data/networks/${method}/${based_on}/${network_id}/${resolution}/"
                echo $reps_dir

                for seed in $(seq ${start} ${end})
                do
                    dir="${reps_dir}/${seed}/"

                    echo "============================"
                    echo $dir

                    echo "Generating network"

                    if [ ! -d ${dir} ]; then
                        python gen_${method}.py \
                            --edgelist ${edgelist_fn} \
                            --clustering ${clustering_fn} \
                            --output-folder ${dir} \
                            --seed ${seed}
                    fi

                    if [ ! -f ${dir}/edge.tsv ] || [ ! -f ${dir}/com.tsv ]; then
                        echo "Error: ${dir}/edge.tsv or ${dir}/com.tsv not found"
                        continue
                    fi

                    echo "============================"

                    echo "Computing stats"

                    if [ ! -f ${dir}/stats.json ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${dir}/edge.tsv \
                            --input-clustering ${dir}/com.tsv \
                            --output-folder ${dir}
                    fi

                    if [ ! -f ${dir}/deg_dist.png ]; then
                        python compute_degree_dist.py \
                            --network-folder ${dir} \
                            --output-folder ${dir}
                    fi

                    if [ ! -f ${dir}/mcs_dist.png ]; then
                        python compute_cluster_stats.py \
                            --network-folder ${dir} \
                            --output-folder ${dir}
                    fi

                    echo "============================"

                    echo "Comparing with original"

                    python network_evaluation/compare_stats_pair.py \
                        --network-1-folder ${orig_stats_outdir} \
                        --network-2-folder ${dir} \
                        --output-file ${dir}/compare_output.csv
                done
                echo "============================"
                echo ""
            done
            echo "============================================"
            echo ""
        done
    done
done
