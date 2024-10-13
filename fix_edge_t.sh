#!/bin/bash
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/fix_edge/slurm-%j.out
#SBATCH --job-name="10_001_fixedge_L1"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=10
end=10
fixedge_method=L1

echo "============================================"
echo "Fixing edge with ${fixedge_method}"
echo "============================================"

for clustering in leiden_cpm_cm #leiden_cpm_cm leiden_cpm ikc_cm leiden_mod_cm
do
    for network_id in $(cat data/networks.txt) cit_hepph cit_patents wiki_topcats wiki_talk orkut cen # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
    do
        # skip jester
        if [ ${network_id} == "jester" ]; then
            continue
        fi
        
        for resolution in leiden.001 # leiden.0001 leiden.001 leiden.01 k10 leidenmod
        do
            orig_dir="data/networks/orig/${clustering}/${network_id}/${resolution}/"
            echo $orig_dir

            orig_edgelist_fn="${orig_dir}/edge.dat"
            orig_clustering_fn="${orig_dir}/com.dat"

            orig_stats_outdir="data/stats/orig/${clustering}/${network_id}/${resolution}/"

            if [ ! -f ${orig_stats_outdir}/done ]; then
                python network_evaluation/compute_stats.py \
                    --input-network ${orig_edgelist_fn} \
                    --input-clustering ${orig_clustering_fn} \
                    --output-folder ${orig_stats_outdir}
            else
                echo "Already computed"
            fi

            echo "============================================"

            for method in sbmmcsprev1 #abcd abcdta4 sbm sbmmcspres sbmmcsprev1
            do
                input_dirs="data/networks/${method}+o/${clustering}/${network_id}/${resolution}/"
                echo $input_dirs

                output_dirs="data/networks/${method}+o+e${fixedge_method}/${clustering}/${network_id}/${resolution}/"
                output_stat_dirs="data/stats/${method}+o+e${fixedge_method}/${clustering}/${network_id}/${resolution}/"

                for seed in $(seq ${start} ${end})
                do
                    echo "============================"

                    input_dir="${input_dirs}/${seed}/"
                    output_dir="${output_dirs}/${seed}/"
                    output_stat_dir="${output_stat_dirs}/${seed}/"
                    
                    if [ ! -f ${input_dir}/edge.tsv ] || [ ! -f ${input_dir}/com.tsv ]; then
                        echo "[ERROR] ${input_dir}/edge.tsv or ${input_dir}/com.tsv not found"
                        continue
                    fi

                    echo "Fixing degree sequence"
                    echo $input_dir

                    if [ ! -f ${output_dir}/fix_edge.tsv ]; then
                        python fix_degree_${fixedge_method}.py \
                            --orig-edgelist ${orig_edgelist_fn} \
                            --orig-clustering ${orig_clustering_fn} \
                            --exist-edgelist ${input_dir}/edge.tsv \
                            --output-folder ${output_dir}
                    else
                        echo "Already fixed"
                    fi

                    if [ ! -f ${output_dir}/edge.tsv ] || [ ! -f ${output_dir}/com.tsv ]; then
                        python combine_clustered_outliers.py \
                            --clustered-edgelist ${input_dir}/edge.tsv \
                            --clustered-clustering ${input_dir}/com.tsv \
                            --outlier-edgelist ${output_dir}/fix_edge.tsv \
                            --output-folder ${output_dir}
                    else
                        echo "Already combined"
                    fi

                    echo "===="

                    echo "Computing stats"

                    if [ ! -f ${output_stat_dir}/done ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${output_dir}/edge.tsv \
                            --input-clustering ${output_dir}/com.tsv \
                            --output-folder ${output_stat_dir}
                    else
                        echo "Already computed"
                    fi

                    echo "===="

                    echo "Comparing with original"

                    if [ ! -f ${output_stat_dir}/compare_output.csv ]; then
                        python network_evaluation/compare_stats_pair.py \
                            --network-1-folder ${orig_stats_outdir} \
                            --network-2-folder ${output_stat_dir} \
                            --output-file ${output_stat_dir}/compare_output.csv \
                            --is-compare-sequence
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