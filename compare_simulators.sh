#!/bin/bash
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/simulators/slurm-%j.out
#SBATCH --job-name="compare_simulators"
#SBATCH --partition=tallis
#SBATCH --mem=8G

for clustering in infomap_nofiltcm infomap_cc # leiden_cpm_nofiltcm leiden_mod_nofiltcm ikc_nofiltcm infomap_nofiltcm leiden_cpm leiden_mod ikc_cc infomap_cc
do
    for resolution in leiden.1 leiden.01 leiden.001 leidenmod k10 infomap # leiden.001 leiden.01 leiden.1 k10 leidenmod infomap
    do
        # Matching clustering with resolution
        if [ $clustering = "leiden_cpm_cm" ] || [ $clustering = "leiden_cpm" ] || [ $clustering = "leiden_cpm_nofiltcm" ]; then
            if [ ! $resolution = "leiden.001" ] && [ ! $resolution = "leiden.01" ] && [ ! $resolution = "leiden.1" ]; then
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
        elif [ $clustering = "infomap_cc" ] || [ $clustering = "infomap_nofiltcm" ]; then
            if [ ! $resolution = "infomap" ]; then
                continue
            fi
        fi

        python network_evaluation/compare_simulators_2.py \
            --names \
                "SBM-MCS(pre)+o" \
                "SBM-MCS(pre)+o+eL1" \
                "SBM-MCS(pre)+o+eL2" \
            --roots \
                data/stats/sbmmcsprev1+o/${clustering} \
                data/stats/sbmmcsprev1+o+eL1/${clustering} \
                data/stats/sbmmcsprev1+o+eL2/${clustering} \
            --output-dir output/val/${clustering}/${resolution}/sbmmcspre/ \
            --resolution ${resolution} \
            --network-whitelist-fp data/networks_val.txt \
            --num-replicates 1

        # python network_evaluation/compare_simulators_2.py \
        #     --names \
        #         "ABCD-MCS(pre)+o" \
        #         "ABCD-MCS(pre)+o+eL1" \
        #         "ABCD-MCS(pre)+o+eL2" \
        #     --roots \
        #         data/stats/abcdta4+o/${clustering} \
        #         data/stats/abcdta4+o+eL1/${clustering} \
        #         data/stats/abcdta4+o+eL2/${clustering} \
        #     --output-dir output/val/${clustering}/${resolution}/abcdmcspre/ \
        #     --resolution ${resolution} \
        #     --network-whitelist-fp data/networks_val.txt \
        #     --num-replicates 1

        python network_evaluation/compare_simulators_2.py \
            --names \
                "SBM+oSBM" \
                "SBM-MCS(pre)+oSBM+eV1" \
                "RECCSv1+OS1" \
            --roots \
                data/stats/sbm+o/${clustering} \
                data/stats/sbmmcsprev1+o+eL1/${clustering} \
                data/stats/RECCSv1_OS1/${clustering} \
            --output-dir output/val/${clustering}/${resolution}/sbm_sbmmcspre_reccs/ \
            --resolution ${resolution} \
            --network-whitelist-fp data/networks_val.txt \
            --num-replicates 1

        # python network_evaluation/compare_simulators_2.py \
        #     --names \
        #         "ABCD+o" \
        #         "ABCD-MCS(pre)+o" \
        #         "RECCSv1+OS1" \
        #     --roots \
        #         data/stats/abcd+o/${clustering} \
        #         data/stats/abcdta4+o/${clustering} \
        #         data/stats/RECCSv1_OS1/${clustering} \
        #     --output-dir output/val/${clustering}/${resolution}/abcd_abcdmcspre_reccs/ \
        #     --resolution ${resolution} \
        #     --network-whitelist-fp data/networks_val.txt \
        #     --num-replicates 1

        # python network_evaluation/compare_simulators_2.py \
        #     --names \
        #         "ABCD-MCS(pre)+o" \
        #         "RECCSv1+OS1" \
        #     --roots \
        #         data/stats/abcdta4+o/${clustering} \
        #         data/stats/RECCSv1_OS1/${clustering} \
        #     --output-dir output/val/${clustering}/${resolution}/abcdmcspre_reccs/ \
        #     --resolution ${resolution} \
        #     --network-whitelist-fp data/networks_val.txt \
        #     --num-replicates 1
    done
done

