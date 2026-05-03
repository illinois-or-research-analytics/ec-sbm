# ec-sbm v1/v2 vs empirical: cluster_* metrics

Each `cluster_*` metric is a per-cluster vector. compare_pair.py emits
two flavours of distance:

* **sequence**: aligns cluster-by-cluster. We pick `mean_l1` for count-valued
  stats (`cluster_n_concomp`, `cluster_pseudo_diameter`) where the natural
  reading is the average integer gap per cluster, and `rmse` for
  continuous-valued stats where squared error highlights per-cluster outlier
  deviations on top of the mean gap.
* **distribution**: EMD over the histogram of per-cluster values, no ID alignment.

Two-stage aggregation: stage 1 averages 5 seeds per network; stage 2
reports mean ± std over networks. Sample sizes: A = 7 nets, P = 2 nets.

## Sequence (mean_l1 / rmse; 0 = perfect)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|---|:---:|:---:|:---:|:---:|
| cluster_deg_assort | rmse | 0.0986 ± 0.0168 (n=7) | 0.0856 ± 0.0081 (n=2) | 0.0978 ± 0.0160 (n=7) | 0.0854 ± 0.0083 (n=2) |
| cluster_global_ccoeff | rmse | 0.0682 ± 0.0511 (n=7) | 0.0622 ± 0.0699 (n=2) | 0.0633 ± 0.0462 (n=7) | 0.0614 ± 0.0637 (n=2) |
| cluster_local_ccoeff | rmse | 0.0839 ± 0.0779 (n=7) | 0.0852 ± 0.0870 (n=2) | 0.0795 ± 0.0739 (n=7) | 0.0819 ± 0.0842 (n=2) |
| cluster_mean_degree | rmse | 0.1093 ± 0.0856 (n=7) | 0.1102 ± 0.0791 (n=2) | 0.0664 ± 0.0476 (n=7) | 0.0704 ± 0.0734 (n=2) |
| cluster_mean_kcore | rmse | 0.1480 ± 0.1431 (n=7) | 0.1733 ± 0.1581 (n=2) | 0.1224 ± 0.1209 (n=7) | 0.1500 ± 0.1444 (n=2) |
| cluster_n_concomp | mean_l1 | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) |
| cluster_frac_giant_ccomp | rmse | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) |
| cluster_pseudo_diameter | mean_l1 | 0.9846 ± 1.3077 (n=7) | 0.5757 ± 0.5326 (n=2) | 0.9885 ± 1.3124 (n=7) | 0.5864 ± 0.5460 (n=2) |

## EMD distribution (0 = perfect)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|---|:---:|:---:|:---:|:---:|
| cluster_deg_assort | emd | 0.0183 ± 0.0062 (n=7) | 0.0142 ± 0.0058 (n=2) | 0.0179 ± 0.0059 (n=7) | 0.0132 ± 0.0070 (n=2) |
| cluster_global_ccoeff | emd | 0.0185 ± 0.0228 (n=7) | 0.0138 ± 0.0170 (n=2) | 0.0162 ± 0.0204 (n=7) | 0.0134 ± 0.0149 (n=2) |
| cluster_local_ccoeff | emd | 0.0252 ± 0.0377 (n=7) | 0.0196 ± 0.0234 (n=2) | 0.0227 ± 0.0352 (n=7) | 0.0181 ± 0.0221 (n=2) |
| cluster_mean_degree | emd | 0.0266 ± 0.0268 (n=7) | 0.0210 ± 0.0051 (n=2) | 0.0130 ± 0.0132 (n=7) | 0.0104 ± 0.0059 (n=2) |
| cluster_mean_kcore | emd | 0.0504 ± 0.0682 (n=7) | 0.0538 ± 0.0387 (n=2) | 0.0418 ± 0.0598 (n=7) | 0.0462 ± 0.0377 (n=2) |
| cluster_n_concomp | emd | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) |
| cluster_frac_giant_ccomp | emd | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) | 0.0000 ± 0.0000 (n=7) | 0.0000 ± 0.0000 (n=2) |
| cluster_pseudo_diameter | emd | 0.9634 ± 1.3101 (n=7) | 0.5523 ± 0.5254 (n=2) | 0.9699 ± 1.3151 (n=7) | 0.5648 ± 0.5372 (n=2) |

