# ec-sbm-v2: cluster_preserving_true_greedy vs stacked variants

Question: does plain `true_greedy` cleanup after
`cluster_preserving_true_greedy` recover stuck stubs without
regressing other stats? Does prepending `cluster_preserving_rewire`
help further? Does the answer change with bucket size?

Three matcher configurations, all on EC-SBM v2 with
`leiden-cpm-0.0001` reference clustering, 5 seeds per network:

| config | matcher stack |
|---|---|
| `cptg` | `cluster_preserving_true_greedy` (current v2 default) |
| `stack` | `cluster_preserving_true_greedy, true_greedy` |
| `rewire_stack` | `cluster_preserving_rewire, cluster_preserving_true_greedy, true_greedy` |

Buckets: **B0** = 10K–100K nodes (26 networks), **B1** = 100K–200K nodes
(7 networks). Aggregation is two-stage: stage 1 means over 5 seeds per
network; stage 2 means or paired Wilcoxon over the networks in the bucket.
Reported `n` is the number of networks. Wilcoxon p-value is two-sided;
`*` = p < 0.05, `**` = p < 0.01.

`SAD = |synth − ref|` (bounded scalars). `SRD = |synth − ref| / |synth|` (unbounded scalars).
`EMD` = Earth Mover's distance over synth/ref histograms; 0 = perfect.
`cluster_*`: rmse for continuous-valued stats, mean_l1 for count-valued ones; 0 = perfect.

## B0 — 10K–100K nodes (n_nets = 26)

### Wall time (s)

| config | mean | std | min | max | n_nets |
|---|---:|---:|---:|---:|---:|
| cptg | 286.0 | 672.5 | 16.6 | 3.3e+03 | 26 |
| stack | 286.5 | 678.5 | 16.6 | 3.3e+03 | 26 |
| rewire_stack | 172.4 | 343.1 | 17.0 | 1.5e+03 | 26 |

### Scalar SAD (bounded)

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| frac_giant_ccomp | SAD | 0.0000 ± 0.0000 (n=26) | 0.0010 ± 0.0044 (n=26) | 0.0063 ± 0.0305 (n=26) |
| deg_assort | SAD | 0.0476 ± 0.0753 (n=26) | 0.0476 ± 0.0754 (n=26) | 0.0485 ± 0.0762 (n=26) |
| global_ccoeff | SAD | 0.0530 ± 0.0763 (n=26) | 0.0531 ± 0.0762 (n=26) | 0.0532 ± 0.0769 (n=26) |
| local_ccoeff | SAD | 0.1272 ± 0.1201 (n=26) | 0.1272 ± 0.1205 (n=26) | 0.1282 ± 0.1207 (n=26) |
| node_coverage | SAD | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) |

### Scalar SRD (unbounded)

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| n_nodes | SRD | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) |
| n_edges | SRD | 0.0050 ± 0.0087 (n=26) | 0.0039 ± 0.0079 (n=26) | 0.0042 ± 0.0081 (n=26) |
| n_concomp | SRD | 0.0000 ± 0.0000 (n=26) | 0.0056 ± 0.0186 (n=26) | 0.0104 ± 0.0413 (n=26) |
| mean_degree | SRD | 0.0050 ± 0.0087 (n=26) | 0.0039 ± 0.0079 (n=26) | 0.0042 ± 0.0081 (n=26) |
| mean_kcore | SRD | 0.0283 ± 0.0489 (n=26) | 0.0280 ± 0.0488 (n=26) | 0.0283 ± 0.0491 (n=26) |
| n_clusters | SRD | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) |
| n_outliers | SRD | 0.0000 ± 0.0000 (n=21) | 0.0000 ± 0.0000 (n=21) | 0.0000 ± 0.0000 (n=21) |
| n_disconnected_clusters | SRD | — | — | — |
| pseudo_diameter | SRD | 0.3603 ± 0.6905 (n=26) | 0.3496 ± 0.6270 (n=26) | 0.3574 ± 0.6569 (n=26) |