SBM_V1=true
SBM_V2=false
ABCD=true

COMP_CL_001=false
COMP_FU_001=false

COMP_CL_01=false
COMP_FU_01=false

COMP_CL_MOD=false
COMP_FU_MOD=false

COMP_CL_K10=false
COMP_FU_K10=false

if $COMP_CL_001; then
    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1_sbm/ \
        --resolution leiden.001
    fi 

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
        --output-dir output/001_sbmmcspre_sbm/ \
        --resolution leiden.001
    fi

    if $SBM_V1 && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/sbmmcspres/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1_sbmmcspre/ \
        --resolution leiden.001
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
        --output-dir output/001_sbm_abcd/ \
        --resolution leiden.001

    python network_evaluation/compare_simulators_2.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
        --output-dir output/001_abcdmcspre_abcd/ \
        --resolution leiden.001
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1_abcdmcspre/ \
        --resolution leiden.001
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
        --output-dir output/001_sbmmcspre_abcdmcspre/ \
        --resolution leiden.001
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1_sbm/ \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbmmcsprev1_sbm/tables \
        --output output/001_sbmmcsprev1_sbm/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
        --output-dir output/001_sbmmcspre_sbm/ \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbmmcspre_sbm/tables \
        --output output/001_sbmmcspre_sbm/plots
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
        --output-dir output/001_sbm_abcd/ \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbm_abcd/tables \
        --output output/001_sbm_abcd/plots

    python network_evaluation/compare_simulators.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
        --output-dir output/001_abcdmcspre_abcd/ \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_abcdmcspre_abcd/tables \
        --output output/001_abcdmcspre_abcd/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1_abcdmcspre/ \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbmmcsprev1_abcdmcspre/tables \
        --output output/001_sbmmcsprev1_abcdmcspre/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
        --output-dir output/001_sbmmcspre_abcdmcspre/ \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbmmcspre_abcdmcspre/tables \
        --output output/001_sbmmcspre_abcdmcspre/plots
    fi

fi

# ===========================================

if $COMP_FU_001; then
    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution leiden.001
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
        --output-dir output/001_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution leiden.001
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leiden.001
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
        --output-dir output/001_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leiden.001
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbmmcsprev1+o_sbm+o/tables \
        --output output/001_sbmmcsprev1+o_sbm+o/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
        --output-dir output/001_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbmmcspre+o_sbm+o/tables \
        --output output/001_sbmmcspre+o_sbm+o/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
        --output-dir output/001_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbmmcsprev1+o_abcdmcspre+o/tables \
        --output output/001_sbmmcsprev1+o_abcdmcspre+o/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
        --output-dir output/001_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leiden.001

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/001_sbmmcspre+o_abcdmcspre+o/tables \
        --output output/001_sbmmcspre+o_abcdmcspre+o/plots
    fi

fi

# ===========================================

if $COMP_CL_01; then

    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1_sbm/ \
        --resolution leiden.01
    fi 

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
        --output-dir output/01_sbmmcspre_sbm/ \
        --resolution leiden.01
    fi

    if $SBM_V1 && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/sbmmcspres/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1_sbmmcspre/ \
        --resolution leiden.01
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
        --output-dir output/01_sbm_abcd/ \
        --resolution leiden.01

    python network_evaluation/compare_simulators_2.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
        --output-dir output/01_abcdmcspre_abcd/ \
        --resolution leiden.01
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1_abcdmcspre/ \
        --resolution leiden.01
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
        --output-dir output/01_sbmmcspre_abcdmcspre/ \
        --resolution leiden.01
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1_sbm/ \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbmmcsprev1_sbm/tables \
        --output output/01_sbmmcsprev1_sbm/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
        --output-dir output/01_sbmmcspre_sbm/ \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbmmcspre_sbm/tables \
        --output output/01_sbmmcspre_sbm/plots
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
        --output-dir output/01_sbm_abcd/ \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbm_abcd/tables \
        --output output/01_sbm_abcd/plots

    python network_evaluation/compare_simulators.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
        --output-dir output/01_abcdmcspre_abcd/ \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_abcdmcspre_abcd/tables \
        --output output/01_abcdmcspre_abcd/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1_abcdmcspre/ \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbmmcsprev1_abcdmcspre/tables \
        --output output/01_sbmmcsprev1_abcdmcspre/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
        --output-dir output/01_sbmmcspre_abcdmcspre/ \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbmmcspre_abcdmcspre/tables \
        --output output/01_sbmmcspre_abcdmcspre/plots
    fi

