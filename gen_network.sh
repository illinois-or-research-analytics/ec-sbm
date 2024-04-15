#!/bin/bash
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --job-name="gen_network"
#SBATCH --partition=tallis

# ===================================

network_id=cit_hepph
resolution=.001
method=abcdta4
based_on=leiden_cpm

python gen_${method}.py $network_id $resolution ${method} ${based_on}
python compute_stats.py $network_id $resolution ${method} ${based_on}
python emulate-real-nets/estimate_properties_networkit.py \
    -n "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/edge.dat" \
    -c "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/com.dat" \
    -o "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/stats.json"
python compute_upperbound.py $network_id $resolution ${method} ${based_on}
python compute_potential_connectivity.py $network_id $resolution ${method} ${based_on}
python compute_wiring_efficiency.py $network_id $resolution ${method} ${based_on}
python compute_degree_dist.py ${network_id} ${resolution} ${method} ${based_on}

# ===================================

# for method in abcdta3 #abcd abcdta2 abcdta3
# do
#     for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
#     do
#         for network_id in wiki_talk orkut #cit_hepph cit_patents wiki_topcats wiki_talk orkut
#         do
#             for resolution in .0001 .001 .01 #.0001 .001 .01
#             do
#                 echo "=> $network_id at $resolution using $method based on $based_on <="

#                 echo "======"
#                 echo "Generating..."
                
#                 python gen_${method}.py $network_id $resolution ${method} ${based_on}

#                 echo "======"

#                 echo "Computing statistics..."

#                 python compute_stats.py $network_id $resolution $method ${based_on}

#                 echo "======"

#                 python emulate-real-nets/estimate_properties_networkit.py \
#                         -n "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/edge.dat" \
#                         -c "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/com.dat" \
#                         -o "data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/stats.json"

#                 echo "======"

#                 python compute_upperbound.py $network_id $resolution $method ${based_on}

#                 python compute_potential_connectivity.py $network_id $resolution $method ${based_on}

#                 python compute_wiring_efficiency.py $network_id $resolution $method ${based_on}

#                 python compute_degree_dist.py ${network_id} ${resolution} ${method} ${based_on}

#                 echo "==========================="
#                 echo " "
#             done
#         done
#     done
# done

# ===================================