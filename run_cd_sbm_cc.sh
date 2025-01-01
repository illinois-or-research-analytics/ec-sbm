#!/bin/bash
#SBATCH --time=3-00:00:00
#SBATCH --output=slurm_output/cd/sbm_cc/slurm-%j.out
#SBATCH --job-name="cdsbmcc_val"
#SBATCH --partition=tallis
#SBATCH --mem=64G

# ===================================

start=0
end=0
# module load gcc/11.2.0
# module load cmake/3.26.3
for clustering in leiden_mod_nofiltcm leiden_cpm_nofiltcm # leiden_cpm leiden_mod ikc infomap
do
    for resolution in leidenmod leiden.1 # leiden.0001 leiden.001 leiden.01 leiden.1 k10 leidenmod infomap
    do
        if [ $clustering = "leiden_cpm_cm" ] || [ $clustering = "leiden_cpm" ] || [ $clustering = "leiden_cpm_nofiltcm" ]; then
            if [ ! $resolution = "leiden.0001" ] && [ ! $resolution = "leiden.001" ] && [ ! $resolution = "leiden.01" ] && [ ! $resolution = "leiden.1" ]; then
                continue
            fi
        elif [ $clustering = "leiden_mod_cm" ] || [ $clustering = "leiden_mod" ] || [ $clustering = "leiden_mod_nofiltcm" ]; then
            if [ ! $resolution = "leidenmod" ]; then
                continue
            fi
        elif [ $clustering = "ikc_cm" ] || [ $clustering = "ikc_cc" ] || [ $clustering = "ikc_nofiltcm" ]; then
            if [ ! $resolution = "k10" ]; then
                continue
            fi
        elif [ $clustering = "infomap" ] || [ $clustering = "infomap_nofiltcm" ]; then
            if [ ! $resolution = "infomap" ]; then
                continue
            fi
        elif [ $clustering = "sbm_cc" ] || [ $clustering = "sbm_wcc" ] || [ $clustering = "sbm" ]; then
            if [ ! $resolution = "sbm" ]; then
                continue
            fi
        fi

        for network_id in $(cat data/networks_val.txt) # $(cat data/networks_train.txt) $(cat data/networks_val.txt) $(cat data/networks_test.txt)  
        do
            for method in sbmmcsprev1+o+eL1
            do
                for seed in $(seq ${start} ${end})
                do
                    echo "============================"
                    echo ${network_id} ${method} ${clustering} ${resolution} ${seed}
                    
                    inp_dir="data/community_detection/${method}/${clustering}/${network_id}/${resolution}/0/sbm/sbm/"
                    
                    inp_clustering_fp="${inp_dir}/com.tsv"
                    if [ ! -f ${inp_clustering_fp} ]; then
                        echo "Input clustering ${inp_clustering_fp} does not exist"
                        continue
                    fi

                    inp_edgelist_fp="${inp_dir}/edge.tsv"
                    if [ ! -f ${inp_edgelist_fp} ]; then
                        echo "Edgelist ${inp_edgelist_fp} does not exist"
                        infomap_dir=$(ls -d ${inp_dir}/../../infomap/infomap/*/)
                        infomap_fp=$(ls ${infomap_dir}/S1_*.tsv)
                        if [ ! -f ${infomap_fp} ]; then
                            echo "Infomap clustering ${infomap_fp} does not exist"
                            continue
                        fi
                        cp "${infomap_fp}" "${inp_edgelist_fp}"
                    fi

                    out_dir="data/community_detection/${method}/${clustering}/${network_id}/${resolution}/0/sbm_cc/sbm/"
                    if [ -f ${out_dir}/done ]; then
                        continue
                    fi

                    if [ ! -d ${out_dir} ]; then
                        mkdir -p ${out_dir}
                    fi
                    
                    ./constrained-clustering/constrained_clustering MincutOnly \
                        --edgelist ${inp_edgelist_fp} \
                        --existing-clustering ${inp_clustering_fp} \
                        --num-processors 1 \
                        --output-file ${out_dir}/com.tsv \
                        --log-file ${out_dir}/cc.log \
                        --log-level 1 \
                        --connectedness-criterion 0

                    if [ -f ${out_dir}/com.tsv ]; then
                        touch ${out_dir}/done
                    fi
                done
            done   
        done
    done
done
