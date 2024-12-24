#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/cm/filt/slurm-%j.out
#SBATCH --job-name="cm_mod"
#SBATCH --partition=tallis
#SBATCH --mem=128G

# ===================================

start=0
end=0

cur_dir=$(pwd)

for clustering in leiden_cpm leiden_mod infomap # leiden_cpm leiden_mod ikc infomap
do
    for resolution in leiden.0001 leiden.001 leiden.01 leiden.1 leidenmod infomap # leiden.0001 leiden.001 leiden.01 leiden.1 k10 leidenmod infomap
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

        cd ${cur_dir}
        for network_id in paris_transportation discogs_label # $(cat data/networks_train.txt) $(cat data/networks_val.txt) $(cat data/networks_test.txt)  
        do  
            cd ${cur_dir}
            for method in sbmmcsprev1+o+eL1
            do
                cd ${cur_dir}
                for seed in $(seq ${start} ${end})
                do
                    echo "============================"
                    echo ${network_id} ${method} ${clustering} ${resolution} ${seed}
                    cd ${cur_dir}
                    cd data/community_detection_filtcm/${method}/sbm_wcc/${network_id}/sbm/0/${clustering}/${resolution}/
                    if [ -f done ]; then
                        cd ${cur_dir}
                        continue
                    fi
                    python -m main pipeline.json
                    touch done
                    cd ${cur_dir}                
                done            
            done        
        done    
    done
done