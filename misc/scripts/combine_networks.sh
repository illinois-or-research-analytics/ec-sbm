#!/bin/bash
#SBATCH --time=168:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="outliers"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=0
end=3

for based_on in leiden_c #leiden_cpm_cm leiden_cpm
do
    for network_id in cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt) # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
    do
        for resolution in .001 # .0001 .001 .01
        do
            echo "${based_on} ${network_id} ${resolution}"
            echo "============================================"

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

            outlier_dirs="data/networks/outliers/${based_on}/${network_id}/leiden${resolution}/"

            for method in abcdta4 sbm sbmmcspres # abcd abcdta4 sbm sbmmcspres
            do 
                clustered_dirs="data/networks/${method}/leiden_cpm_cm/${network_id}/leiden${resolution}/"
                output_dirs="data/networks/${method}+o/leiden_cpm_cm/${network_id}/leiden${resolution}/"

                for seed in $(seq ${start} ${end})
                do
                    echo "============================"
                    clustered_dir="${clustered_dirs}/${seed}/"
                    outlier_dir="${outlier_dirs}/0/" # always use the same clustering for all seeds
                    output_dir="${output_dirs}/${seed}/"

                    if [ ! -d ${clustered_dir} ]; then
                        echo "Clustered directory does not exist: ${clustered_dir}"
                        continue
                    fi

                    if [ ! -d ${outlier_dir} ]; then
                        echo "Outlier directory does not exist: ${outlier_dir}"
                        continue
                    fi

                    if [ ! -d ${output_dir} ]; then
                        python combine_clustered_outliers.py \
                            --clustered-edgelist ${clustered_dir}/edge.tsv \
                            --clustered-clustering ${clustered_dir}/com.tsv \
                            --outlier-edgelist ${outlier_dir}/outlier_edge.tsv \
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
            echo "============================================"
        done
    done
done

