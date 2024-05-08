#!/bin/bash
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --job-name="gen_network"
#SBATCH --partition=tallis

# ===================================

# network_id=cit_hepph
# resolution=.001
# method=abcdta4
# based_on=leiden_cpm_cm
T=10

for network_id in cit_hepph cit_patents #cit_hepph cit_patents wiki_topcats wiki_talk orkut
do
    for method in abcdta4 abcd #abcd abcdta4
    do
        for resolution in .0001 .001 .01 #.0001 .001 .01
        do
            for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
            do
                orig_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"
                orig_outdir="data/stats/orig/${based_on}/${network_id}/leiden${resolution}/"

                python network_evaluation/compute_stats.py \
                        --input-network ${orig_dir}/edge.dat \
                        --input-clustering ${orig_dir}/com.dat \
                        --output-folder ${orig_outdir} \
                        --overwrite

                for seed in 0 #$(seq 1 $T)
                do
                    dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/${seed}/"

                    echo "=================================="
                    echo $dir

                    # python gen_${method}.py \
                    #     --network-id ${network_id} \
                    #     --resolution $resolution \
                    #     --method ${method} \
                    #     --based_on ${based_on} \
                    #     --seed ${seed}

                    python network_evaluation/compute_stats.py \
                        --input-network ${dir}/edge.tsv \
                        --input-clustering ${dir}/com.tsv \
                        --output-folder ${dir} \
                        --overwrite

                    echo "=================================="
                    echo ""
                done
            done
        done
    done
done