### Distributional EMD

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| degree | EMD | 0.0519 ± 0.1095 (n=26) | 0.0442 ± 0.1072 (n=26) | 0.0555 ± 0.1148 (n=26) |
| kcore | EMD | 1.1521 ± 2.6570 (n=26) | 1.1528 ± 2.6569 (n=26) | 1.1279 ± 2.6362 (n=26) |
| conductance | EMD | 6.9459e-04 ± 9.1481e-04 (n=26) | 0.0034 ± 0.0054 (n=26) | 0.0036 ± 0.0056 (n=26) |
| edge_density | EMD | 0.0019 ± 0.0029 (n=26) | 0.0019 ± 0.0029 (n=26) | 0.0019 ± 0.0029 (n=26) |
| degree_density | EMD | 0.0058 ± 0.0088 (n=26) | 0.0058 ± 0.0088 (n=26) | 0.0062 ± 0.0094 (n=26) |
| mincut | EMD | 0.0019 ± 0.0041 (n=26) | 0.0019 ± 0.0041 (n=26) | 0.0019 ± 0.0041 (n=26) |
| modularity | EMD | 4.6820e-06 ± 8.1680e-06 (n=26) | 4.8011e-06 ± 9.4401e-06 (n=26) | 5.1912e-06 ± 1.0034e-05 (n=26) |
| mixing_parameter | EMD | 0.0096 ± 0.0121 (n=26) | 0.0100 ± 0.0121 (n=26) | 0.0101 ± 0.0121 (n=26) |
| concomp_sizes | EMD | 0.0000 ± 0.0000 (n=26) | 1.5499 ± 6.9772 (n=26) | 2.0171 ± 7.5025 (n=26) |
| local_ccoeff_nodes | EMD | 0.1293 ± 0.1193 (n=26) | 0.1294 ± 0.1196 (n=26) | 0.1304 ± 0.1197 (n=26) |
| pagerank | EMD | 2.7442e-06 ± 2.3630e-06 (n=26) | 2.7526e-06 ± 2.3646e-06 (n=26) | 2.7576e-06 ± 2.3696e-06 (n=26) |

### cluster_* sequence (rmse / mean_l1)

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| cluster_deg_assort | rmse | 0.0998 ± 0.0692 (n=26) | 0.0998 ± 0.0692 (n=26) | 0.1008 ± 0.0689 (n=26) |
| cluster_global_ccoeff | rmse | 0.0681 ± 0.0540 (n=26) | 0.0681 ± 0.0540 (n=26) | 0.0684 ± 0.0545 (n=26) |
| cluster_local_ccoeff | rmse | 0.0913 ± 0.0767 (n=26) | 0.0913 ± 0.0767 (n=26) | 0.0917 ± 0.0768 (n=26) |
| cluster_mean_degree | rmse | 0.0549 ± 0.0523 (n=26) | 0.0549 ± 0.0523 (n=26) | 0.0563 ± 0.0546 (n=26) |
| cluster_mean_kcore | rmse | 0.1543 ± 0.1760 (n=26) | 0.1543 ± 0.1760 (n=26) | 0.1615 ± 0.1982 (n=26) |
| cluster_n_concomp | mean_l1 | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) |
| cluster_frac_giant_ccomp | rmse | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) |
| cluster_pseudo_diameter | mean_l1 | 1.2760 ± 3.6801 (n=26) | 1.2760 ± 3.6801 (n=26) | 1.2722 ± 3.6821 (n=26) |

### cluster_* distribution EMD

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| cluster_deg_assort | EMD | 0.0331 ± 0.0510 (n=26) | 0.0331 ± 0.0510 (n=26) | 0.0336 ± 0.0511 (n=26) |
| cluster_global_ccoeff | EMD | 0.0274 ± 0.0373 (n=26) | 0.0274 ± 0.0373 (n=26) | 0.0275 ± 0.0378 (n=26) |
| cluster_local_ccoeff | EMD | 0.0414 ± 0.0715 (n=26) | 0.0414 ± 0.0715 (n=26) | 0.0417 ± 0.0717 (n=26) |
| cluster_mean_degree | EMD | 0.0116 ± 0.0177 (n=26) | 0.0116 ± 0.0177 (n=26) | 0.0123 ± 0.0188 (n=26) |
| cluster_mean_kcore | EMD | 0.0693 ± 0.1406 (n=26) | 0.0693 ± 0.1406 (n=26) | 0.0740 ± 0.1557 (n=26) |
| cluster_n_concomp | EMD | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) |
| cluster_frac_giant_ccomp | EMD | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) | 0.0000 ± 0.0000 (n=26) |
| cluster_pseudo_diameter | EMD | 1.2558 ± 3.6840 (n=26) | 1.2558 ± 3.6840 (n=26) | 1.2520 ± 3.6860 (n=26) |

