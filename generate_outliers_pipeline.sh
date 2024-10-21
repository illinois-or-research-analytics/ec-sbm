#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/generate_outliers/slurm-%j.out
#SBATCH --job-name="o0_nocm_mod_all_sbmmcs"
#SBATCH --partition=folkvangr
#SBATCH --mem=64G

# ===================================

start=0
end=0

for clustering in leiden_mod #leiden_cpm_cm leiden_cpm ikc_cm leiden_mod_cm
do
    for network_id in cit_hepph cit_patents wiki_topcats wiki_talk orkut cen # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
    do
        for resolution in leidenmod # leiden.0001 leiden.001 leiden.01 k10 leidenmod
        do
            orig_dir="data/networks/orig/${clustering}/${network_id}/${resolution}/"
            echo $orig_dir

            orig_edgelist_fn="${orig_dir}/edge.dat"
            orig_clustering_fn="data/networks/orig_wo_outliers/${clustering}/${network_id}/${resolution}/com.dat"

            echo "============================================"

            if [ ! -f ${orig_clustering_fn} ]; then
                raw_dir="data/networks/orig/${clustering}/${network_id}/${resolution}/"
                clean_outlier_dir="data/networks/orig_wo_outliers/${clustering}/${network_id}/${resolution}/"

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
                    --output-folder ${clean_outlier_dir}

                python test_clean_outlier.py \
                    --output-network ${clean_outlier_dir}/edge.dat \
                    --output-clustering ${clean_outlier_dir}/com.dat
            else
                echo "Outliers already removed"
            fi

            echo "============================================"

            if [ ! -f ${orig_edgelist_fn} ] || [ ! -f ${orig_clustering_fn} ]; then
                echo "Error: ${orig_edgelist_fn} or ${orig_clustering_fn} not found"
                continue
            fi

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

            for method in sbmmcsprev1 #abcd abcdta4 sbm sbmmcspres sbmmcsprev1
            do
                clustered_dirs="data/networks/${method}/${clustering}/${network_id}/${resolution}/"
                echo $clustered_dirs

                output_dirs="data/networks/${method}+o/${clustering}/${network_id}/${resolution}/"
                output_stat_dirs="data/stats/${method}+o/${clustering}/${network_id}/${resolution}/"

                for seed in $(seq ${start} ${end})
                do
                    echo "============================"

                    output_dir="${output_dirs}/${seed}/"
                    output_stat_dir="${output_stat_dirs}/${seed}/"

                    if [ ! -f ${output_dir}/outlier_edge.tsv ]; then
                        python generate_outliers.py \
                            --orig-edgelist ${orig_edgelist_fn} \
                            --orig-clustering ${orig_clustering_fn} \
                            --output-folder ${output_dir}
                    else
                        echo "Outliers already generated"
                    fi

                    clustered_dir="${clustered_dirs}/${seed}/"

                    if [ ! -f ${clustered_dir}/edge.tsv ] || [ ! -f ${clustered_dir}/com.tsv ]; then
                        echo "[INFO] ${clustered_dir}/edge.tsv or ${clustered_dir}/com.tsv not found. Skipping."
                        continue
                    fi

                    echo "Generating outlier subnetwork"

                    if [ ! -f ${output_dir}/edge.tsv ] || [ ! -f ${output_dir}/com.tsv ]; then
                        python combine_clustered_outliers.py \
                            --clustered-edgelist ${clustered_dir}/edge.tsv \
                            --clustered-clustering ${clustered_dir}/com.tsv \
                            --outlier-edgelist ${output_dir}/outlier_edge.tsv \
                            --output-folder ${output_dir}
                    else
                        echo "Already generated"
                    fi

                    echo "===="

                    echo "Computing stats"

                    if [ ! -f ${output_stat_dir}/done ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${output_dir}/edge.tsv \
                            --input-clustering ${output_dir}/com.tsv \
                            --output-folder ${output_stat_dir}
                    else
                        echo "Stats already computed"
                    fi

                    echo "===="

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
            done
            echo "============================"
            echo ""
        done
    done
done