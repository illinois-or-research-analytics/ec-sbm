#!/bin/bash
#SBATCH --time=1-12:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/generate_clustered/slurm-%j.out
#SBATCH --job-name="0_all_test_sbmmcs"
#SBATCH --partition=tallis
#SBATCH --mem=128G

# ===================================

start=0
end=0

for clustering in leiden_mod_nofiltcm # leiden_mod_nofiltcm leiden_cpm leiden_mod  # leiden_cpm_nofiltcm leiden_mod_nofiltcm ikc_nofiltcm infomap_nofiltcm leiden_cpm ikc_nofiltcm ikc_cc
do
    for resolution in leiden.0001 leidenmod # leiden.0001 leiden.001 leiden.01 k10 leidenmod infomap
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
        
        for network_id in cen orkut hyves # $(cat data/networks_train.txt) $(cat data/networks_val.txt) $(cat data/networks_test.txt)
        do
            orig_dir="data/networks/orig_wo_outliers/${clustering}/${network_id}/${resolution}/"
            echo $orig_dir

            orig_edgelist_fn="${orig_dir}/edge.dat"
            orig_clustering_fn="${orig_dir}/com.dat"

            echo "============================================"

            if [ ! -f ${orig_dir}/edge.dat ] || [ ! -f ${orig_dir}/com.dat ]; then
                raw_dir="data/networks/orig/${clustering}/${network_id}/${resolution}/"

                raw_edgelist_fn="${raw_dir}/edge.dat"
                raw_clustering_fn="${raw_dir}/com.dat"

                if [ ! -f ${raw_edgelist_fn} ] || [ ! -f ${raw_clustering_fn} ]; then
                    echo "Error: ${raw_edgelist_fn} or ${raw_clustering_fn} not found"
                    continue
                fi

                echo "Cleaning outliers"
                echo "Raw: ${raw_dir}"

                python clean_outlier.py \
                    --input-network ${raw_edgelist_fn} \
                    --input-clustering ${raw_clustering_fn} \
                    --output-folder ${orig_dir}
            else
                echo "Outliers already removed"
            fi

            python test_clean_outlier.py \
                --output-network ${orig_edgelist_fn} \
                --output-clustering ${orig_clustering_fn}

            echo "============================================"

            echo "Computing original stats"

            orig_stat_dir="data/stats/orig_wo_outliers/${clustering}/${network_id}/${resolution}/"

            if [ ! -f ${orig_stat_dir}/done ]; then
                python network_evaluation/compute_stats.py \
                    --input-network ${orig_edgelist_fn} \
                    --input-clustering ${orig_clustering_fn} \
                    --output-folder ${orig_stat_dir}
            else
                echo "Stats already computed"
            fi

            echo "============================"
            echo ""
            
            for method in sbmmcsprev1 #abcd abcdta4 sbm sbmmcsprev1
            do
                output_dirs="data/networks/${method}/${clustering}/${network_id}/${resolution}/"
                output_stat_dirs="data/stats/${method}/${clustering}/${network_id}/${resolution}/"

                for seed in $(seq ${start} ${end})
                do
                    output_dir="${output_dirs}/${seed}/"
                    output_stat_dir="${output_stat_dirs}/${seed}/"

                    echo "============================"

                    echo "Generating network"
                    echo "Output: ${output_dir}"

                    if [ ! -f ${output_dir}/edge.tsv ] || [ ! -f ${output_dir}/com.tsv ]; then
                        python gen_${method}.py \
                            --edgelist ${orig_edgelist_fn} \
                            --clustering ${orig_clustering_fn} \
                            --output-folder ${output_dir} \
                            --seed ${seed}
                    else
                        echo "Already generated"
                    fi

                    if [ ! -f ${output_dir}/edge.tsv ] || [ ! -f ${output_dir}/com.tsv ]; then
                        echo "Error: ${output_dir}/edge.tsv or ${output_dir}/com.tsv not found"
                        continue
                    fi

                    echo "============================"

                    echo "Computing stats"
                    echo "Output: ${output_stat_dir}"

                    if [ ! -f ${output_stat_dir}/done ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${output_dir}/edge.tsv \
                            --input-clustering ${output_dir}/com.tsv \
                            --output-folder ${output_stat_dir}
                    else
                        echo "Already computed"
                    fi

                    if [ ! -f ${output_stat_dir}/deg_dist.png ]; then
                        python compute_degree_dist.py \
                            --network-folder ${output_dir} \
                            --output-folder ${output_stat_dir}
                    else 
                        echo "Already computed"
                    fi

                    if [ $method = "abcd" ]; then
                        if [ ! -f ${output_stat_dir}/mcs_dist.png ]; then
                            python compute_cluster_stats.py \
                                --network-folder ${output_dir} \
                                --output-folder ${output_stat_dir}
                        else 
                            echo "Already computed"
                        fi
                    else
                        if [ ! -f ${output_stat_dir}/mcs_compare.png ] || [ ! -f ${output_stat_dir}/mcs_dist.png ]; then
                            python compute_cluster_stats.py \
                                --network-folder ${output_dir} \
                                --output-folder ${output_stat_dir} \
                                --is-with-bijection
                        else
                            echo "Already computed"
                        fi
                    fi

                    echo "============================"

                    echo "Comparing with original"

                    if [ ! -f ${output_stat_dir}/compare_output.csv ]; then
                        if [ $method = "abcd" ]; then
                            python network_evaluation/compare_stats_pair.py \
                                --network-1-folder ${orig_stat_dir} \
                                --network-2-folder ${output_stat_dir} \
                                --output-file ${output_stat_dir}/compare_output.csv
                        else
                            python network_evaluation/compare_stats_pair.py \
                                --network-1-folder ${orig_stat_dir} \
                                --network-2-folder ${output_stat_dir} \
                                --output-file ${output_stat_dir}/compare_output.csv \
                                --is-compare-sequence
                        fi
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
