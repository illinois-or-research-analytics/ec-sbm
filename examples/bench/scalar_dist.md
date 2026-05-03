# Bucket 100,000-200,000 nodes — ec-sbm v1/v2 vs empirical

**Networks:** wiki_link_dyn (n=100,304, m=824,968), livemocha (n=104,103, m=2,193,083), wikiconflict (n=116,836, m=2,027,871), lastfm_aminer (n=136,409, m=1,685,524), wiki_users (n=138,587, m=715,883), wordnet (n=146,005, m=656,999), douban (n=154,908, m=327,162)

Two-stage aggregation: stage 1 averages 5 seeds per network;
stage 2 averages networks within each (gen, clustering) cell.
Reported mean/std are over networks, not over seeds.

`SAD` = |synth − ref| (bounded scalars). `SRD` = |synth − ref| / |synth| (unbounded scalars).
`emd` = Earth Mover's distance over synth/ref histograms; 0 = perfect match.

## Wall time (s)

| gen | clustering | mean | std | min | max | n_nets |
|---|---|---:|---:|---:|---:|---:|
| ec-sbm-v1 | leiden-cpm-0.0001 | 217.6 | 144.9 | 57.6 | 454.0 | 7 |
| ec-sbm-v2 | leiden-cpm-0.0001 | 427.1 | 280.9 | 135.4 | 929.0 | 7 |
| ec-sbm-v1 | leiden-cpm-0.0001+cm(piecewise) | 36.7 | 20.5 | 22.2 | 51.2 | 2 |
| ec-sbm-v2 | leiden-cpm-0.0001+cm(piecewise) | 95.7 | 57.3 | 55.2 | 136.2 | 2 |

## Scalar stats — SAD (bounded)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|---|:---:|:---:|:---:|:---:|
| frac_giant_ccomp | SAD | 1.2651e-04 ± 2.1544e-04 (n=7) | 0.0000 ± 0.0000 (n=7) | 2.6506e-04 ± 3.7485e-04 (n=2) | 0.0013 ± 4.5993e-04 (n=2) |
| deg_assort | SAD | 0.0319 ± 0.0344 (n=7) | 0.0285 ± 0.0313 (n=7) | 0.0150 ± 0.0037 (n=2) | 0.0512 ± 0.0399 (n=2) |
| global_ccoeff | SAD | 0.0296 ± 0.0360 (n=7) | 0.0281 ± 0.0351 (n=7) | 0.0400 ± 0.0518 (n=2) | 0.0382 ± 0.0513 (n=2) |
| local_ccoeff | SAD | 0.2011 ± 0.1770 (n=7) | 0.2000 ± 0.1740 (n=7) | 0.2547 ± 0.3457 (n=2) | 0.2634 ± 0.3569 (n=2) |
| node_coverage | SAD | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) | 0.0000 ± 0.0000 (n=2) |

## Scalar stats — SRD (unbounded)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|---|:---:|:---:|:---:|:---:|
| n_nodes | SRD | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) | 0.0000 ± 0.0000 (n=2) |
| n_edges | SRD | 1.0459e-04 ± 2.5249e-04 (n=7) | 0.0019 ± 0.0034 (n=7) | 9.6247e-04 ± 0.0013 (n=2) | 7.8820e-04 ± 6.5290e-04 (n=2) |
| n_concomp | SRD | 0.0089 ± 0.0149 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0174 ± 0.0246 (n=2) | 0.6299 ± 0.5041 (n=2) |
| mean_degree | SRD | 1.0459e-04 ± 2.5249e-04 (n=7) | 0.0019 ± 0.0034 (n=7) | 9.6247e-04 ± 0.0013 (n=2) | 7.8820e-04 ± 6.5290e-04 (n=2) |
| mean_kcore | SRD | 0.0303 ± 0.0420 (n=7) | 0.0309 ± 0.0412 (n=7) | 0.0562 ± 0.0713 (n=2) | 0.0636 ± 0.0739 (n=2) |
| n_clusters | SRD | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) | 0.0000 ± 0.0000 (n=2) |
| n_outliers | SRD | 0.0000 ± 0.0000 (n=6) | 0.0000 ± 0.0000 (n=6) | 0.0000 ± 0.0000 (n=2) | 0.0000 ± 0.0000 (n=2) |
| n_disconnected_clusters | SRD | — | — | — | — |
| pseudo_diameter | SRD | 0.1425 ± 0.1128 (n=7) | 0.1071 ± 0.0894 (n=7) | 0.0986 ± 0.0020 (n=2) | 0.0864 ± 0.0656 (n=2) |

