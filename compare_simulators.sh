python network_evaluation/compare_simulators.py \
    --names "SBM-MCS(pre)" "ABCD-MCS(pre)" \
    --roots data/networks/sbmmcspre/leiden_cpm_cm data/networks/abcdta4/leiden_cpm_cm \
    --output-dir output/sbmmcspre_abcdmcspre/

python network_evaluation/gen_bar_graph_with_err.py \
    --root output/sbmmcspre_abcdmcspre/tables/ \
    --output output/sbmmcspre_abcdmcspre/plots/

python network_evaluation/compare_simulators.py \
    --names "SBM-MCS(pre)" "SBM-MCS(post)" \
    --roots data/networks/sbmmcspre/leiden_cpm_cm data/networks/sbmmcspost/leiden_cpm_cm \
    --output-dir output/sbmmcspre_sbmmcspost/

python network_evaluation/gen_bar_graph_with_err.py \
    --root output/sbmmcspre_sbmmcspost/tables/ \
    --output output/sbmmcspre_sbmmcspost/plots/