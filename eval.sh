#!/bin/bash
#SBATCH --time=168:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="eval_sbmmcspre_10"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=0
end=1

for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
do
    for network_id in discogs_label paris_transportation dnc # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
    do
        for resolution in .001 # .0001 .001 .01
        do
            orig_dir="data/networks/orig_wo_outliers/${based_on}/${network_id}/leiden${resolution}/"

            edgelist_fn="${orig_dir}/edge.dat"
            clustering_fn="${orig_dir}/com.dat"

            echo ${orig_dir}
            echo "============================================"

            if [ ! -d ${orig_dir} ]; then
                raw_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"

                if [ ! -d ${raw_dir} ]; then
                    echo "Error: ${raw_dir} not found"
                    continue
                fi

                echo "Cleaning outliers"
                echo "Raw: ${raw_dir}"

                python clean_outlier.py \
                    --input-network ${raw_dir}/edge.dat \
                    --input-clustering ${raw_dir}/com.dat \
                    --output-folder ${orig_dir}

                python test_clean_outlier.py \
                    --output-network ${output_dir}/edge.dat \
                    --output-clustering ${output_dir}/com.dat
            fi

            echo "============================================"

            echo "Computing original stats"

            orig_stats_outdir="data/stats/orig_wo_outliers/${based_on}/${network_id}/leiden${resolution}/"

            if [ ! -d ${orig_stats_outdir} ]; then
                python network_evaluation/compute_stats.py \
                    --input-network ${edgelist_fn} \
                    --input-clustering ${clustering_fn} \
                    --output-folder ${orig_stats_outdir}
            fi

            echo "============================"
            echo ""
            
            for method in abcdta4 sbm sbmmcspres #abcd abcdta4 sbm sbmmcspre
            do
                reps_dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/"
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

                    if [ $method = "abcdta4" ] || [ $method = "sbm" ] || [ $method = "sbmmcspre" ]; then
                        if [ ! -f ${dir}/mcs_compare.png ] || [ ! -f ${dir}/mcs_dist.png ]; then
                            python compute_cluster_stats.py \
                                --network-folder ${dir} \
                                --output-folder ${dir} \
                                --is-with-bijection
                        fi
                    else
                        if [ ! -f ${dir}/mcs_dist.png ]; then
                            python compute_cluster_stats.py \
                                --network-folder ${dir} \
                                --output-folder ${dir}
                        fi
                    fi

                    echo "============================"

                    echo "Comparing with original"

                    python network_evaluation/compare_stats_pair.py \
                        --network-1-folder ${orig_stats_outdir} \
                        --network-2-folder ${dir} \
                        --output-file ${dir}/compare_output.csv \
                        --is-compare-sequence
                done
                echo "============================"
                echo ""
            done
            echo "============================================"
            echo ""
        done
    done
done
