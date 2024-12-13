#!/bin/bash
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compute_gt_stats/slurm-%j.out
#SBATCH --job-name="gtstats_orig"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================
        
for network_id in $(cat data/networks_val.txt) # $(cat data/networks_train.txt) $(cat data/networks_val.txt) $(cat data/networks_test.txt)
do  
    echo "============================"
    input_dir="data/networks/orig/sbm/${network_id}/sbm/"
    output_stat_dir="data/stats/orig/network_only/${network_id}/"
    echo ${input_dir}

    if [ ! -f ${input_dir}/edge.dat ]; then
        echo "Error: ${input_dir}/edge.dat not found"
        continue
    fi

    python network_evaluation/compute_gt_stats.py \
        --input ${input_dir}/edge.dat \
        --output ${output_stat_dir}
done