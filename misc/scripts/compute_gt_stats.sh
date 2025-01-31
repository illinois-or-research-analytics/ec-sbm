#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compute_gt_stats/slurm-%j.out
#SBATCH --job-name="gt_sbmwcc_lj_sbmmcs+e"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=0
end=0

for clustering in sbm_wcc # sbm sbm_cc sbm_wcc leiden_cpm leiden_cpm_nofiltcm leiden_mod leiden_mod_nofiltcm ikc_cc ikc_nofiltcm infomap_cc infomap_nofiltcm
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
        
        for network_id in livejournal # $(cat data/networks_train.txt) $(cat data/networks_val.txt) $(cat data/networks_test.txt)
        do  
            orig_stat_dir="data/stats/orig/network_only/${network_id}/"
            echo $orig_stat_dir

            if [ ! -f ${orig_stat_dir}/gt_stats.json ]; then
                echo "Error: ${orig_stat_dir}/gt_stats.json not found"
                continue
            fi

            for method in sbmmcsprev1+o+eL1 # sbm+o sbmmcsprev1+o sbmmcsprev1+o+eL1 RECCSv1_OS1 abcd+o abcdta4+o abcdta4+o+eL1 
            do
                input_dirs="data/networks/${method}/${clustering}/${network_id}/${resolution}/"
                output_stat_dirs="data/stats/${method}/${clustering}/${network_id}/${resolution}/"

                for seed in $(seq ${start} ${end})
                do
                    echo "============================"
                    input_dir="${input_dirs}/${seed}/"
                    output_stat_dir="${output_stat_dirs}/${seed}/"
                    echo ${input_dir}

                    if [ ! -f ${input_dir}/edge.tsv ]; then
                        echo "Error: ${input_dir}/edge.tsv not found"
                        continue
                    fi

                    python network_evaluation/compute_gt_stats.py \
                        --input ${input_dir}/edge.tsv \
                        --output ${output_stat_dir}

                    if [ ! -f ${output_stat_dir}/gt_stats.json ]; then
                        echo "Error: ${output_stat_dir}/gt_stats.json not found"
                        continue
                    fi

                    # if [ ! -f ${output_stat_dir}/compare_gt_stats.csv ]; then
                        python network_evaluation/compare_gt_stats_pair.py \
                            --network-1-folder ${orig_stat_dir} \
                            --network-2-folder ${output_stat_dir} \
                            --output-file ${output_stat_dir}/compare_gt_stats.csv
                    # else
                    #     echo "Already compared."
                    # fi
                done
                echo "============================"
                echo ""
            done
            echo "============================================"
            echo ""
        done
    done
done
