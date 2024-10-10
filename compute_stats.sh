#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compute_stat/slurm-%j.out
#SBATCH --job-name="s10_k10_all"
#SBATCH --partition=secondary
#SBATCH --mem=64G

# ===================================

start=10
end=10

for seed in $(seq ${start} ${end})
do
    echo "============================="
    echo "============================="
    echo "Seed: ${seed}"
    echo "============================="
    echo "============================="

    for clustering in ikc_cm # leiden_cpm_cm leiden_cpm ikc_cm leiden_mod_cm
    do
        for resolution in k10 # leiden.0001 leiden.001 leiden.01 k10 leidenmod
        do
            for network_id in cit_hepph cit_patents wiki_topcats wiki_talk orkut cen # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
            do
                echo "============================="
                echo "Network: ${network_id} | Clustering: ${clustering} | Resolution: ${resolution}"

                orig_dir="data/networks/orig/${clustering}/${network_id}/${resolution}/"
                edgelist_fn="${orig_dir}/edge.dat"
                clustering_fn="${orig_dir}/com.dat"

                orig_stat_dir="data/stats/orig/${clustering}/${network_id}/${resolution}/"

                echo "Computing statistics for original network"

                if [ ! -f ${orig_stat_dir}/done ]; then
                    python network_evaluation/compute_stats.py \
                        --input-network ${edgelist_fn} \
                        --input-clustering ${clustering_fn} \
                        --output-folder ${orig_stat_dir}
                else
                    echo "Statistics already computed"
                fi

                for method in sbmmcsprev1 abcdta4 sbm abcd # sbmmcsprev1 abcdta4 sbm abcd
                do
                    echo "============================="
                    echo "Method: ${method}"

                    output_dirs="data/networks/${method}+o/${clustering}/${network_id}/${resolution}/"
                    output_stat_dirs="data/stats/${method}+o/${clustering}/${network_id}/${resolution}/"

                    output_dir="${output_dirs}/${seed}/"
                    output_stat_dir="${output_stat_dirs}/${seed}/"

                    echo "Computing stats"

                    if [ ! -f ${output_dir}/edge.tsv ] || [ ! -f ${output_dir}/com.tsv ]; then
                        echo "[ERROR] ${output_dir}/edge.tsv or ${output_dir}/com.tsv not found"
                        continue
                    fi

                    if [ ! -f ${output_stat_dir}/done ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${output_dir}/edge.tsv \
                            --input-clustering ${output_dir}/com.tsv \
                            --output-folder ${output_stat_dir}
                    else
                        echo "Statistics already computed"
                    fi

                    echo "===="

                    echo "Comparing with original"

                    if [ ! -f ${output_stat_dir}/compare_output.csv ]; then
                        python network_evaluation/compare_stats_pair.py \
                            --network-1-folder ${orig_stat_dir} \
                            --network-2-folder ${output_stat_dir} \
                            --output-file ${output_stat_dir}/compare_output.csv \
                            --is-compare-sequence
                    else
                        echo "Comparison already made"
                    fi
                done
            done
        done
    done

    echo ""
done