### Paired Wilcoxon over networks

Three pairwise tests per metric. Winner = config with lower mean
distance. `*` = p < 0.05, `**` = p < 0.01.

| stat | metric | cptg vs stack | cptg vs rewire_stack | stack vs rewire_stack |
|---|---|---|---|---|
| frac_giant_ccomp | SAD | cptg * (p=0.0431, n=26) | cptg * (p=0.0431, n=26) | stack (p=0.0679, n=26) |
| deg_assort | SAD | stack (p=0.664, n=26) | cptg (p=0.532, n=26) | stack (p=0.408, n=26) |
| global_ccoeff | SAD | cptg (p=0.23, n=26) | cptg (p=0.111, n=26) | stack (p=0.303, n=26) |
| local_ccoeff | SAD | cptg (p=0.709, n=26) | cptg (p=0.116, n=26) | stack * (p=0.0254, n=26) |
| node_coverage | SAD | tie (p=—, n=26) | tie (p=—, n=26) | tie (p=—, n=26) |
| n_nodes | SRD | tie (p=—, n=26) | tie (p=—, n=26) | tie (p=—, n=26) |
| n_edges | SRD | stack ** (p=5.96e-05, n=26) | rewire_stack * (p=0.0186, n=26) | stack ** (p=0.00985, n=26) |
| n_concomp | SRD | cptg * (p=0.0431, n=26) | cptg * (p=0.0431, n=26) | stack (p=0.0679, n=26) |
| mean_degree | SRD | stack ** (p=5.96e-05, n=26) | rewire_stack * (p=0.0186, n=26) | stack ** (p=0.00985, n=26) |
| mean_kcore | SRD | stack (p=0.106, n=26) | cptg (p=0.901, n=26) | stack (p=0.565, n=26) |
| n_clusters | SRD | tie (p=—, n=26) | tie (p=—, n=26) | tie (p=—, n=26) |
| n_outliers | SRD | tie (p=—, n=21) | tie (p=—, n=21) | tie (p=—, n=21) |
| n_disconnected_clusters | SRD | — | — | — |
| pseudo_diameter | SRD | stack (p=0.893, n=26) | rewire_stack (p=1, n=26) | stack (p=0.465, n=26) |
| degree | EMD | stack ** (p=5.96e-05, n=26) | cptg (p=0.0653, n=26) | stack * (p=0.0459, n=26) |
| kcore | EMD | cptg * (p=0.0457, n=26) | rewire_stack * (p=0.0463, n=26) | rewire_stack ** (p=0.00561, n=26) |
| conductance | EMD | cptg ** (p=5.96e-05, n=26) | cptg ** (p=2.67e-05, n=26) | stack ** (p=0.000748, n=26) |
| edge_density | EMD | tie (p=—, n=26) | cptg ** (p=0.000493, n=26) | stack ** (p=0.000493, n=26) |
| degree_density | EMD | tie (p=—, n=26) | cptg ** (p=2.26e-05, n=26) | stack ** (p=2.26e-05, n=26) |
| mincut | EMD | tie (p=—, n=26) | cptg (p=0.18, n=26) | stack (p=0.18, n=26) |
| modularity | EMD | cptg * (p=0.0386, n=26) | cptg (p=0.932, n=26) | stack ** (p=0.00427, n=26) |
| mixing_parameter | EMD | cptg ** (p=9.22e-05, n=26) | cptg ** (p=7.14e-05, n=26) | stack * (p=0.0152, n=26) |
| concomp_sizes | EMD | cptg * (p=0.0431, n=26) | cptg * (p=0.0431, n=26) | stack (p=0.0679, n=26) |
| local_ccoeff_nodes | EMD | cptg (p=0.502, n=26) | cptg * (p=0.0407, n=26) | stack ** (p=0.00469, n=26) |
| pagerank | EMD | cptg (p=0.768, n=26) | cptg (p=0.217, n=26) | stack (p=0.165, n=26) |
| cluster_deg_assort | rmse | tie (p=—, n=26) | cptg (p=0.0669, n=26) | stack (p=0.0669, n=26) |
| cluster_global_ccoeff | rmse | tie (p=—, n=26) | cptg (p=0.157, n=26) | stack (p=0.157, n=26) |
| cluster_local_ccoeff | rmse | tie (p=—, n=26) | cptg (p=0.157, n=26) | stack (p=0.157, n=26) |
| cluster_mean_degree | rmse | tie (p=—, n=26) | cptg ** (p=0.000113, n=26) | stack ** (p=0.000113, n=26) |
| cluster_mean_kcore | rmse | tie (p=—, n=26) | cptg ** (p=0.00631, n=26) | stack ** (p=0.00631, n=26) |
| cluster_n_concomp | mean_l1 | tie (p=—, n=26) | tie (p=—, n=26) | tie (p=—, n=26) |
| cluster_frac_giant_ccomp | rmse | tie (p=—, n=26) | tie (p=—, n=26) | tie (p=—, n=26) |
| cluster_pseudo_diameter | mean_l1 | tie (p=—, n=26) | rewire_stack (p=0.496, n=26) | rewire_stack (p=0.496, n=26) |
| cluster_deg_assort | EMD-clu | tie (p=—, n=26) | cptg (p=0.468, n=26) | stack (p=0.468, n=26) |
| cluster_global_ccoeff | EMD-clu | tie (p=—, n=26) | cptg (p=0.157, n=26) | stack (p=0.157, n=26) |
| cluster_local_ccoeff | EMD-clu | tie (p=—, n=26) | cptg (p=0.0993, n=26) | stack (p=0.0993, n=26) |
| cluster_mean_degree | EMD-clu | tie (p=—, n=26) | cptg ** (p=2.26e-05, n=26) | stack ** (p=2.26e-05, n=26) |
| cluster_mean_kcore | EMD-clu | tie (p=—, n=26) | cptg ** (p=0.00322, n=26) | stack ** (p=0.00322, n=26) |
| cluster_n_concomp | EMD-clu | tie (p=—, n=26) | tie (p=—, n=26) | tie (p=—, n=26) |
| cluster_frac_giant_ccomp | EMD-clu | tie (p=—, n=26) | tie (p=—, n=26) | tie (p=—, n=26) |
| cluster_pseudo_diameter | EMD-clu | tie (p=—, n=26) | rewire_stack (p=0.379, n=26) | rewire_stack (p=0.379, n=26) |

