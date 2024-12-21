#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/generate_outliers/slurm-%j.out
#SBATCH --job-name="o0_all_val_sbm"
#SBATCH --partition=folkvangr
#SBATCH --mem=64G

# ===================================

start=0
end=0

for clustering in sbm sbm_cc sbm_wcc leiden_cpm leiden_cpm_nofiltcm leiden_mod leiden_mod_nofiltcm ikc_cc ikc_nofiltcm infomap_cc infomap_nofiltcm
do
    for resolution in sbm leiden.001 leiden.01 leiden.1 leidenmod k10 infomap
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

        for network_id in $(cat data/networks_val.txt) # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt) $(cat data/networks_test.txt)
        do
            orig_dir="data/networks/orig/${clustering}/${network_id}/${resolution}/"
            echo $orig_dir

            orig_edgelist_fn="${orig_dir}/edge.dat"
            orig_clustering_fn="${orig_dir}/com.dat"

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

            for method in sbm #abcd abcdta4 sbm sbmmcspres sbmmcsprev1
            do
                clustered_dirs="data/networks/${method}/${clustering}/${network_id}/${resolution}/"
                echo $clustered_dirs

                output_dirs="data/networks/${method}+o_/${clustering}/${network_id}/${resolution}/"
                output_stat_dirs="data/stats/${method}+o_/${clustering}/${network_id}/${resolution}/"

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
