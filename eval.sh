#!/bin/bash
#SBATCH --time=48:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="eval"
#SBATCH --partition=eng-research-gpu
#SBATCH --mem=64G

# ===================================

T=9

for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
do
    for network_id in cit_hepph cit_patents wiki_talk #cit_hepph cit_patents wiki_topcats wiki_talk orkut
    do
        for resolution in .0001 .001 .01 #.0001 .001 .01
        do
            orig_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"
            orig_outdir="data/stats/orig/${based_on}/${network_id}/leiden${resolution}/"

            echo "=================================================="
            echo $orig_dir

            # python network_evaluation/compute_stats.py \
            #         --input-network ${orig_dir}/edge.dat \
            #         --input-clustering ${orig_dir}/com.dat \
            #         --output-folder ${orig_outdir} \
            #         --overwrite

            for method in abcdta4 abcd #abcd abcdta4
            do
                reps_dir="data/networks/${method}/${based_on}/${network_id}/leiden${resolution}/"

                for seed in $(seq 1 $T)
                do
                    dir="${reps_dir}/${seed}/"

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

                python network_evaluation/compare_stats.py \
                    --input-network-folder ${orig_outdir} \
                    --input-replicates-folder ${reps_dir} \
                    --output-folder ${reps_dir}

                echo "=================================================="
                echo ""
            done
        done
    done
done