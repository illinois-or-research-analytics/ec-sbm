#!/bin/bash
#SBATCH --time=1-12:00:00
#SBATCH --output=slurm_output/cd/slurm-%j.out
#SBATCH --job-name="cdsbm_modcm_vallarge"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=0
end=0

for clustering in leiden_mod_nofiltcm # leiden_cpm leiden_mod ikc infomap
do
    for resolution in leiden.1 leidenmod # leiden.0001 leiden.001 leiden.01 leiden.1 k10 leidenmod infomap
    do
        if [ $clustering = "leiden_cpm_cm" ] || [ $clustering = "leiden_cpm" ] || [ $clustering = "leiden_cpm_nofiltcm" ]; then
            if [ ! $resolution = "leiden.0001" ] && [ ! $resolution = "leiden.001" ] && [ ! $resolution = "leiden.01" ] && [ ! $resolution = "leiden.1" ]; then
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
        elif [ $clustering = "infomap" ] || [ $clustering = "infomap_nofiltcm" ]; then
            if [ ! $resolution = "infomap" ]; then
                continue
            fi
        elif [ $clustering = "sbm_cc" ] || [ $clustering = "sbm_wcc" ] || [ $clustering = "sbm" ]; then
            if [ ! $resolution = "sbm" ]; then
                continue
            fi
        fi

        for network_id in $(cat data/networks_val.txt) # $(cat data/networks_train.txt) $(cat data/networks_val.txt) $(cat data/networks_test.txt)  
        do
            for method in sbmmcsprev1+o+eL1
            do
                for seed in $(seq ${start} ${end})
                do
                    echo "============================"
                    echo ${network_id} ${method} ${clustering} ${resolution} ${seed}
                    out_dir="data/community_detection/${method}/${clustering}/${network_id}/${resolution}/${seed}/sbm/sbm/"
                    if [ -f ${out_dir}/done ]; then
                        continue
                    fi
                    
                    python cd_sbm.py \
                        --edgelist data/networks/${method}/${clustering}/${network_id}/${resolution}/${seed}/edge.tsv \
                        --output-folder ${out_dir}

                    if [ -f ${out_dir}/com.tsv ]; then
                        touch ${out_dir}/done
                    fi
                done            
            done        
        done
    done
done