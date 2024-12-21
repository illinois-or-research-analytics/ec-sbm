#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/excess_edges/slurm-%j.out
#SBATCH --job-name="fix_abcd+o"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

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
            echo ${clustering} ${resolution} ${network_id}

            rm data/networks/abcd+o/${clustering}/${network_id}/${resolution}/0/edge.bak.tsv
            # python fix_abcd+o.py \
            #     --clustering ${clustering} \
            #     --resolution ${resolution} \
            #     --network_id ${network_id}
        done
    done
done
