#!/bin/bash
#SBATCH --time=02-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/fix_edge/slurm-%j.out
#SBATCH --job-name="0_k10_fixedge_L2"
#SBATCH --partition=folkvangr
#SBATCH --mem=128G

# ===================================

start=0
end=0

for based_on in ikc_cm #leiden_cpm_cm leiden_cpm ikc_cm leiden_mod_cm
do
    for network_id in cit_hepph cit_patents wiki_topcats wiki_talk orkut cen # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
    do
        # skip jester
        if [ ${network_id} == "jester" ]; then
            continue
        fi
        
        for resolution in k10 # leiden.0001 leiden.001 leiden.01 k10 leidenmod
        do
            orig_dir="data/networks/orig/${based_on}/${network_id}/${resolution}/"
            echo $orig_dir

            orig_edgelist_fn="${orig_dir}/edge.dat"
            orig_clustering_fn="${orig_dir}/com.dat"

            orig_stats_outdir="data/stats/orig/${based_on}/${network_id}/${resolution}/"

            if [ ! -f ${orig_stats_outdir}/done ]; then
                python network_evaluation/compute_stats.py \
                    --input-network ${orig_edgelist_fn} \
                    --input-clustering ${orig_clustering_fn} \
                    --output-folder ${orig_stats_outdir}
            else
                echo "Already computed"
            fi

            origwo_dir="data/networks/orig_wo_outliers/${based_on}/${network_id}/${resolution}/"
            echo $origwo_dir

            origwo_edgelist_fn="${origwo_dir}/edge.dat"
            origwo_clustering_fn="${origwo_dir}/com.dat"

            origwo_stats_outdir="data/stats/orig_wo_outliers/${based_on}/${network_id}/${resolution}/"

            if [ ! -d ${origwo_stats_outdir} ]; then
                python network_evaluation/compute_stats.py \
                    --input-network ${origwo_edgelist_fn} \
                    --input-clustering ${origwo_clustering_fn} \
                    --output-folder ${origwo_stats_outdir}
            else
                echo "Already computed"
            fi

            echo "============================================"

            for method in sbmmcsprev1 #abcd abcdta4 sbm sbmmcspres sbmmcsprev1
            do
                input_dirs="data/networks/${method}/${based_on}/${network_id}/${resolution}/"

                output_fixdegree_dirs="data/networks/${method}+eL2/${based_on}/${network_id}/${resolution}/"
                output_dirs="data/networks/${method}+eL2+o/${based_on}/${network_id}/${resolution}/"

                output_fixdegree_stat_dirs="data/stats/${method}+eL2/${based_on}/${network_id}/${resolution}/"
                output_stat_dirs="data/stats/${method}+eL2+o/${based_on}/${network_id}/${resolution}/"
                
                echo $input_dirs

                for seed in $(seq ${start} ${end})
                do
                    echo "============================"

                    input_dir="${input_dirs}/${seed}/"
                    if [ ! -f ${input_dir}/edge.tsv ] || [ ! -f ${input_dir}/com.tsv ]; then
                        echo "[ERROR] ${input_dir}/edge.tsv or ${input_dir}/com.tsv not found"
                        continue
                    fi
                    echo $input_dir

                    echo "Fixing degree sequence"
                    output_fixdegree_dir="${output_fixdegree_dirs}/${seed}/"

                    if [ ! -f ${output_fixdegree_dir}/edge.tsv ] || [ ! -f ${output_fixdegree_dir}/com.tsv ]; then
                        python fix_degree_v2_lahari.py \
                            -f ${input_dir}/edge.tsv \
                            -c ${input_dir}/com.tsv \
                            -ef ${origwo_edgelist_fn} \
                            -oe ${output_fixdegree_dir}/edge.tsv

                        cp ${input_dir}/com.tsv ${output_fixdegree_dir}/com.tsv
                    else
                        echo "Already fixed"
                    fi

                    echo "===="

                    echo "Computing stats"
                    output_fixdegree_stat_dir="${output_fixdegree_stat_dirs}/${seed}/"

                    if [ ! -f ${output_fixdegree_stat_dir}/done ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${output_fixdegree_dir}/edge.tsv \
                            --input-clustering ${output_fixdegree_dir}/com.tsv \
                            --output-folder ${output_fixdegree_stat_dir}
                    else
                        echo "Already computed"
                    fi

                    echo "Comparing with original"

                    if [ ! -f ${output_fixdegree_stat_dir}/compare_output.csv ]; then
                        python network_evaluation/compare_stats_pair.py \
                            --network-1-folder ${origwo_stats_outdir} \
                            --network-2-folder ${output_fixdegree_stat_dir} \
                            --output-file ${output_fixdegree_stat_dir}/compare_output.csv \
                            --is-compare-sequence
                    else
                        echo "Already compared"
                    fi

                    echo "===="

                    echo "Adding outliers"
                    output_dir="${output_dirs}/${seed}/"

                    if [ ! -f ${output_dir}/edge.tsv ] || [ ! -f ${output_dir}/com.tsv ]; then
                        if [ ! -f ${input_dir}/outlier_edge.tsv ]; then
                            python generate_outliers.py \
                                --orig-edgelist ${orig_edgelist_fn} \
                                --orig-clustering ${orig_clustering_fn} \
                                --output-folder ${input_dir}/outlier_edge.tsv
                        else
                            echo "Already generated outliers"
                        fi

                        if [ ! -f ${input_dir}/outlier_edge.tsv ]; then
                            echo "[ERROR] ${input_dir}/outlier_edge.tsv not found"
                            continue
                        fi

                        python combine_clustered_outliers.py \
                            --clustered-edgelist ${output_fixdegree_dir}/edge.tsv \
                            --clustered-clustering ${output_fixdegree_dir}/com.tsv \
                            --outlier-edgelist ${input_dir}/outlier_edge.tsv \
                            --output-folder ${output_dir}
                    else
                        echo "Already generated"
                    fi

                    echo "===="

                    echo "Computing stats"
                    output_stat_dir="${output_stat_dirs}/${seed}/"

                    if [ ! -f ${output_stat_dir}/done ]; then
                        python network_evaluation/compute_stats.py \
                            --input-network ${output_dir}/edge.tsv \
                            --input-clustering ${output_dir}/com.tsv \
                            --output-folder ${output_stat_dir}
                    else
                        echo "Already computed"
                    fi

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