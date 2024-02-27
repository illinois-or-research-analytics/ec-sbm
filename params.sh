#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --job-name="params"
#SBATCH --partition=tallis

# network_id=cen
# resolution=.001
# method=lfr

for method in abcd
do
    for network_id in cen wiki_talk wiki_topcats cit_hepph cit_patents oc
    do
        for resolution in .001 .01 .1
        do
            python emulate-real-nets/estimate_properties_networkit.py \
                -n "data/networks/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/edge.dat" \
                -c "data/networks/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/com.dat" \
                -o "data/networks/${network_id}_${method}_networks/cen_leiden${resolution}_${method}/stats.json"
        done
    done
done
