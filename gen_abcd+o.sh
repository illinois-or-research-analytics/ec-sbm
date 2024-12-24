#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/abcd+o/slurm-%j.out
#SBATCH --job-name="0_k10cm_val_abcd+o"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=0
end=0

for clustering in ikc_nofiltcm # sbm sbm_cc sbm_wcc leiden_cpm leiden_cpm_nofiltcm leiden_mod leiden_mod_nofiltcm ikc_cc ikc_nofiltcm infomap_cc infomap_nofiltcm
do
    for resolution in sbm leiden.001 leiden.01 leiden.1 leidenmod k10 infomap # sbm leiden.001 leiden.01 leiden.1 leidenmod k10 infomap
    do
        # Matching clustering with resolution
        if [ $clustering = "leiden_cpm_cm" ] || [ $clustering = "leiden_cpm" ] || [ $clustering = "leiden_cpm_nofiltcm" ]; then
            if [ ! $resolution = "leiden.001" ] && [ ! $resolution = "leiden.01" ] && [ ! $resolution = "leiden.1" ]; then
                continue
            fi
        elif [ $clustering = "leiden_mod_cm" ] || [ $clustering = "leiden_mod" ] || [ $clustering = "leiden_mod_nofiltcm" ]; then
            if [ ! $resolution = "leidenmod" ]; then
                continue
            fi
        elif [ $clustering = "ikc_cm" ] || [ $clustering = "ikc_cc" ] || [ $clustering = "ikc_nofiltcm" ]; then
            if [ ! $resolution = "k10" ]; then
                continue
            fi
        elif [ $clustering = "infomap_cc" ] || [ $clustering = "infomap_nofiltcm" ]; then
            if [ ! $resolution = "infomap" ]; then
                continue
            fi
        elif [ $clustering = "sbm_cc" ] || [ $clustering = "sbm_wcc" ] || [ $clustering = "sbm" ]; then
            if [ ! $resolution = "sbm" ]; then
                continue
            fi
        fi

        for network_id in $(cat data/networks_val.txt) # $(cat data/networks_train.txt) $(cat data/networks_val.txt) $(cat data/networks_test.txt)
        do
            orig_dir="data/networks/orig/${clustering}/${network_id}/${resolution}/"

            orig_edgelist_fn="${orig_dir}/edge.dat"
            orig_clustering_fn="${orig_dir}/com.dat"

            echo "============================================"

            if [ ! -f ${orig_edgelist_fn} ] || [ ! -f ${orig_clustering_fn} ]; then
                echo "Error: ${orig_edgelist_fn} or ${orig_clustering_fn} not found"
                continue
            fi

            echo "Computing original stats"

            orig_stat_dir="data/stats/orig/${clustering}/${network_id}/${resolution}/"

            if [ ! -f ${orig_stat_dir}/done ]; then
                python network_evaluation/compute_stats.py \
                    --input-network ${orig_edgelist_fn} \
                    --input-clustering ${orig_clustering_fn} \
                    --output-folder ${orig_stat_dir}
            else
                echo "Already computed"
            fi

            echo "============================================"
            
            for method in abcd+o #abcd abcdta4 sbm sbmmcspre
            do
                output_dirs="data/networks/${method}/${clustering}/${network_id}/${resolution}/"
                output_stat_dirs="data/stats/${method}/${clustering}/${network_id}/${resolution}/"
                echo $output_dirs

                for seed in $(seq ${start} ${end})
                do
                    output_dir="${output_dirs}/${seed}/"
                    output_stat_dir="${output_stat_dirs}/${seed}/"

                    echo "============================"
                    echo $output_dir

                    echo "Generating network"

                    if [ ! -f ${output_dir}/edge.tsv ] || [ ! -f ${output_dir}/com.tsv ]; then
                        python gen_${method}.py \
                            --edgelist ${orig_edgelist_fn} \
                            --clustering ${orig_clustering_fn} \
                            --output-folder ${output_dir} \
                            --seed ${seed}
                    fi

                    if [ ! -f ${output_dir}/edge.tsv ] || [ ! -f ${output_dir}/com.tsv ]; then
                        echo "Error: ${output_dir}/edge.tsv or ${output_dir}/com.tsv not found"
                        continue
                    fi

                    echo "============================"

                    echo "Computing stats"

                    if [ ! -f ${output_stat_dir}/done ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${output_dir}/edge.tsv \
                            --input-clustering ${output_dir}/com.tsv \
                            --output-folder ${output_stat_dir}
                    fi

                    if [ ! -f ${output_stat_dir}/deg_dist.png ]; then
                        python compute_degree_dist.py \
                            --network-folder ${output_dir} \
                            --output-folder ${output_stat_dir}
                    else 
                        echo "Already computed"
                    fi

                    if [ ! -f ${output_stat_dir}/mcs_dist.png ]; then
                        python compute_cluster_stats.py \
                            --network-folder ${output_dir} \
                            --output-folder ${output_stat_dir}
                    else 
                        echo "Already computed"
                    fi

                    echo "============================"

                    echo "Comparing with original"

                    if [ ! -f ${output_stat_dir}/compare_output.csv ]; then
                        python network_evaluation/compare_stats_pair.py \
                            --network-1-folder ${orig_stat_dir} \
                            --network-2-folder ${output_stat_dir} \
                            --output-file ${output_stat_dir}/compare_output.csv
                    else
                        echo "Already compared"
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