## v1 vs v2 — paired Wilcoxon over networks

Pairs are per-network mean values (one pair per network). `*` p < 0.05, `**` p < 0.01.

| clustering | stat | metric | v1 mean | v2 mean | winner | p | n |
|---|---|---|---:|---:|:---:|---:|---:|
| leiden-cpm-0.0001 | cluster_deg_assort | rmse | 0.0986 | 0.0978 | v2 | 0.1562 | 7 |
| leiden-cpm-0.0001 | cluster_deg_assort | EMD | 0.0183 | 0.0179 | v2 | 0.375 | 7 |
| leiden-cpm-0.0001 | cluster_global_ccoeff | rmse | 0.0682 | 0.0633 | v2 | 0.07812 | 7 |
| leiden-cpm-0.0001 | cluster_global_ccoeff | EMD | 0.0185 | 0.0162 | v2 * | 0.03125 | 7 |
| leiden-cpm-0.0001 | cluster_local_ccoeff | rmse | 0.0839 | 0.0795 | v2 | 0.07812 | 7 |
| leiden-cpm-0.0001 | cluster_local_ccoeff | EMD | 0.0252 | 0.0227 | v2 * | 0.03125 | 7 |
| leiden-cpm-0.0001 | cluster_mean_degree | rmse | 0.1093 | 0.0664 | v2 * | 0.01562 | 7 |
| leiden-cpm-0.0001 | cluster_mean_degree | EMD | 0.0266 | 0.0130 | v2 * | 0.03125 | 7 |
| leiden-cpm-0.0001 | cluster_mean_kcore | rmse | 0.1480 | 0.1224 | v2 * | 0.03125 | 7 |
| leiden-cpm-0.0001 | cluster_mean_kcore | EMD | 0.0504 | 0.0418 | v2 * | 0.03125 | 7 |
| leiden-cpm-0.0001 | cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 | tie | — | 7 |
| leiden-cpm-0.0001 | cluster_n_concomp | EMD | 0.0000 | 0.0000 | tie | — | 7 |
| leiden-cpm-0.0001 | cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 | tie | — | 7 |
| leiden-cpm-0.0001 | cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 | tie | — | 7 |
| leiden-cpm-0.0001 | cluster_pseudo_diameter | mean_l1 | 0.9846 | 0.9885 | v1 * | 0.04688 | 7 |
| leiden-cpm-0.0001 | cluster_pseudo_diameter | EMD | 0.9634 | 0.9699 | v1 * | 0.01562 | 7 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_deg_assort | rmse | 0.0856 | 0.0854 | v2 | 1 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_deg_assort | EMD | 0.0142 | 0.0132 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_global_ccoeff | rmse | 0.0622 | 0.0614 | v2 | 1 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_global_ccoeff | EMD | 0.0138 | 0.0134 | v2 | 1 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_local_ccoeff | rmse | 0.0852 | 0.0819 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_local_ccoeff | EMD | 0.0196 | 0.0181 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_mean_degree | rmse | 0.1102 | 0.0704 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_mean_degree | EMD | 0.0210 | 0.0104 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_mean_kcore | rmse | 0.1733 | 0.1500 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_mean_kcore | EMD | 0.0538 | 0.0462 | v2 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 | tie | — | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_n_concomp | EMD | 0.0000 | 0.0000 | tie | — | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 | tie | — | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 | tie | — | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_pseudo_diameter | mean_l1 | 0.5757 | 0.5864 | v1 | 0.5 | 2 |
| leiden-cpm-0.0001+cm(piecewise) | cluster_pseudo_diameter | EMD | 0.5523 | 0.5648 | v1 | 0.5 | 2 |

## Per-network mean (averaged over seeds)