## Distributional stats — EMD

| stat | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|:---:|:---:|:---:|:---:|
| degree | 0.0017 ± 0.0042 (n=7) | 0.0274 ± 0.0558 (n=7) | 0.0086 ± 0.0120 (n=2) | 0.0092 ± 0.0056 (n=2) |
| kcore | 0.6054 ± 0.4533 (n=7) | 0.5888 ± 0.4396 (n=7) | 0.2887 ± 0.3267 (n=2) | 0.3331 ± 0.3055 (n=2) |
| conductance | 0.0060 ± 0.0061 (n=7) | 0.0011 ± 0.0011 (n=7) | 0.0052 ± 0.0039 (n=2) | 8.2223e-04 ± 3.0565e-04 (n=2) |
| edge_density | 0.0030 ± 0.0032 (n=7) | 0.0022 ± 0.0022 (n=7) | 0.0022 ± 0.0029 (n=2) | 0.0017 ± 0.0023 (n=2) |
| degree_density | 0.0133 ± 0.0134 (n=7) | 0.0065 ± 0.0066 (n=7) | 0.0105 ± 0.0026 (n=2) | 0.0052 ± 0.0029 (n=2) |
| mincut | 0.0012 ± 0.0020 (n=7) | 0.0015 ± 0.0024 (n=7) | 0.0017 ± 0.0024 (n=2) | 0.0027 ± 0.0039 (n=2) |
| modularity | 4.7030e-06 ± 4.6366e-06 (n=7) | 1.0781e-06 ± 1.2887e-06 (n=7) | 2.4350e-06 ± 1.7119e-06 (n=2) | 7.2382e-07 ± 3.4301e-07 (n=2) |
| mixing_parameter | 0.0190 ± 0.0178 (n=7) | 0.0197 ± 0.0153 (n=7) | 0.0319 ± 0.0282 (n=2) | 0.0349 ± 0.0285 (n=2) |
| concomp_sizes | 4.9208 ± 8.0984 (n=7) | 0.0000 ± 0.0000 (n=7) | 8.8579 ± 12.5269 (n=2) | 7.6466e+04 ± 1.0795e+05 (n=2) |
| local_ccoeff_nodes | 0.2011 ± 0.1770 (n=7) | 0.2000 ± 0.1740 (n=7) | 0.2547 ± 0.3457 (n=2) | 0.2634 ± 0.3569 (n=2) |
| pagerank | 3.2813e-07 ± 1.5335e-07 (n=7) | 3.7798e-07 ± 1.3663e-07 (n=7) | 2.0666e-07 ± 1.0721e-07 (n=2) | 2.0824e-07 ± 9.1444e-08 (n=2) |

## Per-network mean (averaged over seeds)

