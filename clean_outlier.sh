#!/bin/bash
#SBATCH --time=72:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/slurm-%j.out
#SBATCH --job-name="clean_outlier_test"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# network_id=cit_hepph
# resolution=.001
# based_on=leiden_cpm_cm

# input_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"
# output_dir="data/networks/orig_wo_outliers/${based_on}/${network_id}/leiden${resolution}/"

# python clean_outlier.py \
#     --input-network ${input_dir}/edge.dat \
#     --input-clustering ${input_dir}/com.dat \
#     --output-folder ${output_dir}

# ===================================

for based_on in leiden_cpm_cm leiden_cpm #leiden_cpm_cm leiden_cpm
do
    for network_id in wiki_talk #cit_hepph cit_patents wiki_topcats wiki_talk orkut cen
    do
        for resolution in .01 #.0001 .001 .01 .1 .5
        do
            input_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"
            output_dir="data/networks/orig_wo_outliers/${based_on}/${network_id}/leiden${resolution}/"

            echo "Cleaning outliers"
            echo "Input: ${input_dir}"
            echo "Output: ${output_dir}"

            python clean_outlier.py \
                --input-network ${input_dir}/edge.dat \
                --input-clustering ${input_dir}/com.dat \
                --output-folder ${output_dir}

            python test_clean_outlier.py \
                --output-network ${output_dir}/edge.dat \
                --output-clustering ${output_dir}/com.dat

            echo "=================================="
            echo ""
        done
    done
done

# ===================================

# for based_on in leiden_cpm_cm leiden_cpm #leiden_cpm_cm leiden_cpm
# do
#     for network_id in $(cat data/networks.txt)
#     do
#         # Ignore lines starting with #
#         if [[ $network_id == \#* ]]; then
#             continue
#         fi

#         for resolution in .001 #.0001 .001 .01 .1 .5
#         do
#             input_dir="data/networks/orig/${based_on}/${network_id}/leiden${resolution}/"
#             output_dir="data/networks/orig_wo_outliers/${based_on}/${network_id}/leiden${resolution}/"

#             echo "Cleaning outliers"
#             echo "Input: ${input_dir}"
#             echo "Output: ${output_dir}"

#             python clean_outlier.py \
#                 --input-network ${input_dir}/edge.dat \
#                 --input-clustering ${input_dir}/com.dat \
#                 --output-folder ${output_dir}

#             python test_clean_outlier.py \
#                 --output-network ${output_dir}/edge.dat \
#                 --output-clustering ${output_dir}/com.dat

#             echo "=================================="
#             echo ""
#         done
#     done
# done