fi

# ===========================================

if $COMP_FU_01; then
    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution leiden.01
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
        --output-dir output/01_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution leiden.01
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leiden.01
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
        --output-dir output/01_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leiden.01
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbmmcsprev1+o_sbm+o/tables \
        --output output/01_sbmmcsprev1+o_sbm+o/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
        --output-dir output/01_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbmmcspre+o_sbm+o/tables \
        --output output/01_sbmmcspre+o_sbm+o/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
        --output-dir output/01_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbmmcsprev1+o_abcdmcspre+o/tables \
        --output output/01_sbmmcsprev1+o_abcdmcspre+o/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
        --output-dir output/01_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leiden.01

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/01_sbmmcspre+o_abcdmcspre+o/tables \
        --output output/01_sbmmcspre+o_abcdmcspre+o/plots
    fi

fi

# ===========================================

if $COMP_CL_MOD; then

    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/leiden_mod_cm data/networks/sbm/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1_sbm/ \
        --resolution leidenmod
    fi 

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/leiden_mod_cm data/networks/sbm/leiden_mod_cm \
        --output-dir output/mod_sbmmcspre_sbm/ \
        --resolution leidenmod
    fi

    if $SBM_V1 && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_mod_cm data/networks/sbmmcspres/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1_sbmmcspre/ \
        --resolution leidenmod
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/leiden_mod_cm data/networks/abcd/leiden_mod_cm \
        --output-dir output/mod_sbm_abcd/ \
        --resolution leidenmod

    python network_evaluation/compare_simulators_2.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/leiden_mod_cm data/networks/abcd/leiden_mod_cm \
        --output-dir output/mod_abcdmcspre_abcd/ \
        --resolution leidenmod
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_mod_cm data/networks/abcdta4/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1_abcdmcspre/ \
        --resolution leidenmod
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/leiden_mod_cm data/networks/abcdta4/leiden_mod_cm \
        --output-dir output/mod_sbmmcspre_abcdmcspre/ \
        --resolution leidenmod
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/leiden_mod_cm data/networks/sbm/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1_sbm/ \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcsprev1_sbm/tables \
        --output output/mod_sbmmcsprev1_sbm/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/leiden_mod_cm data/networks/sbm/leiden_mod_cm \
        --output-dir output/mod_sbmmcspre_sbm/ \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcspre_sbm/tables \
        --output output/mod_sbmmcspre_sbm/plots
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/leiden_mod_cm data/networks/abcd/leiden_mod_cm \
        --output-dir output/mod_sbm_abcd/ \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbm_abcd/tables \
        --output output/mod_sbm_abcd/plots

    python network_evaluation/compare_simulators.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/leiden_mod_cm data/networks/abcd/leiden_mod_cm \
        --output-dir output/mod_abcdmcspre_abcd/ \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_abcdmcspre_abcd/tables \
        --output output/mod_abcdmcspre_abcd/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/leiden_mod_cm data/networks/abcdta4/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1_abcdmcspre/ \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcsprev1_abcdmcspre/tables \
        --output output/mod_sbmmcsprev1_abcdmcspre/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/leiden_mod_cm data/networks/abcdta4/leiden_mod_cm \
        --output-dir output/mod_sbmmcspre_abcdmcspre/ \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcspre_abcdmcspre/tables \
        --output output/mod_sbmmcspre_abcdmcspre/plots
    fi

fi

# ===========================================

if $COMP_FU_MOD; then
    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_mod_cm data/networks/sbm+o/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution leidenmod
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/leiden_mod_cm data/networks/sbm+o/leiden_mod_cm \
        --output-dir output/mod_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution leidenmod
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_mod_cm data/networks/abcdta4+o/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leidenmod
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/leiden_mod_cm data/networks/abcdta4+o/leiden_mod_cm \
        --output-dir output/mod_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leidenmod
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_mod_cm data/networks/sbm+o/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcsprev1+o_sbm+o/tables \
        --output output/mod_sbmmcsprev1+o_sbm+o/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/leiden_mod_cm data/networks/sbm+o/leiden_mod_cm \
        --output-dir output/mod_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcspre+o_sbm+o/tables \
        --output output/mod_sbmmcspre+o_sbm+o/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/leiden_mod_cm data/networks/abcdta4+o/leiden_mod_cm \
        --output-dir output/mod_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcsprev1+o_abcdmcspre+o/tables \
        --output output/mod_sbmmcsprev1+o_abcdmcspre+o/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/leiden_mod_cm data/networks/abcdta4+o/leiden_mod_cm \
        --output-dir output/mod_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution leidenmod

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcspre+o_abcdmcspre+o/tables \
        --output output/mod_sbmmcspre+o_abcdmcspre+o/plots
    fi

