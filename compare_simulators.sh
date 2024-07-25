#!/bin/bash
#SBATCH --time=72:00:00
#SBATCH --nodes=1
#SBATCH --output=slurm_output/compare/slurm-%j.out
#SBATCH --job-name="compare_simulators"
#SBATCH --partition=tallis
#SBATCH --mem=64G

COMP_CL_001=true
COMP_FU_001=true

COMP_CL_01=false
COMP_FU_01=false

COMP_CL_MOD=false
COMP_FU_MOD=false

COMP_CL_K10=false
COMP_FU_K10=false

if $COMP_CL_001; then
python network_evaluation/compare_simulators_2.py \
    --names "SBM" "ABCD" \
    --roots data/networks/sbm/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
    --output-dir output/sbm_abcd/ \
    --resolution leiden.001

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)" "SBM" \
    --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
    --output-dir output/sbmmcspre_sbm/ \
    --resolution leiden.001

python network_evaluation/compare_simulators_2.py \
    --names "ABCD-MCS(pre)" "ABCD" \
    --roots data/networks/abcdta4/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
    --output-dir output/abcdmcspre_abcd/ \
    --resolution leiden.001

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
    --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
    --output-dir output/sbmmcspre_abcdmcspre/ \
    --resolution leiden.001
fi

# ===========================================

if $COMP_FU_001; then
python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)+o" "SBM+o" \
    --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
    --output-dir output/sbmmcspre+o_sbm+o/ \
    --with-outliers \
    --resolution leiden.001

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
    --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
    --output-dir output/sbmmcspre+o_abcdmcspre+o/ \
    --with-outliers \
    --resolution leiden.001
fi

# ===========================================

if $COMP_CL_01; then
python network_evaluation/compare_simulators_2.py \
    --names "SBM" "ABCD" \
    --roots data/networks/sbm/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
    --output-dir output/01_sbm_abcd/ \
    --resolution leiden.01

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)" "SBM" \
    --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/sbm/leiden_cpm_cm \
    --output-dir output/01_sbmmcspre_sbm/ \
    --resolution leiden.01

python network_evaluation/compare_simulators_2.py \
    --names "ABCD-MCS(pre)" "ABCD" \
    --roots data/networks/abcdta4/leiden_cpm_cm data/networks/abcd/leiden_cpm_cm \
    --output-dir output/01_abcdmcspre_abcd/ \
    --resolution leiden.01

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
    --roots data/networks/sbmmcspres/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
    --output-dir output/01_sbmmcspre_abcdmcspre/ \
    --resolution leiden.01
fi

# ===========================================

if $COMP_FU_01; then
python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)+o" "SBM+o" \
    --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/sbm+o/leiden_cpm_cm \
    --output-dir output/01_sbmmcspre+o_sbm+o/ \
    --with-outliers \
    --resolution leiden.01

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
    --roots data/networks/sbmmcspres+o/leiden_cpm_cm data/networks/abcdta4+o/leiden_cpm_cm \
    --output-dir output/01_sbmmcspre+o_abcdmcspre+o/ \
    --with-outliers \
    --resolution leiden.01
fi

# ===========================================

if $COMP_CL_MOD; then
python network_evaluation/compare_simulators_2.py \
    --names "SBM" "ABCD" \
    --roots data/networks/sbm/leiden_mod_cm data/networks/abcd/leiden_mod_cm \
    --output-dir output/mod_sbm_abcd/ \
    --resolution leidenmod

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)" "SBM" \
    --roots data/networks/sbmmcspres/leiden_mod_cm data/networks/sbm/leiden_mod_cm \
    --output-dir output/mod_sbmmcspre_sbm/ \
    --resolution leidenmod

python network_evaluation/compare_simulators_2.py \
    --names "ABCD-MCS(pre)" "ABCD" \
    --roots data/networks/abcdta4/leiden_mod_cm data/networks/abcd/leiden_mod_cm \
    --output-dir output/mod_abcdmcspre_abcd/ \
    --resolution leidenmod

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
    --roots data/networks/sbmmcspres/leiden_mod_cm data/networks/abcdta4/leiden_mod_cm \
    --output-dir output/mod_sbmmcspre_abcdmcspre/ \
    --resolution leidenmod
fi

# ===========================================

if $COMP_FU_MOD; then
python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)+o" "SBM+o" \
    --roots data/networks/sbmmcspres+o/leiden_mod_cm data/networks/sbm+o/leiden_mod_cm \
    --output-dir output/mod_sbmmcspre+o_sbm+o/ \
    --with-outliers \
    --resolution leidenmod

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
    --roots data/networks/sbmmcspres+o/leiden_mod_cm data/networks/abcdta4+o/leiden_mod_cm \
    --output-dir output/mod_sbmmcspre+o_abcdmcspre+o/ \
    --with-outliers \
    --resolution leidenmod
fi

# ===========================================

if $COMP_CL_K10; then
python network_evaluation/compare_simulators_2.py \
    --names "SBM" "ABCD" \
    --roots data/networks/sbm/ikc_cm data/networks/abcd/ikc_cm \
    --output-dir output/k10_sbm_abcd/ \
    --resolution k10

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)" "SBM" \
    --roots data/networks/sbmmcspres/ikc_cm data/networks/sbm/ikc_cm \
    --output-dir output/k10_sbmmcspre_sbm/ \
    --resolution k10

python network_evaluation/compare_simulators_2.py \
    --names "ABCD-MCS(pre)" "ABCD" \
    --roots data/networks/abcdta4/ikc_cm data/networks/abcd/ikc_cm \
    --output-dir output/k10_abcdmcspre_abcd/ \
    --resolution k10

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
    --roots data/networks/sbmmcspres/ikc_cm data/networks/abcdta4/ikc_cm \
    --output-dir output/k10_sbmmcspre_abcdmcspre/ \
    --resolution k10
fi

# ===========================================

if $COMP_FU_K10; then
python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)+o" "SBM+o" \
    --roots data/networks/sbmmcspres+o/ikc_cm data/networks/sbm+o/ikc_cm \
    --output-dir output/k10_sbmmcspre+o_sbm+o/ \
    --with-outliers \
    --resolution k10

python network_evaluation/compare_simulators_2.py \
    --names "SBM-MCS(pre)+o" "ABCD-MCS(pre)+o" \
    --roots data/networks/sbmmcspres+o/ikc_cm data/networks/abcdta4+o/ikc_cm \
    --output-dir output/k10_sbmmcspre+o_abcdmcspre+o/ \
    --with-outliers \
    --resolution k10
fi

echo "Done"