### wiki_link_dyn (n=100,304, m=824,968)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| frac_giant_ccomp | SAD | 0.0000 | 0.0000 |
| deg_assort | SAD | 0.0093 | 0.0091 |
| global_ccoeff | SAD | 0.0080 | 0.0082 |
| local_ccoeff | SAD | 0.1877 | 0.1864 |
| node_coverage | SAD | 0.0000 | 0.0000 |
| n_nodes | SRD | 0.0000 | 0.0000 |
| n_edges | SRD | 6.7589e-04 | 0.0094 |
| n_concomp | SRD | 0.0000 | 0.0000 |
| mean_degree | SRD | 6.7589e-04 | 0.0094 |
| mean_kcore | SRD | 0.0087 | 0.0143 |
| n_clusters | SRD | 0.0000 | 0.0000 |
| n_outliers | SRD | 0.0000 | 0.0000 |
| n_disconnected_clusters | SRD | — | — |
| pseudo_diameter | SRD | 0.0909 | 0.1127 |
| degree | EMD | 0.0113 | 0.1534 |
| kcore | EMD | 0.5966 | 0.5989 |
| conductance | EMD | 0.0046 | 0.0017 |
| edge_density | EMD | 0.0039 | 0.0033 |
| degree_density | EMD | 0.0109 | 0.0079 |
| mincut | EMD | 4.6826e-04 | 7.2841e-04 |
| modularity | EMD | 4.8622e-06 | 3.5331e-06 |
| mixing_parameter | EMD | 0.0132 | 0.0129 |
| concomp_sizes | EMD | 0.0000 | 0.0000 |
| local_ccoeff_nodes | EMD | 0.1877 | 0.1864 |
| pagerank | EMD | 3.3861e-07 | 3.8235e-07 |

### livemocha (n=104,103, m=2,193,083)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| frac_giant_ccomp | SAD | 0.0000 | 0.0000 |
| deg_assort | SAD | 0.0424 | 0.0157 |
| global_ccoeff | SAD | 0.0052 | 0.0034 |
| local_ccoeff | SAD | 0.0263 | 0.0292 |
| node_coverage | SAD | 0.0000 | 0.0000 |
| n_nodes | SRD | 0.0000 | 0.0000 |
| n_edges | SRD | 0.0000 | 2.9183e-06 |
| n_concomp | SRD | 0.0000 | 0.0000 |
| mean_degree | SRD | 0.0000 | 2.9183e-06 |
| mean_kcore | SRD | 0.0130 | 0.0115 |
| n_clusters | SRD | 0.0000 | 0.0000 |
| n_outliers | SRD | 0.0000 | 0.0000 |
| n_disconnected_clusters | SRD | — | — |
| pseudo_diameter | SRD | 0.0857 | 0.1143 |
| degree | EMD | 0.0000 | 1.2296e-04 |
| kcore | EMD | 0.6886 | 0.5671 |
| conductance | EMD | 1.7987e-04 | 1.2382e-04 |
| edge_density | EMD | 2.2444e-04 | 2.6549e-04 |
| degree_density | EMD | 5.3185e-04 | 5.3828e-04 |
| mincut | EMD | 0.0000 | 0.0000 |
| modularity | EMD | 3.8173e-09 | 3.2593e-09 |
| mixing_parameter | EMD | 0.0010 | 0.0048 |
| concomp_sizes | EMD | 0.0000 | 0.0000 |
| local_ccoeff_nodes | EMD | 0.0263 | 0.0292 |
| pagerank | EMD | 2.4649e-07 | 3.5561e-07 |

