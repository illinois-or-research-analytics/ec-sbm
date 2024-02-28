#!/bin/bash
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --job-name="gen_network"
#SBATCH --partition=tallis

# method=abcd
for method in abcd lfr
do
    for network_id in cen wiki_topcats cit_hepph wiki_talk cit_patents oc
    do
        for resolution in .001 .01 .1
        do
            echo "=> k_id at $resolution using $method <="

            echo "======"

            # echo "Generating..."
            # python gen_${method}.py $network_id $resolution

            echo "======"

            echo "Computing statistics..."
            python compute_stats.py $network_id $resolution $method

            echo "======"

            # python emulate-real-nets/estimate_properties_networkit.py \
            #         -n "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/edge.dat" \
            #         -c "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/com.dat" \
            #         -o "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/stats.json"

            echo "======"

            # python compute_upperbound.py $network_id $resolution $method

            python compute_wiring_efficiency.py $network_id $resolution $method

            echo "==========================="
            echo " "
        done
    done
done

# python gen_abcds.py cen .001

# network_id=cit_hepph
# resolution=.1
# method=abcdta

# python gen_${method}.py $network_id $resolution
# python compute_stats.py $network_id $resolution $method