## B1 — 100K–200K nodes (n_nets = 7)

### Wall time (s)

| config | mean | std | min | max | n_nets |
|---|---:|---:|---:|---:|---:|
| cptg | 667.5 | 488.2 | 128.4 | 1.3e+03 | 7 |
| stack | 667.7 | 476.8 | 138.8 | 1.3e+03 | 7 |
| rewire_stack | 536.2 | 349.3 | 137.4 | 1.1e+03 | 7 |

### Scalar SAD (bounded)

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| frac_giant_ccomp | SAD | 0.0000 ± 0.0000 (n=7) | 9.5853e-05 ± 1.6134e-04 (n=7) | 1.1402e-04 ± 1.8963e-04 (n=7) |
| deg_assort | SAD | 0.0285 ± 0.0313 (n=7) | 0.0277 ± 0.0319 (n=7) | 0.0279 ± 0.0339 (n=7) |
| global_ccoeff | SAD | 0.0281 ± 0.0351 (n=7) | 0.0281 ± 0.0350 (n=7) | 0.0282 ± 0.0354 (n=7) |
| local_ccoeff | SAD | 0.2000 ± 0.1740 (n=7) | 0.2000 ± 0.1741 (n=7) | 0.2014 ± 0.1744 (n=7) |
| node_coverage | SAD | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) |