### wikiconflict (n=116,836, m=2,027,871)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| frac_giant_ccomp | SAD | 4.2795e-05 | 0.0000 |
| deg_assort | SAD | 0.0098 | 0.0134 |
| global_ccoeff | SAD | 0.0010 | 0.0036 |
| local_ccoeff | SAD | 0.2775 | 0.2828 |
| node_coverage | SAD | 0.0000 | 0.0000 |
| n_nodes | SRD | 0.0000 | 0.0000 |
| n_edges | SRD | 2.4656e-06 | 1.5664e-04 |
| n_concomp | SRD | 5.6148e-04 | 0.0000 |
| mean_degree | SRD | 2.4656e-06 | 1.5664e-04 |
| mean_kcore | SRD | 0.0427 | 0.0410 |
| n_clusters | SRD | 0.0000 | 0.0000 |
| n_outliers | SRD | 0.0000 | 0.0000 |
| n_disconnected_clusters | SRD | — | — |
| pseudo_diameter | SRD | 0.0000 | 0.0000 |
| degree | EMD | 8.5590e-05 | 0.0054 |
| kcore | EMD | 0.8578 | 0.8244 |
| conductance | EMD | 0.0019 | 6.3487e-04 |
| edge_density | EMD | 0.0016 | 0.0015 |
| degree_density | EMD | 0.0041 | 0.0028 |
| mincut | EMD | 1.4278e-04 | 1.4278e-04 |
| modularity | EMD | 5.1652e-07 | 5.1893e-08 |
| mixing_parameter | EMD | 0.0054 | 0.0068 |
| concomp_sizes | EMD | 0.0401 | 0.0000 |
| local_ccoeff_nodes | EMD | 0.2775 | 0.2828 |
| pagerank | EMD | 3.1725e-07 | 4.4536e-07 |

### lastfm_aminer (n=136,409, m=1,685,524)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| frac_giant_ccomp | SAD | 2.2726e-04 | 0.0000 |
| deg_assort | SAD | 0.0737 | 0.0650 |
| global_ccoeff | SAD | 0.0784 | 0.0771 |
| local_ccoeff | SAD | 0.1731 | 0.1705 |
| node_coverage | SAD | 0.0000 | 0.0000 |
| n_nodes | SRD | 0.0000 | 0.0000 |
| n_edges | SRD | 2.3731e-06 | 2.2099e-04 |
| n_concomp | SRD | 0.0198 | 0.0000 |
| mean_degree | SRD | 2.3731e-06 | 2.2099e-04 |
| mean_kcore | SRD | 0.0069 | 0.0075 |
| n_clusters | SRD | 0.0000 | 0.0000 |
| n_outliers | SRD | 0.0000 | 0.0000 |
| n_disconnected_clusters | SRD | — | — |
| pseudo_diameter | SRD | 0.2000 | 0.0582 |
| degree | EMD | 5.8647e-05 | 0.0055 |
| kcore | EMD | 1.3684 | 1.3655 |
| conductance | EMD | 0.0156 | 0.0032 |
| edge_density | EMD | 0.0089 | 0.0063 |
| degree_density | EMD | 0.0355 | 0.0191 |
| mincut | EMD | 0.0021 | 0.0032 |
| modularity | EMD | 3.0193e-06 | 2.1966e-07 |
| mixing_parameter | EMD | 0.0235 | 0.0256 |
| concomp_sizes | EMD | 13.3150 | 0.0000 |
| local_ccoeff_nodes | EMD | 0.1731 | 0.1705 |
| pagerank | EMD | 6.3892e-07 | 6.3109e-07 |

### wiki_users (n=138,587, m=715,883)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| frac_giant_ccomp | SAD | 3.6078e-05 | 0.0000 |
| deg_assort | SAD | 5.9465e-04 | 0.0051 |
| global_ccoeff | SAD | 0.0245 | 0.0184 |
| local_ccoeff | SAD | 0.1930 | 0.1915 |
| node_coverage | SAD | 0.0000 | 0.0000 |
| n_nodes | SRD | 0.0000 | 0.0000 |
| n_edges | SRD | 4.1906e-06 | 0.0013 |
| n_concomp | SRD | 0.0033 | 0.0000 |
| mean_degree | SRD | 4.1906e-06 | 0.0013 |
| mean_kcore | SRD | 0.0015 | 0.0024 |
| n_clusters | SRD | 0.0000 | 0.0000 |
| n_outliers | SRD | 0.0000 | 0.0000 |
| n_disconnected_clusters | SRD | — | — |
| pseudo_diameter | SRD | 0.2091 | 0.1879 |
| degree | EMD | 4.3294e-05 | 0.0130 |
| kcore | EMD | 0.0523 | 0.0971 |
| conductance | EMD | 0.0030 | 5.8944e-04 |
| edge_density | EMD | 0.0013 | 9.5727e-04 |
| degree_density | EMD | 0.0076 | 0.0032 |
| mincut | EMD | 0.0000 | 1.3241e-04 |
| modularity | EMD | 2.4975e-06 | 5.0006e-07 |
| mixing_parameter | EMD | 0.0182 | 0.0235 |
| concomp_sizes | EMD | 1.5093 | 0.0000 |
| local_ccoeff_nodes | EMD | 0.1930 | 0.1915 |
| pagerank | EMD | 1.8886e-07 | 2.7856e-07 |