### douban (n=154,908, m=327,162)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|---|:---:|:---:|:---:|:---:|
| cluster_deg_assort | rmse | 0.0882 | 0.0799 | 0.0895 | 0.0796 |
| cluster_deg_assort | EMD | 0.0161 | 0.0101 | 0.0183 | 0.0083 |
| cluster_global_ccoeff | rmse | 0.0079 | 0.0127 | 0.0067 | 0.0163 |
| cluster_global_ccoeff | EMD | 0.0019 | 0.0018 | 0.0012 | 0.0028 |
| cluster_local_ccoeff | rmse | 0.0117 | 0.0236 | 0.0109 | 0.0224 |
| cluster_local_ccoeff | EMD | 0.0031 | 0.0030 | 0.0026 | 0.0025 |
| cluster_mean_degree | rmse | 0.0206 | 0.0543 | 0.0058 | 0.0185 |
| cluster_mean_degree | EMD | 0.0113 | 0.0173 | 0.0032 | 0.0063 |
| cluster_mean_kcore | rmse | 0.0286 | 0.0615 | 0.0260 | 0.0479 |
| cluster_mean_kcore | EMD | 0.0191 | 0.0264 | 0.0156 | 0.0196 |
| cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cluster_n_concomp | EMD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cluster_pseudo_diameter | mean_l1 | 3.7549 | 0.9523 | 3.7695 | 0.9725 |
| cluster_pseudo_diameter | EMD | 3.7549 | 0.9238 | 3.7695 | 0.9446 |

### wordnet (n=146,005, m=656,999)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v1 / leiden-cpm-0.0001+cm(piecewise) | ec-sbm-v2 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001+cm(piecewise) |
|---|---|:---:|:---:|:---:|:---:|
| cluster_deg_assort | rmse | 0.1057 | 0.0913 | 0.1031 | 0.0913 |
| cluster_deg_assort | EMD | 0.0279 | 0.0184 | 0.0261 | 0.0181 |
| cluster_global_ccoeff | rmse | 0.1463 | 0.1116 | 0.1365 | 0.1064 |
| cluster_global_ccoeff | EMD | 0.0558 | 0.0258 | 0.0510 | 0.0239 |
| cluster_local_ccoeff | rmse | 0.2382 | 0.1467 | 0.2291 | 0.1414 |
| cluster_local_ccoeff | EMD | 0.1026 | 0.0362 | 0.0966 | 0.0337 |
| cluster_mean_degree | rmse | 0.2105 | 0.1661 | 0.1213 | 0.1223 |
| cluster_mean_degree | EMD | 0.0576 | 0.0246 | 0.0205 | 0.0146 |
| cluster_mean_kcore | rmse | 0.4209 | 0.2850 | 0.3670 | 0.2522 |
| cluster_mean_kcore | EMD | 0.1903 | 0.0812 | 0.1681 | 0.0729 |
| cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cluster_n_concomp | EMD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| cluster_pseudo_diameter | mean_l1 | 1.2566 | 0.1991 | 1.2636 | 0.2003 |
| cluster_pseudo_diameter | EMD | 1.2210 | 0.1808 | 1.2380 | 0.1850 |

### wiki_users (n=138,587, m=715,883)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| cluster_deg_assort | rmse | 0.1022 | 0.1016 |
| cluster_deg_assort | EMD | 0.0202 | 0.0195 |
| cluster_global_ccoeff | rmse | 0.0432 | 0.0401 |
| cluster_global_ccoeff | EMD | 0.0036 | 0.0020 |
| cluster_local_ccoeff | rmse | 0.0496 | 0.0473 |
| cluster_local_ccoeff | EMD | 0.0029 | 0.0020 |
| cluster_mean_degree | rmse | 0.0987 | 0.0500 |
| cluster_mean_degree | EMD | 0.0152 | 0.0065 |
| cluster_mean_kcore | rmse | 0.0915 | 0.0623 |
| cluster_mean_kcore | EMD | 0.0159 | 0.0100 |
| cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 |
| cluster_n_concomp | EMD | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 |
| cluster_pseudo_diameter | mean_l1 | 0.4420 | 0.4457 |
| cluster_pseudo_diameter | EMD | 0.4253 | 0.4303 |