### Scalar SRD (unbounded)

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| n_nodes | SRD | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) |
| n_edges | SRD | 0.0019 ± 0.0034 (n=7) | 0.0012 ± 0.0031 (n=7) | 0.0014 ± 0.0032 (n=7) |
| n_concomp | SRD | 0.0000 ± 0.0000 (n=7) | 0.0071 ± 0.0117 (n=7) | 0.0079 ± 0.0132 (n=7) |
| mean_degree | SRD | 0.0019 ± 0.0034 (n=7) | 0.0012 ± 0.0031 (n=7) | 0.0014 ± 0.0032 (n=7) |
| mean_kcore | SRD | 0.0309 ± 0.0412 (n=7) | 0.0304 ± 0.0410 (n=7) | 0.0309 ± 0.0413 (n=7) |
| n_clusters | SRD | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) |
| n_outliers | SRD | 0.0000 ± 0.0000 (n=6) | 0.0000 ± 0.0000 (n=6) | 0.0000 ± 0.0000 (n=6) |
| n_disconnected_clusters | SRD | — | — | — |
| pseudo_diameter | SRD | 0.1071 ± 0.0894 (n=7) | 0.1116 ± 0.1010 (n=7) | 0.1206 ± 0.1118 (n=7) |

### Distributional EMD

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| degree | EMD | 0.0274 ± 0.0558 (n=7) | 0.0194 ± 0.0510 (n=7) | 0.0245 ± 0.0517 (n=7) |
| kcore | EMD | 0.5888 ± 0.4396 (n=7) | 0.5884 ± 0.4407 (n=7) | 0.5877 ± 0.4397 (n=7) |
| conductance | EMD | 0.0011 ± 0.0011 (n=7) | 0.0035 ± 0.0036 (n=7) | 0.0036 ± 0.0036 (n=7) |
| edge_density | EMD | 0.0022 ± 0.0022 (n=7) | 0.0022 ± 0.0022 (n=7) | 0.0023 ± 0.0022 (n=7) |
| degree_density | EMD | 0.0065 ± 0.0066 (n=7) | 0.0065 ± 0.0066 (n=7) | 0.0067 ± 0.0067 (n=7) |
| mincut | EMD | 0.0015 ± 0.0024 (n=7) | 0.0015 ± 0.0024 (n=7) | 0.0015 ± 0.0024 (n=7) |
| modularity | EMD | 1.0781e-06 ± 1.2887e-06 (n=7) | 9.2212e-07 ± 1.2120e-06 (n=7) | 1.0528e-06 ± 1.2454e-06 (n=7) |
| mixing_parameter | EMD | 0.0197 ± 0.0153 (n=7) | 0.0197 ± 0.0154 (n=7) | 0.0197 ± 0.0154 (n=7) |
| concomp_sizes | EMD | 0.0000 ± 0.0000 (n=7) | 3.9459 ± 6.3884 (n=7) | 4.4066 ± 7.1862 (n=7) |
| local_ccoeff_nodes | EMD | 0.2000 ± 0.1740 (n=7) | 0.2000 ± 0.1741 (n=7) | 0.2014 ± 0.1744 (n=7) |
| pagerank | EMD | 3.7798e-07 ± 1.3663e-07 (n=7) | 3.7805e-07 ± 1.3647e-07 (n=7) | 3.8114e-07 ± 1.3685e-07 (n=7) |

### cluster_* sequence (rmse / mean_l1)

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| cluster_deg_assort | rmse | 0.0978 ± 0.0160 (n=7) | 0.0978 ± 0.0160 (n=7) | 0.0978 ± 0.0162 (n=7) |
| cluster_global_ccoeff | rmse | 0.0633 ± 0.0462 (n=7) | 0.0633 ± 0.0462 (n=7) | 0.0636 ± 0.0464 (n=7) |
| cluster_local_ccoeff | rmse | 0.0795 ± 0.0739 (n=7) | 0.0795 ± 0.0739 (n=7) | 0.0798 ± 0.0744 (n=7) |
| cluster_mean_degree | rmse | 0.0664 ± 0.0476 (n=7) | 0.0664 ± 0.0476 (n=7) | 0.0669 ± 0.0478 (n=7) |
| cluster_mean_kcore | rmse | 0.1224 ± 0.1209 (n=7) | 0.1224 ± 0.1209 (n=7) | 0.1228 ± 0.1212 (n=7) |
| cluster_n_concomp | mean_l1 | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) |
| cluster_frac_giant_ccomp | rmse | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) |
| cluster_pseudo_diameter | mean_l1 | 0.9885 ± 1.3124 (n=7) | 0.9885 ± 1.3124 (n=7) | 0.9888 ± 1.3130 (n=7) |