### wordnet (n=146,005, m=656,999)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|---|:---:|:---:|:---:|:---:|
| frac_giant_ccomp | SAD | 5.7943e-04 | 0.0000 | 5.3012e-04 | 0.0016 |
| deg_assort | SAD | 0.0051 | 0.0094 | 0.0124 | 0.0230 |
| global_ccoeff | SAD | 0.0839 | 0.0806 | 0.0766 | 0.0745 |
| local_ccoeff | SAD | 0.5392 | 0.5295 | 0.4991 | 0.5158 |
| node_coverage | SAD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| n_nodes | SRD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| n_edges | SRD | 4.7182e-05 | 0.0013 | 0.0019 | 3.2653e-04 |
| n_concomp | SRD | 0.0384 | 0.0000 | 0.0348 | 0.2735 |
| mean_degree | SRD | 4.7182e-05 | 0.0013 | 0.0019 | 3.2653e-04 |
| mean_kcore | SRD | 0.1206 | 0.1200 | 0.1067 | 0.1158 |
| n_clusters | SRD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| n_outliers | SRD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| n_disconnected_clusters | SRD | — | — | — | — |
| pseudo_diameter | SRD | 0.3371 | 0.2513 | 0.0971 | 0.0400 |
| degree | EMD | 4.2464e-04 | 0.0117 | 0.0171 | 0.0132 |
| kcore | EMD | 0.5921 | 0.5884 | 0.5197 | 0.5492 |
| conductance | EMD | 0.0136 | 9.5739e-04 | 0.0080 | 0.0010 |
| edge_density | EMD | 0.0053 | 0.0034 | 0.0042 | 0.0033 |
| degree_density | EMD | 0.0288 | 0.0102 | 0.0123 | 0.0073 |
| mincut | EMD | 0.0054 | 0.0063 | 0.0035 | 0.0055 |
| modularity | EMD | 1.2030e-05 | 1.8083e-06 | 1.2245e-06 | 4.8128e-07 |
| mixing_parameter | EMD | 0.0555 | 0.0496 | 0.0518 | 0.0551 |
| concomp_sizes | EMD | 19.5814 | 0.0000 | 17.7157 | 136.7668 |
| local_ccoeff_nodes | EMD | 0.5392 | 0.5295 | 0.4991 | 0.5158 |
| pagerank | EMD | 3.6771e-07 | 3.5517e-07 | 2.8247e-07 | 2.7290e-07 |