fi

# ===========================================

if $COMP_CL_K10; then
    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/sbm/ikc_cm \
        --output-dir output/k10_sbmmcsprev1_sbm/ \
        --resolution k10
    fi 

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/ikc_cm data/networks/sbm/ikc_cm \
        --output-dir output/k10_sbmmcspre_sbm/ \
        --resolution k10
    fi

    if $SBM_V1 && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/sbmmcspres/ikc_cm \
        --output-dir output/k10_sbmmcsprev1_sbmmcspre/ \
        --resolution k10
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/ikc_cm data/networks/abcd/ikc_cm \
        --output-dir output/k10_sbm_abcd/ \
        --resolution k10

    python network_evaluation/compare_simulators_2.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/ikc_cm data/networks/abcd/ikc_cm \
        --output-dir output/k10_abcdmcspre_abcd/ \
        --resolution k10
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/abcdta4/ikc_cm \
        --output-dir output/k10_sbmmcsprev1_abcdmcspre/ \
        --resolution k10
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/ikc_cm data/networks/abcdta4/ikc_cm \
        --output-dir output/k10_sbmmcspre_abcdmcspre/ \
        --resolution k10
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/sbm/ikc_cm \
        --output-dir output/k10_sbmmcsprev1_sbm/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbmmcsprev1_sbm/tables \
        --output output/k10_sbmmcsprev1_sbm/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/ikc_cm data/networks/sbm/ikc_cm \
        --output-dir output/k10_sbmmcspre_sbm/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbmmcspre_sbm/tables \
        --output output/k10_sbmmcspre_sbm/plots
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/ikc_cm data/networks/abcd/ikc_cm \
        --output-dir output/k10_sbm_abcd/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbm_abcd/tables \
        --output output/k10_sbm_abcd/plots

    python network_evaluation/compare_simulators.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/ikc_cm data/networks/abcd/ikc_cm \
        --output-dir output/k10_abcdmcspre_abcd/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_abcdmcspre_abcd/tables \
        --output output/k10_abcdmcspre_abcd/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/abcdta4/ikc_cm \
        --output-dir output/k10_sbmmcsprev1_abcdmcspre/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbmmcsprev1_abcdmcspre/tables \
        --output output/k10_sbmmcsprev1_abcdmcspre/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/ikc_cm data/networks/abcdta4/ikc_cm \
        --output-dir output/k10_sbmmcspre_abcdmcspre/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbmmcspre_abcdmcspre/tables \
        --output output/k10_sbmmcspre_abcdmcspre/plots
    fi

fi

# ===========================================

if $COMP_FU_K10; then
    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/ikc_cm data/networks/sbm+o/ikc_cm \
        --output-dir output/k10_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution k10
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/ikc_cm data/networks/sbm+o/ikc_cm \
        --output-dir output/k10_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution k10
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
        --output-dir output/k10_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution k10
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
        --output-dir output/k10_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution k10
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/ikc_cm data/networks/sbm+o/ikc_cm \
        --output-dir output/k10_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbmmcsprev1+o_sbm+o/tables \
        --output output/k10_sbmmcsprev1+o_sbm+o/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/ikc_cm data/networks/sbm+o/ikc_cm \
        --output-dir output/k10_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbmmcspre+o_sbm+o/tables \
        --output output/k10_sbmmcspre+o_sbm+o/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
        --output-dir output/k10_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbmmcsprev1+o_abcdmcspre+o/tables \
        --output output/k10_sbmmcsprev1+o_abcdmcspre+o/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
        --output-dir output/k10_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/k10_sbmmcspre+o_abcdmcspre+o/tables \
        --output output/k10_sbmmcspre+o_abcdmcspre+o/plots
    fi

fi

echo "Done"