### cluster_* distribution EMD

| stat | metric | cptg | stack | rewire_stack |
|---|---|:---:|:---:|:---:|
| cluster_deg_assort | EMD | 0.0179 ± 0.0059 (n=7) | 0.0179 ± 0.0059 (n=7) | 0.0179 ± 0.0060 (n=7) |
| cluster_global_ccoeff | EMD | 0.0162 ± 0.0204 (n=7) | 0.0162 ± 0.0204 (n=7) | 0.0163 ± 0.0206 (n=7) |
| cluster_local_ccoeff | EMD | 0.0227 ± 0.0352 (n=7) | 0.0227 ± 0.0352 (n=7) | 0.0229 ± 0.0355 (n=7) |
| cluster_mean_degree | EMD | 0.0130 ± 0.0132 (n=7) | 0.0130 ± 0.0132 (n=7) | 0.0134 ± 0.0135 (n=7) |
| cluster_mean_kcore | EMD | 0.0418 ± 0.0598 (n=7) | 0.0418 ± 0.0598 (n=7) | 0.0420 ± 0.0600 (n=7) |
| cluster_n_concomp | EMD | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) |
| cluster_frac_giant_ccomp | EMD | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) |
| cluster_pseudo_diameter | EMD | 0.9699 ± 1.3151 (n=7) | 0.9699 ± 1.3151 (n=7) | 0.9699 ± 1.3156 (n=7) |

### Paired Wilcoxon over networks

Three pairwise tests per metric. Winner = config with lower mean
distance. `*` = p < 0.05, `**` = p < 0.01.

