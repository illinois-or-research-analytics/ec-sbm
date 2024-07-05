#!/bin/bash
#SBATCH --time=168:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="outliers"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=1
end=3

for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
do
    for network_id in twitter uni_email escorts discogs_label foldoc anybeat bitcoin_alpha eu_procurements paris_transportation dnc # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
    do
        for resolution in .001 # .0001 .001 .01
        do
            orig_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"

            edgelist_fn="${orig_dir}/edge.dat"
            clustering_fn="${orig_dir}/com.dat"

            orig_stats_outdir="data/stats/orig/${based_on}/${network_id}/leiden${resolution}/"

            if [ ! -d ${orig_stats_outdir} ]; then
                python network_evaluation/compute_stats.py \
                    --input-network ${edgelist_fn} \
                    --input-clustering ${clustering_fn} \
                    --output-folder ${orig_stats_outdir}
            fi

            echo "============================================"

            for method in sbm sbmmcspres abcdta4 #abcd abcdta4 sbm sbmmcspre
            do
                reps_dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/"
                echo $reps_dir

                output_dirs="data/networks/${method}+o/leiden_cpm_cm/${network_id}/leiden${resolution}/"

                for seed in $(seq ${start} ${end})
                do
                    dir="${reps_dir}/${seed}/"
                    output_dir="${output_dirs}/${seed}/"

                    echo "============================"
                    echo $dir

                    if [ ! -f ${dir}/edge.tsv ] || [ ! -f ${dir}/com.tsv ]; then
                        echo "[ERROR] ${dir}/edge.tsv or ${dir}/com.tsv not found"
                        continue
                    fi

                    echo "Generating outlier subnetwork"

                    if [ ! -d ${output_dir} ]; then
                        if [ ! -f ${dir}/outlier_edge.tsv ]; then
                            python generate_outliers.py \
                                --orig-edgelist ${edgelist_fn} \
                                --orig-clustering ${clustering_fn} \
                                --output-folder ${dir}
                        fi

                        python combine_clustered_outliers.py \
                            --clustered-edgelist ${dir}/edge.tsv \
                            --clustered-clustering ${dir}/com.tsv \
                            --outlier-edgelist ${dir}/outlier_edge.tsv \
                            --output-folder ${output_dir}
                    fi

                    echo "===="

                    echo "Computing stats"

                    if [ ! -f ${output_dir}/stats.json ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${output_dir}/edge.tsv \
                            --input-clustering ${output_dir}/com.tsv \
                            --output-folder ${output_dir}
                    fi

                    echo "===="

                    echo "Comparing with original"

                    python network_evaluation/compare_stats_pair.py \
                        --network-1-folder ${orig_stats_outdir} \
                        --network-2-folder ${output_dir} \
                        --output-file ${output_dir}/compare_output.csv \
                        --is-compare-sequence
                done
            done
            echo "============================"
            echo ""
        done
    done
done