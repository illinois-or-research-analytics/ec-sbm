#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --job-name="network_stats"
#SBATCH --partition=tallis

for method in abcds
do
    for network_id in wiki_talk cen wiki_topcats cit_hepph cit_patents oc
    do
        for resolution in .001 .01 .1
        do
            python compute_stats.py $network_id $resolution $method
            # echo "python gen_abcd.py $network_id $resolution"
        done
    done
done
# python compute_stats.py cen .01 abcd