#!/bin/bash
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --job-name="gen_network"
#SBATCH --partition=tallis

# for method in abcdta2
# do
#     for network_id in cen #wiki_topcats cit_patents cit_hepph wiki_talk oc
#     do
#         for resolution in .1 #.001 .01 .1
#         do
#             echo "=> $network_id at $resolution using $method <="

#             echo "======"

#             echo "Generating..."
#             python gen_abcdta.py $network_id $resolution $method

#             echo "======"

#             echo "Computing statistics..."
#             python compute_stats.py $network_id $resolution $method

#             echo "======"

#             python emulate-real-nets/estimate_properties_networkit.py \
#                     -n "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/edge.dat" \
#                     -c "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/com.dat" \
#                     -o "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/stats.json"

#             echo "======"

#             python compute_upperbound.py $network_id $resolution $method

#             python compute_potential_connectivity.py $network_id $resolution $method

#             python compute_wiring_efficiency.py $network_id $resolution $method

#             echo "==========================="
#             echo " "
#         done
#     done
# done

# ===================================

network_id=cen
resolution=.01
method=abcdta2

python gen_abcdta.py $network_id $resolution $method
python compute_stats.py $network_id $resolution $method
python emulate-real-nets/estimate_properties_networkit.py \
    -n "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/edge.dat" \
    -c "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/com.dat" \
    -o "data/networks/${method}/${network_id}_${method}_networks/${network_id}_leiden${resolution}_${method}/stats.json"
python compute_upperbound.py $network_id $resolution $method
python compute_potential_connectivity.py $network_id $resolution $method
python compute_wiring_efficiency.py $network_id $resolution $method