| stat | metric | cptg vs stack | cptg vs rewire_stack | stack vs rewire_stack |
|---|---|---|---|---|
| frac_giant_ccomp | SAD | cptg (p=0.125, n=7) | cptg (p=0.125, n=7) | stack (p=0.5, n=7) |
| deg_assort | SAD | stack (p=0.688, n=7) | rewire_stack (p=0.812, n=7) | stack (p=1, n=7) |
| global_ccoeff | SAD | cptg (p=0.375, n=7) | cptg (p=0.297, n=7) | stack (p=0.297, n=7) |
| local_ccoeff | SAD | stack (p=1, n=7) | cptg * (p=0.0156, n=7) | stack * (p=0.0156, n=7) |
| node_coverage | SAD | tie (p=—, n=7) | tie (p=—, n=7) | tie (p=—, n=7) |
| n_nodes | SRD | tie (p=—, n=7) | tie (p=—, n=7) | tie (p=—, n=7) |
| n_edges | SRD | stack * (p=0.0156, n=7) | rewire_stack (p=0.0781, n=7) | stack (p=0.125, n=7) |
| n_concomp | SRD | cptg (p=0.125, n=7) | cptg (p=0.125, n=7) | stack (p=0.5, n=7) |
| mean_degree | SRD | stack * (p=0.0156, n=7) | rewire_stack (p=0.0781, n=7) | stack (p=0.125, n=7) |
| mean_kcore | SRD | stack (p=0.156, n=7) | rewire_stack (p=0.938, n=7) | stack (p=0.578, n=7) |
| n_clusters | SRD | tie (p=—, n=7) | tie (p=—, n=7) | tie (p=—, n=7) |
| n_outliers | SRD | tie (p=—, n=6) | tie (p=—, n=6) | tie (p=—, n=6) |
| n_disconnected_clusters | SRD | — | — | — |
| pseudo_diameter | SRD | cptg (p=0.75, n=7) | cptg (p=0.5, n=7) | stack (p=0.375, n=7) |
| degree | EMD | stack * (p=0.0156, n=7) | rewire_stack (p=0.297, n=7) | stack (p=0.188, n=7) |
| kcore | EMD | stack (p=0.938, n=7) | rewire_stack (p=0.578, n=7) | rewire_stack (p=0.938, n=7) |
| conductance | EMD | cptg * (p=0.0156, n=7) | cptg * (p=0.0156, n=7) | stack * (p=0.0312, n=7) |
| edge_density | EMD | tie (p=—, n=7) | cptg * (p=0.0312, n=7) | stack * (p=0.0312, n=7) |
| degree_density | EMD | tie (p=—, n=7) | cptg * (p=0.0312, n=7) | stack * (p=0.0312, n=7) |
| mincut | EMD | tie (p=—, n=7) | rewire_stack (p=0.5, n=7) | rewire_stack (p=0.5, n=7) |
| modularity | EMD | stack * (p=0.0156, n=7) | rewire_stack (p=0.375, n=7) | stack (p=0.0625, n=7) |
| mixing_parameter | EMD | cptg (p=0.938, n=7) | cptg (p=0.938, n=7) | stack (p=0.938, n=7) |
| concomp_sizes | EMD | cptg (p=0.125, n=7) | cptg (p=0.125, n=7) | stack (p=0.5, n=7) |
| local_ccoeff_nodes | EMD | stack (p=1, n=7) | cptg * (p=0.0156, n=7) | stack * (p=0.0156, n=7) |
| pagerank | EMD | cptg (p=0.469, n=7) | cptg (p=0.297, n=7) | stack (p=0.156, n=7) |
| cluster_deg_assort | rmse | tie (p=—, n=7) | cptg (p=0.578, n=7) | stack (p=0.578, n=7) |
| cluster_global_ccoeff | rmse | tie (p=—, n=7) | cptg * (p=0.0156, n=7) | stack * (p=0.0156, n=7) |
| cluster_local_ccoeff | rmse | tie (p=—, n=7) | cptg * (p=0.0469, n=7) | stack * (p=0.0469, n=7) |
| cluster_mean_degree | rmse | tie (p=—, n=7) | cptg * (p=0.0312, n=7) | stack * (p=0.0312, n=7) |
| cluster_mean_kcore | rmse | tie (p=—, n=7) | cptg (p=0.109, n=7) | stack (p=0.109, n=7) |
| cluster_n_concomp | mean_l1 | tie (p=—, n=7) | tie (p=—, n=7) | tie (p=—, n=7) |
| cluster_frac_giant_ccomp | rmse | tie (p=—, n=7) | tie (p=—, n=7) | tie (p=—, n=7) |
| cluster_pseudo_diameter | mean_l1 | tie (p=—, n=7) | cptg (p=0.844, n=7) | stack (p=0.844, n=7) |
| cluster_deg_assort | EMD-clu | tie (p=—, n=7) | cptg (p=0.938, n=7) | stack (p=0.938, n=7) |
| cluster_global_ccoeff | EMD-clu | tie (p=—, n=7) | cptg * (p=0.0156, n=7) | stack * (p=0.0156, n=7) |
| cluster_local_ccoeff | EMD-clu | tie (p=—, n=7) | cptg * (p=0.0156, n=7) | stack * (p=0.0156, n=7) |
| cluster_mean_degree | EMD-clu | tie (p=—, n=7) | cptg * (p=0.0312, n=7) | stack * (p=0.0312, n=7) |
| cluster_mean_kcore | EMD-clu | tie (p=—, n=7) | cptg (p=0.109, n=7) | stack (p=0.109, n=7) |
| cluster_n_concomp | EMD-clu | tie (p=—, n=7) | tie (p=—, n=7) | tie (p=—, n=7) |
| cluster_frac_giant_ccomp | EMD-clu | tie (p=—, n=7) | tie (p=—, n=7) | tie (p=—, n=7) |
| cluster_pseudo_diameter | EMD-clu | tie (p=—, n=7) | cptg (p=1, n=7) | stack (p=1, n=7) |
