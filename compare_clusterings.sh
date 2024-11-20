#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/clusterings/slurm-%j.out
#SBATCH --job-name="compare_clustering"
#SBATCH --partition=tallis
#SBATCH --mem=8G

for method in sbmmcsprev1+o+eL1 abcdta4+o # sbmmcsprev1+o+eL1 abcdta4+o
do
    python network_evaluation/compare_simulators_3.py \
        --names \
            "InfoMap+CM(no-filter)" \
            "IKC(10)+CM(no-filter)" \
            "Leiden-CPM(0.1)+CM(no-filter)" \
            "Leiden-CPM(0.01)+CM(no-filter)" \
            "Leiden-CPM(0.001)+CM(no-filter)" \
            "Leiden-Mod+CM(no-filter)" \
            "InfoMap+CC" \
            "IKC(10)+CC" \
            "Leiden-CPM(0.1)" \
            "Leiden-CPM(0.01)" \
            "Leiden-CPM(0.001)" \
            "Leiden-Mod" \
        --roots \
            data/stats/${method}/infomap_nofiltcm \
            data/stats/${method}/ikc_nofiltcm \
            data/stats/${method}/leiden_cpm_nofiltcm \
            data/stats/${method}/leiden_cpm_nofiltcm \
            data/stats/${method}/leiden_cpm_nofiltcm \
            data/stats/${method}/leiden_mod_nofiltcm \
            data/stats/${method}/infomap_cc \
            data/stats/${method}/ikc_cc \
            data/stats/${method}/leiden_cpm \
            data/stats/${method}/leiden_cpm \
            data/stats/${method}/leiden_cpm \
            data/stats/${method}/leiden_mod \
        --resolution \
            infomap_nofiltcm \
            k10 \
            leiden.1 \
            leiden.01 \
            leiden.001 \
            leidenmod \
            infomap_cc \
            k10 \
            leiden.1 \
            leiden.01 \
            leiden.001 \
            leidenmod \
        --output-dir output/val_cl/${method}/cpm_ikc_mod_infomap/ \
        --network-whitelist-fp data/networks_val.txt \
        --num-replicates 1
done



echo "Done"