### douban (n=154,908, m=327,162)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|---|:---:|:---:|:---:|:---:|
| frac_giant_ccomp | SAD | 0.0000 | 0.0000 | 0.0000 | 9.3991e-04 |
| deg_assort | SAD | 0.0824 | 0.0820 | 0.0176 | 0.0794 |
| global_ccoeff | SAD | 0.0059 | 0.0052 | 0.0034 | 0.0019 |
| local_ccoeff | SAD | 0.0109 | 0.0104 | 0.0102 | 0.0110 |
| node_coverage | SAD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| n_nodes | SRD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| n_edges | SRD | 0.0000 | 6.0741e-04 | 2.4452e-05 | 0.0012 |
| n_concomp | SRD | 0.0000 | 0.0000 | 0.0000 | 0.9864 |
| mean_degree | SRD | 0.0000 | 6.0741e-04 | 2.4452e-05 | 0.0012 |
| mean_kcore | SRD | 0.0189 | 0.0194 | 0.0058 | 0.0114 |
| n_clusters | SRD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| n_outliers | SRD | — | — | 0.0000 | 0.0000 |
| n_disconnected_clusters | SRD | — | — | — | — |
| pseudo_diameter | SRD | 0.0750 | 0.0250 | 0.1000 | 0.1327 |
| degree | EMD | 0.0000 | 0.0026 | 1.0329e-04 | 0.0053 |
| kcore | EMD | 0.0819 | 0.0803 | 0.0577 | 0.1171 |
| conductance | EMD | 0.0032 | 3.3554e-04 | 0.0025 | 6.0610e-04 |
| edge_density | EMD | 3.6781e-05 | 1.4616e-05 | 1.8546e-04 | 7.7862e-05 |
| degree_density | EMD | 0.0056 | 0.0016 | 0.0087 | 0.0031 |
| mincut | EMD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| modularity | EMD | 9.9911e-06 | 1.4302e-06 | 3.6456e-06 | 9.6636e-07 |
| mixing_parameter | EMD | 0.0159 | 0.0148 | 0.0120 | 0.0148 |
| concomp_sizes | EMD | 0.0000 | 0.0000 | 0.0000 | 1.5280e+05 |
| local_ccoeff_nodes | EMD | 0.0109 | 0.0104 | 0.0102 | 0.0110 |
| pagerank | EMD | 1.9909e-07 | 1.9775e-07 | 1.3085e-07 | 1.4358e-07 |

## v1 vs v2 — paired Wilcoxon over networks

Paired Wilcoxon signed-rank on per-net mean distances (n = number of
networks where both v1 and v2 ran). `winner` = gen with lower mean
distance. `p` = two-sided p-value; n=2 has no p-value (no scipy fallback).
Be careful with low n — bench has 7 nets on A, 2 on P, so P-clustering
results never reach conventional significance.

