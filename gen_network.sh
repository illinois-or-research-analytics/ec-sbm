#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --job-name="gen_network"
#SBATCH --partition=tallis

for network_id in cen wiki_talk wiki_topcats cit_hepph cit_patents oc
do
    for resolution in .001 .01 .1
    do
        echo "Generating $network_id at $resolution..."
        python gen_abcd.py $network_id $resolution
        echo "==========================="
    done
done

# python gen_abcds.py cen .001

# python gen_abcd.py wiki_talk .001