#!/bin/bash
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --job-name="gen_network"
#SBATCH --partition=tallis

# ===================================

# network_id=cit_patents
# resolution=.01
# method=abcd
# based_on=leiden_cpm

# python gen_${method}.py $network_id $resolution ${method} ${based_on}
# python compute_stats.py $network_id $resolution ${method}_${based_on}
# python emulate-real-nets/estimate_properties_networkit.py \
#     -n "data/networks/${method}/${network_id}_${method}_${based_on}_networks/${network_id}_leiden${resolution}_${method}_${based_on}/edge.dat" \
#     -c "data/networks/${method}/${network_id}_${method}_${based_on}_networks/${network_id}_leiden${resolution}_${method}_${based_on}/com.dat" \
#     -o "data/networks/${method}/${network_id}_${method}_${based_on}_networks/${network_id}_leiden${resolution}_${method}_${based_on}/stats.json"
# python compute_upperbound.py $network_id $resolution ${method}_${based_on}
# python compute_potential_connectivity.py $network_id $resolution ${method}_${based_on}
# python compute_wiring_efficiency.py $network_id $resolution ${method}_${based_on}

# ===================================

for method in abcd
do
    for based_on in leiden_cpm_cm
    do
        for network_id in cit_hepph #cit_patents wiki_topcats wiki_talk orkut
        do
            for resolution in .0001 .001 .01 #.0001 .001 .01
            do
                echo "=> $network_id at $resolution using $method based on $based_on <="

                echo "======"
                echo "Generating..."
                
                python gen_${method}.py $network_id $resolution ${method} ${based_on}

                echo "======"

                echo "Computing statistics..."

                python compute_stats.py $network_id $resolution $method ${based_on}

                echo "======"

                python emulate-real-nets/estimate_properties_networkit.py \
                        -n "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/edge.dat" \
                        -c "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/com.dat" \
                        -o "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/stats.json"

                echo "======"

                python compute_upperbound.py $network_id $resolution $method ${based_on}

                python compute_potential_connectivity.py $network_id $resolution $method ${based_on}

                python compute_wiring_efficiency.py $network_id $resolution $method ${based_on}

                echo "==========================="
                echo " "
            done
        done
    done
done

# ===================================