| clustering | stat | metric | v1 mean | v2 mean | winner | p | n |
|---|---|---|---:|---:|:---:|---:|---:|
| leiden-cpm-0.0001 | frac_giant_ccomp | SAD | 1.2651e-04 | 0.0000 | v2 | 0.125 | 7 |
| leiden-cpm-0.0001 | deg_assort | SAD | 0.0319 | 0.0285 | v2 | 0.8125 | 7 |
| leiden-cpm-0.0001 | global_ccoeff | SAD | 0.0296 | 0.0281 | v2 | 0.2188 | 7 |
| leiden-cpm-0.0001 | local_ccoeff | SAD | 0.2011 | 0.2000 | v2 | 0.6875 | 7 |
| leiden-cpm-0.0001 | node_coverage | SAD | 0.0000 | 0.0000 | tie | — | 7 |
| leiden-cpm-0.0001 | n_nodes | SRD | 0.0000 | 0.0000 | tie | — | 7 |
| leiden-cpm-0.0001 | n_edges | SRD | 1.0459e-04 | 0.0019 | v1 * | 0.01562 | 7 |
| leiden-cpm-0.0001 | n_concomp | SRD | 0.0089 | 0.0000 | v2 | 0.125 | 7 |
| leiden-cpm-0.0001 | mean_degree | SRD | 1.0459e-04 | 0.0019 | v1 * | 0.01562 | 7 |
| leiden-cpm-0.0001 | mean_kcore | SRD | 0.0303 | 0.0309 | v1 | 0.9375 | 7 |
| leiden-cpm-0.0001 | n_clusters | SRD | 0.0000 | 0.0000 | tie | — | 7 |
| leiden-cpm-0.0001 | n_outliers | SRD | 0.0000 | 0.0000 | tie | — | 6 |
| leiden-cpm-0.0001 | pseudo_diameter | SRD | 0.1425 | 0.1071 | v2 | 0.3125 | 7 |
| leiden-cpm-0.0001 | degree | EMD | 0.0017 | 0.0274 | v1 * | 0.01562 | 7 |
| leiden-cpm-0.0001 | kcore | EMD | 0.6054 | 0.5888 | v2 | 0.375 | 7 |
| leiden-cpm-0.0001 | conductance | EMD | 0.0060 | 0.0011 | v2 * | 0.01562 | 7 |
| leiden-cpm-0.0001 | edge_density | EMD | 0.0030 | 0.0022 | v2 * | 0.04688 | 7 |
| leiden-cpm-0.0001 | degree_density | EMD | 0.0133 | 0.0065 | v2 * | 0.03125 | 7 |
| leiden-cpm-0.0001 | mincut | EMD | 0.0012 | 0.0015 | v1 | 0.125 | 7 |
| leiden-cpm-0.0001 | modularity | EMD | 4.7030e-06 | 1.0781e-06 | v2 * | 0.01562 | 7 |
| leiden-cpm-0.0001 | mixing_parameter | EMD | 0.0190 | 0.0197 | v1 | 0.5781 | 7 |
| leiden-cpm-0.0001 | concomp_sizes | EMD | 4.9208 | 0.0000 | v2 | 0.125 | 7 |
| leiden-cpm-0.0001 | local_ccoeff_nodes | EMD | 0.2011 | 0.2000 | v2 | 0.6875 | 7 |
| leiden-cpm-0.0001 | pagerank | EMD | 3.2813e-07 | 3.7798e-07 | v1 | 0.2188 | 7 |
| leiden-cpm-0.0001+cm(piecewise) | frac_giant_ccomp | SAD | 2.6506e-04 | 0.0013 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | deg_assort | SAD | 0.0150 | 0.0512 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | global_ccoeff | SAD | 0.0400 | 0.0382 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | local_ccoeff | SAD | 0.2547 | 0.2634 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | node_coverage | SAD | 0.0000 | 0.0000 | tie | — | 2 |
| leiden-cpm-0.0001+cm(piecewise) | n_nodes | SRD | 0.0000 | 0.0000 | tie | — | 2 |
| leiden-cpm-0.0001+cm(piecewise) | n_edges | SRD | 9.6247e-04 | 7.8820e-04 | v2 | 1 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | n_concomp | SRD | 0.0174 | 0.6299 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | mean_degree | SRD | 9.6247e-04 | 7.8820e-04 | v2 | 1 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | mean_kcore | SRD | 0.0562 | 0.0636 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | n_clusters | SRD | 0.0000 | 0.0000 | tie | — | 2 |
| leiden-cpm-0.0001+cm(piecewise) | n_outliers | SRD | 0.0000 | 0.0000 | tie | — | 2 |
| leiden-cpm-0.0001+cm(piecewise) | pseudo_diameter | SRD | 0.0986 | 0.0864 | v2 | 1 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | degree | EMD | 0.0086 | 0.0092 | v1 | 1 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | kcore | EMD | 0.2887 | 0.3331 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | conductance | EMD | 0.0052 | 8.2223e-04 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | edge_density | EMD | 0.0022 | 0.0017 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | degree_density | EMD | 0.0105 | 0.0052 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | mincut | EMD | 0.0017 | 0.0027 | v1 | 1 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | modularity | EMD | 2.4350e-06 | 7.2382e-07 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | mixing_parameter | EMD | 0.0319 | 0.0349 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | concomp_sizes | EMD | 8.8579 | 7.6466e+04 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | local_ccoeff_nodes | EMD | 0.2547 | 0.2634 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | pagerank | EMD | 2.0666e-07 | 2.0824e-07 | v1 | 1 | 2 |

`*` = p < 0.05, `**` = p < 0.01.
