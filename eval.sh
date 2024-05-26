#!/bin/bash
#SBATCH --time=168:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="eval"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

orig="orig_wo_outliers"
T=0

for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
do
    for network_id in cit_hepph cit_patents wiki_talk orkut wiki_topcats cen #cit_hepph cit_patents wiki_topcats wiki_talk orkut
    do
        for resolution in .0001 .001 .01 #.0001 .001 .01
        do
            orig_dir="data/networks/${orig}/${based_on}/${network_id}/leiden${resolution}/"

            edgelist_fn="${orig_dir}/edge.dat"
            clustering_fn="${orig_dir}/com.dat"

            echo ${orig_dir}
            echo "============================================"

            # raw_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"

            # echo "Cleaning outliers"
            # echo "Raw: ${raw_dir}"

            # python clean_outlier.py \
            #     --input-network ${raw_dir}/edge.dat \
            #     --input-clustering ${raw_dir}/com.dat \
            #     --output-folder ${orig_dir}

            # python test_clean_outlier.py \
            #     --output-network ${output_dir}/edge.dat \
            #     --output-clustering ${output_dir}/com.dat

            echo "============================================"

            echo "Computing original stats"

            orig_stats_outdir="data/stats/${orig}/${based_on}/${network_id}/leiden${resolution}/"
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

                for seed in $(seq 0 ${T})
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

                    python compute_connectivity.py \
                        --network-folder ${dir} \
                        --output-folder ${dir}

                    python compute_degree_dist.py \
                        --network-folder ${dir} \
                        --output-folder ${dir}

                    if [ $method = "abcdta4" ]; then
                        python compute_cluster_stats.py \
                            --network-folder ${dir} \
                            --output-folder ${dir} \
                            --is-with-bijection
                    else
                        python compute_cluster_stats.py \
                            --network-folder ${dir} \
                            --output-folder ${dir}
                    fi

                    echo "============================"

                    echo "Comparing with original"

                    python network_evaluation/compare_stats_pair.py \
                            --network-1-folder ${orig_stats_outdir} \
                            --network-2-folder ${dir} \
                            --output-file ${dir}/compare_output.csv \
                            --is-compare-sequence

                    # if [ $method = "abcdta4" ]; then
                    #     python network_evaluation/compare_stats_pair.py \
                    #         --network-1-folder ${orig_stats_outdir} \
                    #         --network-2-folder ${dir} \
                    #         --output-file ${dir}/compare_output.csv \
                    #         --is-compare-sequence
                    # else
                    #     python network_evaluation/compare_stats_pair.py \
                    #         --network-1-folder ${orig_stats_outdir} \
                    #         --network-2-folder ${dir} \
                    #         --output-file ${dir}/compare_output.csv
                    # fi
                done
                echo "============================"
                echo ""
            done
            echo "============================================"
            echo ""
        done
    done
done