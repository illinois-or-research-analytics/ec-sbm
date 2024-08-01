#!/bin/bash
#SBATCH --time=1:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/slurm-%j.out
#SBATCH --job-name="compare_simulators"
#SBATCH --partition=folkvangr
#SBATCH --mem=8G

SBM_V1=true
SBM_V2=true
ABCD=false

COMP_CL_001=true
COMP_FU_001=true

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
        --output-dir output/mod_sbmmcsprev1_sbm/ \
        --resolution k10
    fi 

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/ikc_cm data/networks/sbm/ikc_cm \
        --output-dir output/mod_sbmmcspre_sbm/ \
        --resolution k10
    fi

    if $SBM_V1 && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "SBM-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/sbmmcspres/ikc_cm \
        --output-dir output/mod_sbmmcsprev1_sbmmcspre/ \
        --resolution k10
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/ikc_cm data/networks/abcd/ikc_cm \
        --output-dir output/mod_sbm_abcd/ \
        --resolution k10

    python network_evaluation/compare_simulators_2.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/ikc_cm data/networks/abcd/ikc_cm \
        --output-dir output/mod_abcdmcspre_abcd/ \
        --resolution k10
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/abcdta4/ikc_cm \
        --output-dir output/mod_sbmmcsprev1_abcdmcspre/ \
        --resolution k10
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/ikc_cm data/networks/abcdta4/ikc_cm \
        --output-dir output/mod_sbmmcspre_abcdmcspre/ \
        --resolution k10
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "SBM" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/sbm/ikc_cm \
        --output-dir output/mod_sbmmcsprev1_sbm/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcsprev1_sbm/tables \
        --output output/mod_sbmmcsprev1_sbm/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "SBM" \
        --roots data/networks/sbmmcspres/ikc_cm data/networks/sbm/ikc_cm \
        --output-dir output/mod_sbmmcspre_sbm/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcspre_sbm/tables \
        --output output/mod_sbmmcspre_sbm/plots
    fi

    if $ABCD; then
    python network_evaluation/compare_simulators.py \
        --names "SBM" "ABCD" \
        --roots data/networks/sbm/ikc_cm data/networks/abcd/ikc_cm \
        --output-dir output/mod_sbm_abcd/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbm_abcd/tables \
        --output output/mod_sbm_abcd/plots

    python network_evaluation/compare_simulators.py \
        --names "ABCD-MCS(pre)" "ABCD" \
        --roots data/networks/abcdta4/ikc_cm data/networks/abcd/ikc_cm \
        --output-dir output/mod_abcdmcspre_abcd/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_abcdmcspre_abcd/tables \
        --output output/mod_abcdmcspre_abcd/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcsprev1/ikc_cm data/networks/abcdta4/ikc_cm \
        --output-dir output/mod_sbmmcsprev1_abcdmcspre/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcsprev1_abcdmcspre/tables \
        --output output/mod_sbmmcsprev1_abcdmcspre/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
        --roots data/networks/sbmmcspres/ikc_cm data/networks/abcdta4/ikc_cm \
        --output-dir output/mod_sbmmcspre_abcdmcspre/ \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcspre_abcdmcspre/tables \
        --output output/mod_sbmmcspre_abcdmcspre/plots
    fi

fi

# ===========================================

if $COMP_FU_K10; then
    if $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/ikc_cm data/networks/sbm+o/ikc_cm \
        --output-dir output/mod_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution k10
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/ikc_cm data/networks/sbm+o/ikc_cm \
        --output-dir output/mod_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution k10
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
        --output-dir output/mod_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution k10
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators_2.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
        --output-dir output/mod_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution k10
    fi

    # ===

    if $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "SBM+o" \
        --roots data/networks/sbmmcsprev1+o/ikc_cm data/networks/sbm+o/ikc_cm \
        --output-dir output/mod_sbmmcsprev1+o_sbm+o/ \
        --with-outliers \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcsprev1+o_sbm+o/tables \
        --output output/mod_sbmmcsprev1+o_sbm+o/plots
    fi

    if $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "SBM+o" \
        --roots data/networks/sbmmcspres+o/ikc_cm data/networks/sbm+o/ikc_cm \
        --output-dir output/mod_sbmmcspre+o_sbm+o/ \
        --with-outliers \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcspre+o_sbm+o/tables \
        --output output/mod_sbmmcspre+o_sbm+o/plots
    fi

    if $ABCD && $SBM_V1; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)-V1+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcsprev1+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
        --output-dir output/mod_sbmmcsprev1+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcsprev1+o_abcdmcspre+o/tables \
        --output output/mod_sbmmcsprev1+o_abcdmcspre+o/plots
    fi

    if $ABCD && $SBM_V2; then
    python network_evaluation/compare_simulators.py \
        --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
        --roots data/networks/sbmmcspres+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
        --output-dir output/mod_sbmmcspre+o_abcdmcspre+o/ \
        --with-outliers \
        --resolution k10

    python network_evaluation/gen_bar_graph_with_err.py \
        --root output/mod_sbmmcspre+o_abcdmcspre+o/tables \
        --output output/mod_sbmmcspre+o_abcdmcspre+o/plots
    fi

fi

echo "Done"