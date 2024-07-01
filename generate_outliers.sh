#!/bin/bash
#SBATCH --time=168:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="outliers"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=0
end=0

for based_on in leiden_cpm_cm #leiden_cpm_cm leiden_cpm
do
    for network_id in $(cat data/networks.txt) cit_hepph cit_patents wiki_topcats wiki_talk orkut cen # cit_hepph cit_patents wiki_topcats wiki_talk orkut cen $(cat data/networks.txt)
    do
        for resolution in .001 # .0001 .001 .01
        do
            orig_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"

            edgelist_fn="${orig_dir}/edge.dat"
            clustering_fn="${orig_dir}/com.dat"

            echo ${orig_dir}
            echo "============================================"

            reps_dir="data/networks/outliers/${based_on}/${network_id}/leiden${resolution}/"
            echo $reps_dir

            for seed in $(seq ${start} ${end})
            do
                dir="${reps_dir}/${seed}/"

                echo "============================"
                echo $dir

                echo "Generating network"

                if [ ! -d ${dir} ]; then
                    python generate_outliers.py \
                        --orig-edgelist ${edgelist_fn} \
                        --orig-clustering ${clustering_fn} \
                        --output-folder ${dir}
                fi
            done
            echo "============================"
            echo ""
        done
    done
done