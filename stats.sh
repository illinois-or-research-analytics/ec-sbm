#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --job-name="network_stats"
#SBATCH --partition=tallis

for method in abcd abcdta2
do
    for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
    do
        for network_id in cit_patents #cit_hepph cit_patents wiki_topcats wiki_talk orkut
        do
            for resolution in .0001 .001 .01 #.0001 .001 .01
            do
                python compute_degree_dist.py ${network_id} ${resolution} ${method} ${based_on}
            done
        done
    done
done

# ===================================

network_id=cit_hepph
resolution=.0001
method=abcd
based_on=leiden_cpm_cm

python compute_degree_dist.py ${network_id} ${resolution} ${method} ${based_on}