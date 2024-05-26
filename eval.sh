#!/bin/bash
#SBATCH --time=48:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="eval"
#SBATCH --partition=eng-research-gpu
#SBATCH --mem=64G

# ===================================

T=2

for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
do
    for network_id in cit_hepph #cit_hepph cit_patents wiki_topcats wiki_talk orkut
    do
        for resolution in .0001 #.0001 .001 .01
        do
            orig_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"
            edgelist_fn="${orig_dir}/edge.dat"
            clustering_fn="${orig_dir}/com.dat"

            echo $orig_dir

            echo "============================================"

            echo "Computing original stats"

            orig_stats_outdir="data/stats/orig/${based_on}/${network_id}/leiden${resolution}/"
            python network_evaluation/compute_stats.py \
                --input-network ${edgelist_fn} \
                --input-clustering ${clustering_fn} \
                --output-folder ${orig_stats_outdir} \
                --overwrite

            echo "============================"
            echo ""
            
            for method in abcdta4 abcd #abcd abcdta4
            do    
                reps_dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/"
                echo $reps_dir

                for seed in $(seq 1 ${T})
                do
                    dir="${reps_dir}/${seed}/"

                    echo "============================"
                    echo $dir

                    echo "Generating network"

                    python gen_${method}.py \
                        --edgelist ${edgelist_fn} \
                        --clustering ${clustering_fn} \
                        --output-folder ${dir} \
                        --seed ${seed}

                    echo "============================"

                    echo "Computing stats"

                    python network_evaluation/compute_stats.py \
                        --input-network ${dir}/edge.tsv \
                        --input-clustering ${dir}/com.tsv \
                        --output-folder ${dir} \
                        --overwrite

                    echo "============================"

                    echo "Comparing with original"

                    if [ $method = "abcdta4" ]; then
                        python network_evaluation/compare_stats_pair.py \
                            --network-1-folder ${orig_stats_outdir} \
                            --network-2-folder ${dir} \
                            --output-file ${dir}/compare_output.csv \
                            --is-compare-sequence
                    else
                        python network_evaluation/compare_stats_pair.py \
                            --network-1-folder ${orig_stats_outdir} \
                            --network-2-folder ${dir} \
                            --output-file ${dir}/compare_output.csv
                    fi
                done
                echo "============================"
                echo ""
            done
            echo "============================================"
            echo ""
        done
    done
done