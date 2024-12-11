#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/generate_clustered/slurm-%j.out
#SBATCH --job-name="0_infomapcc_val_sbmmcspre"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=0
end=0

for clustering in sbm
do
    for resolution in sbm
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
        fi
        
        for network_id in $(cat data/networks_val.txt) # $(cat data/networks_train.txt) $(cat data/networks_val.txt) $(cat data/networks_test.txt)
        do  
            for method in sbm #abcd abcdta4 sbm sbmmcspres sbmmcsprev1
            do
                input_dirs="data/networks/${method}/${clustering}/${network_id}/${resolution}/"
                output_stat_dirs="data/stats/${method}/${clustering}/${network_id}/${resolution}/"

                for seed in $(seq ${start} ${end})
                do
                    input_dir="${input_dirs}/${seed}/"
                    output_stat_dir="${output_stat_dirs}/${seed}/"

                    echo "============================"

                    if [ ! -f ${input_dir}/edge.tsv ]; then
                        echo "Error: ${input_dir}/edge.dat not found"
                        continue
                    fi

                    rm ${output_stat_dir}/excess_edges.tsv

                    python compute_excess_edges.py \
                        --input ${input_dir}/edge.tsv \
                        --output ${output_stat_dir}/excess_edges.json
                done
                echo "============================"
                echo ""
            done
            echo "============================================"
            echo ""
        done
    done
done