### wiki_link_dyn (n=100,304, m=824,968)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| cluster_deg_assort | rmse | 0.1155 | 0.1144 |
| cluster_deg_assort | EMD | 0.0239 | 0.0232 |
| cluster_global_ccoeff | rmse | 0.0840 | 0.0782 |
| cluster_global_ccoeff | EMD | 0.0157 | 0.0138 |
| cluster_local_ccoeff | rmse | 0.0865 | 0.0802 |
| cluster_local_ccoeff | EMD | 0.0150 | 0.0128 |
| cluster_mean_degree | rmse | 0.1154 | 0.0880 |
| cluster_mean_degree | EMD | 0.0219 | 0.0157 |
| cluster_mean_kcore | rmse | 0.1263 | 0.1101 |
| cluster_mean_kcore | EMD | 0.0251 | 0.0207 |
| cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 |
| cluster_n_concomp | EMD | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 |
| cluster_pseudo_diameter | mean_l1 | 0.2599 | 0.2616 |
| cluster_pseudo_diameter | EMD | 0.2459 | 0.2482 |

### lastfm_aminer (n=136,409, m=1,685,524)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| cluster_deg_assort | rmse | 0.1181 | 0.1160 |
| cluster_deg_assort | EMD | 0.0146 | 0.0127 |
| cluster_global_ccoeff | rmse | 0.1196 | 0.1050 |
| cluster_global_ccoeff | EMD | 0.0461 | 0.0389 |
| cluster_local_ccoeff | rmse | 0.1232 | 0.1101 |
| cluster_local_ccoeff | EMD | 0.0467 | 0.0389 |
| cluster_mean_degree | rmse | 0.2351 | 0.1281 |
| cluster_mean_degree | EMD | 0.0709 | 0.0383 |
| cluster_mean_kcore | rmse | 0.2575 | 0.1869 |
| cluster_mean_kcore | EMD | 0.0902 | 0.0678 |
| cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 |
| cluster_n_concomp | EMD | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 |
| cluster_pseudo_diameter | mean_l1 | 1.0470 | 1.0455 |
| cluster_pseudo_diameter | EMD | 0.9788 | 0.9828 |

### wikiconflict (n=116,836, m=2,027,871)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| cluster_deg_assort | rmse | 0.0708 | 0.0704 |
| cluster_deg_assort | EMD | 0.0091 | 0.0090 |
| cluster_global_ccoeff | rmse | 0.0558 | 0.0542 |
| cluster_global_ccoeff | EMD | 0.0055 | 0.0051 |
| cluster_local_ccoeff | rmse | 0.0571 | 0.0555 |
| cluster_local_ccoeff | EMD | 0.0055 | 0.0049 |
| cluster_mean_degree | rmse | 0.0646 | 0.0510 |
| cluster_mean_degree | EMD | 0.0082 | 0.0056 |
| cluster_mean_kcore | rmse | 0.0810 | 0.0729 |
| cluster_mean_kcore | EMD | 0.0106 | 0.0089 |
| cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 |
| cluster_n_concomp | EMD | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 |
| cluster_pseudo_diameter | mean_l1 | 0.0682 | 0.0701 |
| cluster_pseudo_diameter | EMD | 0.0603 | 0.0624 |

### livemocha (n=104,103, m=2,193,083)

| stat | metric | ec-sbm-v1 / leiden-cpm-0.0001 | ec-sbm-v2 / leiden-cpm-0.0001 |
|---|---|:---:|:---:|
| cluster_deg_assort | rmse | 0.0894 | 0.0894 |
| cluster_deg_assort | EMD | 0.0162 | 0.0162 |
| cluster_global_ccoeff | rmse | 0.0209 | 0.0226 |
| cluster_global_ccoeff | EMD | 0.0011 | 0.0012 |
| cluster_local_ccoeff | rmse | 0.0211 | 0.0232 |
| cluster_local_ccoeff | EMD | 0.0010 | 0.0011 |
| cluster_mean_degree | rmse | 0.0203 | 0.0203 |
| cluster_mean_degree | EMD | 0.0011 | 0.0011 |
| cluster_mean_kcore | rmse | 0.0301 | 0.0316 |
| cluster_mean_kcore | EMD | 0.0016 | 0.0018 |
| cluster_n_concomp | mean_l1 | 0.0000 | 0.0000 |
| cluster_n_concomp | EMD | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | rmse | 0.0000 | 0.0000 |
| cluster_frac_giant_ccomp | EMD | 0.0000 | 0.0000 |
| cluster_pseudo_diameter | mean_l1 | 0.0636 | 0.0638 |
| cluster_pseudo_diameter | EMD | 0.0579 | 0.0580 |
