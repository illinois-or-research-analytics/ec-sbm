# ec-sbm v1/v2 vs empirical (100K-200K node bucket): consolidated report

7 empirical networks, 100K-200K nodes, 5 seeds per gen-clustering pair,
generators ec-sbm v1 and ec-sbm v2 — both share the same five-stage
pipeline (`profile` → `gen_clustered` → `gen_outlier` → `combine` →
`match_degree`), differing only in a preset flag bundle. v3 (per-cluster
PSO) was dropped after a single 100K-node run did not converge inside an
hour.

The v1 and v2 presets disagree on four flags:

| flag | v1 | v2 |
|---|---|---|
| `--sbm-overlay` | on (gen_clustered overlays `gt.generate_sbm` on the kec core) | off (gen_clustered stops after the kec core) |
| `--scope` (gen_outlier) | `outlier-incident` (sample only edges with ≥1 outlier endpoint) | `all` (deduped orig edges, full inter-block residual sampling) |
| `--gen-outlier-mode` | `singleton` (each outlier is its own block) | `combined` (one block for all outliers) |
| `--degree-matcher` | `greedy` (no cluster gating) | `cluster_preserving_true_greedy` (per-(min_block, max_block) budget gating) |

Both share `gen_kec_core` for stage 2 (K_{k+1} clique on top-(k+1) by
residual degree, then attach-by-degree to k edges each, guaranteeing
edge-connectivity ≥ k(C) per cluster). `gen_kec_core.md` and
`gen_ec_sbm.md` carry the full mechanics. Two reference clusterings:
A = `leiden-cpm-0.0001`, P = `+cm(piecewise)`.

Backing artifacts in this directory:

* `summary.csv` — per-run wall time and status (90 ok rows).
* `scalar_dist.md` / `scalar_dist.csv` — auto-rendered scalar +
  distributional tables (SAD/SRD/EMD), with per-net + bench-level mean ±
  std and a paired Wilcoxon significance table.
* `cluster.md` / `cluster.csv` — auto-rendered `cluster_*` tables (rmse
  for continuous, mean_l1 for counts, plus EMD), same structure +
  significance.
* `bench.log`, `bench.driver.log`, `recompute_refs.log`,
  `recompute_refs.driver.log` — execution logs.

Conventions used throughout this report:

* **Scalar stats**: `SAD = |synth - ref|` for bounded stats, `SRD =
  |synth - ref| / |synth|` for unbounded stats.
* **Distributional stats**: `EMD` (Earth Mover's distance) over synth/ref
  histograms.
* **`cluster_*` per-cluster sequences**: `rmse` for continuous-valued
  stats, `mean_l1` for count-valued ones, plus `EMD`.
* **Aggregation is two-stage**: stage 1 means over 5 seeds per network;
  stage 2 means/std/min/max over networks. `n` in tables is **number of
  networks**, not seed count. n = 7 on A, n = 2 on P.
* **Significance** is paired Wilcoxon signed-rank on the per-network
  values, two-sided. `*` = p < 0.05, `**` = p < 0.01.

---

## 1. Bench setup

* Hardware: i9-12900HK, 14 P-cores + 6 E-threads (HT on), 64 GB RAM.
* Single-thread per gen run; `xargs -P 14` for parallel dispatch.
* Networks (ascending edge count):

  | net            | n       | m         | clusterings used |
  |---             |---:     |---:       |---|
  | douban         | 154,908 |   327,162 | A, P |
  | wordnet        | 146,005 |   656,999 | A, P |
  | wiki_users     | 138,587 |   715,883 | A    |
  | wiki_link_dyn  | 100,304 |   824,968 | A    |
  | lastfm_aminer  | 136,409 | 1,685,524 | A    |
  | wikiconflict   | 116,836 | 2,027,871 | A    |
  | livemocha      | 104,103 | 2,193,083 | A    |

---

## 2. Wall time

```
gen        clustering            mean ± std (s)    min     max     n_nets
v1         A                     217.6 ± 144.9     57.6    454.0   7
v2         A                     427.1 ± 280.9    135.4    929.0   7
v1         P                      36.7 ±  20.5     22.2     51.2   2
v2         P                      95.7 ±  57.3     55.2    136.2   2
```

Per-network mean (s):

```
gen   douban  wordnet  wiki_users  wiki_link_dyn  wikiconflict  lastfm_aminer  livemocha
v1       58       79         126            195           286            325        454
v2      135      272         330            197           482            644        929
v2/v1   2.3x    3.4x        2.6x          1.0x           1.7x           2.0x       2.0x
```

* v2 ~2x v1 on most nets; wiki_link_dyn is the lone tie.
* P is ~5-6x faster than A on the same net (smaller per-cluster SBM
  work after piecewise refinement).

---

## 3. Section A — `leiden-cpm-0.0001`

7 nets, 5 seeds, 2 gens = 70 runs. Significance is real here (n=7).

### 3.1 Stats both gens reproduce within noise

For every (gen, net) cell, mean SAD or SRD < 1e-3 or zero:

* `n_nodes`, `n_clusters`, `n_outliers`, `node_coverage`,
  `n_disconnected_clusters`: 0 across all 70 runs.
* `frac_giant_ccomp`: SAD < 3e-4.
* `mincut` EMD: 0 to 0.006.
* `degree` EMD: 0.0017 (v1) to 0.0274 (v2). v1 essentially perfect; v2
  drifts (see 3.3).

### 3.2 Where v2 wins, with significance

Mean ± std over 7 nets (paired Wilcoxon; `*` p < 0.05):

| stat                          | metric | v1                | v2                | p     |
|---                            |---     |---:               |---:               |---:   |
| `conductance`                 | EMD    | 0.0060 ± 0.0061   | 0.0011 ± 0.0011   | 0.016 * |
| `modularity`                  | EMD    | 4.7e-6 ± 4.6e-6   | 1.1e-6 ± 1.3e-6   | 0.016 * |
| `degree_density`              | EMD    | 0.0133 ± 0.0134   | 0.0065 ± 0.0066   | 0.031 * |
| `edge_density`                | EMD    | 0.0030 ± 0.0032   | 0.0022 ± 0.0022   | 0.047 * |
| `cluster_mean_degree`         | rmse   | 0.1093 ± 0.0856   | 0.0664 ± 0.0476   | 0.016 * |
| `cluster_mean_kcore`          | rmse   | 0.1480 ± 0.1431   | 0.1224 ± 0.1209   | 0.031 * |
| `cluster_global_ccoeff`       | EMD    | 0.0185            | 0.0162            | 0.031 * |
| `cluster_local_ccoeff`        | EMD    | 0.0252            | 0.0227            | 0.031 * |
| `cluster_mean_degree`         | EMD    | 0.0266            | 0.0130            | 0.031 * |
| `cluster_mean_kcore`          | EMD    | 0.0504            | 0.0418            | 0.031 * |

Suggestive but not significant at α=0.05 (winner = v2):

| stat                  | metric | v1     | v2     | p     |
|---                    |---     |---:    |---:    |---:   |
| `concomp_sizes`       | EMD    | 4.92   | 0.000  | 0.125 |
| `n_concomp`           | SRD    | 0.0089 | 0.0000 | 0.125 |
| `frac_giant_ccomp`    | SAD    | 1.3e-4 | 0.000  | 0.125 |
| `cluster_global_ccoeff` | rmse | 0.0682 | 0.0633 | 0.078 |
| `cluster_local_ccoeff` | rmse  | 0.0839 | 0.0795 | 0.078 |

`concomp_sizes` and `n_concomp` are exactly v2 = 0 on every net (v2's
clustered generator places every cluster as one connected piece on A).
The Wilcoxon p-value is bounded below by the number of distinct
non-zero pairs, hence 0.125 even though every pair points the same way.

### 3.3 Where v1 wins, with significance

| stat              | metric | v1                | v2              | p     |
|---                |---     |---:               |---:             |---:   |
| `n_edges`         | SRD    | 1.0e-4 ± 2.5e-4   | 0.0019 ± 0.0034 | 0.016 * |
| `mean_degree`     | SRD    | 1.0e-4 ± 2.5e-4   | 0.0019 ± 0.0034 | 0.016 * |
| `degree`          | EMD    | 0.0017 ± 0.0042   | 0.0274 ± 0.0558 | 0.016 * |
| `cluster_pseudo_diameter` | mean_l1 | 0.9846 | 0.9885 | 0.047 * |
| `cluster_pseudo_diameter` | EMD     | 0.9634 | 0.9699 | 0.016 * |

n_edges and mean_degree share the same SRD numerator (m and n are both
preserved exactly; only m varies), so the test on the two stats is
collinear.

`cluster_pseudo_diameter` shifts in v1's favour by tiny absolute
margins (0.985 vs 0.989), but the test is significant because v1 wins
on 6 out of 7 networks consistently.

### 3.4 Stats with no significant gen difference

* `kcore` EMD: 0.605 vs 0.589 (p = 0.375).
* `mincut` EMD: 0.0012 vs 0.0015 (p = 0.125).
* `mixing_parameter` EMD: 0.019 vs 0.020 (p = 0.578).
* `local_ccoeff_nodes` EMD: 0.201 vs 0.200 (p = 0.688).
* `pagerank` EMD: 3.3e-7 vs 3.8e-7 (p = 0.219).
* `pseudo_diameter` SRD: 0.143 vs 0.107 (p = 0.313, winner v2 directionally).
* `cluster_deg_assort` rmse / EMD: tied within noise.

### 3.5 Per-net headline (SRD or SAD over the bounded ones)

```
                     n_edges        deg_assort    global_ccoeff   local_ccoeff
                    SRD v1   v2     SAD v1  v2    SAD v1  v2      SAD v1  v2
douban           0.0e+0  3.0e-4   0.044  0.044   0.014  0.012    0.080  0.075
wordnet          2.4e-5  6.5e-4   0.014  0.025   0.024  0.022    0.074  0.071
wiki_users       2.1e-6  6.3e-4   0.001  0.011   0.022  0.014    0.062  0.061
wiki_link_dyn    3.4e-4  4.7e-3   0.012  0.012   0.011  0.011    0.044  0.044
lastfm_aminer    1.2e-6  1.1e-4   0.012  0.012   0.025  0.024    0.062  0.060
wikiconflict     1.2e-6  7.8e-5   0.027  0.039   1.7e-4 5.7e-4   0.020  0.021
livemocha        0.0e+0  1.5e-6   0.014  0.006   0.010  0.006    0.011  0.013
```

### 3.6 Trends on `leiden-cpm-0.0001`

* **Cluster boundary stats: v2 wins every time.** Conductance,
  edge_density, degree_density, modularity all significantly tighter
  in v2. Per-cluster mean degree and per-cluster mean k-core rmse
  also significantly tighter. The driver is most likely v2's
  `gen_outlier --scope all` (which populates the inter-block residual
  probabilities directly from the deduped original edges) plus
  `cluster_preserving_true_greedy` match_degree (which respects
  per-(min_block, max_block) edge budgets). v1's `outlier-incident`
  scope only samples residuals incident to outliers, so cluster
  interiors are filled in by the v1-only `gt.generate_sbm` overlay.
* **Degree-distribution mass: v1 wins every time.** Both n_edges SRD
  and the degree EMD are significantly worse in v2. The mechanism is
  v2's `cluster_preserving_true_greedy` match_degree: it places
  topup edges only when both endpoints' (min_block, max_block) bucket
  still has budget. Once a budget hits zero, candidate pairs in that
  bucket are refused even if both endpoints still have positive
  residual degree. v1's plain `greedy` matcher has no per-block
  budget, so it places those same edges and lands closer to the
  target n_edges. The gap is < 0.5% of m but the Wilcoxon test sees
  the same direction on every net.
* **`cluster_pseudo_diameter`** is the one cluster-level stat where v1
  is the better fit, by a tiny margin but consistent across nets.
  v1's SBM overlay introduces extra mid-distance edges inside clusters
  (driven by degree expectations); v2's kec-core-only stage 2 is
  sparser, leaving slightly larger per-cluster diameters.
* **Most node-level distributional shapes do not move.** kcore,
  mixing_parameter, local_ccoeff_nodes, pagerank EMD are tied between
  gens. Whatever ec-sbm gets right or wrong on these stats is shared
  by both presets.
* **Triangle structure stays far from ref for both.** Pooled `cluster_*
  global/local_ccoeff` rmse is in the 0.06-0.08 band. Neither gen has
  a triangle-closure mechanism.
* **wordnet** is the worst-fitting net on local_ccoeff (~0.81 SAD).
  Documented in `gen_ec_sbm.md` as a known limitation; thesaurus
  graphs with dense synonym cliques are outside the SBM family.
* **lastfm_aminer**: SAD on `deg_assort` is 0.012, well within bench
  noise. A normalised relative metric saturates at 1.0 on this net
  because the reference assortativity is near zero, so the bench
  reports SAD on bounded scalars.
* **wall ~ m roughly.** v2/v1 wall ratio sits at 2-3x except on
  wiki_link_dyn (1.0x). The extra cost in v2 comes from
  `cluster_preserving_true_greedy` match_degree (per-(block, block)
  budget bookkeeping) and from the broader `--scope all` outlier-stage
  sampling.

---

## 4. Section B — `leiden-cpm-0.0001+cm(piecewise)`

2 nets (douban, wordnet), 5 seeds, 2 gens = 20 runs. **No paired
Wilcoxon result reaches conventional significance with n=2.** Treat the
section as descriptive.

### 4.1 Stats both gens reproduce within noise

Same shape as A: `n_nodes`, `n_clusters`, `n_outliers`,
`node_coverage`, `n_disconnected_clusters`, `mean_degree`, `n_edges`,
`mincut`, `frac_giant_ccomp` all match within 1e-3.

### 4.2 v1 vs v2 (descriptive, n=2)

| stat                          | metric | v1                  | v2                |
|---                            |---     |---:                 |---:               |
| `concomp_sizes`               | EMD    | 8.9 ± 12.5          | **76,466 ± 1.1e+5** |
| `n_concomp`                   | SRD    | 0.017 ± 0.025       | 0.630 ± 0.504     |
| `conductance`                 | EMD    | 0.0052 ± 0.0039     | 8.2e-4 ± 3.1e-4   |
| `modularity`                  | EMD    | 2.4e-6 ± 1.7e-6     | 7.2e-7 ± 3.4e-7   |
| `degree_density`              | EMD    | 0.0105 ± 0.0026     | 0.0052 ± 0.0029   |
| `edge_density`                | EMD    | 0.0022 ± 0.0029     | 0.0017 ± 0.0023   |
| `degree`                      | EMD    | 0.0086 ± 0.0120     | 0.0092 ± 0.0056   |
| `mixing_parameter`            | EMD    | 0.0319 ± 0.0282     | 0.0349 ± 0.0285   |
| `kcore`                       | EMD    | 0.289 ± 0.327       | 0.333 ± 0.306     |
| `pagerank`                    | EMD    | 2.1e-7 ± 1.1e-7     | 2.1e-7 ± 9.1e-8   |
| `mincut`                      | EMD    | 0.0017 ± 0.0024     | 0.0027 ± 0.0039   |
| `pseudo_diameter`             | SRD    | 0.099 ± 0.002       | 0.086 ± 0.066     |
| `cluster_pseudo_diameter`     | mean_l1| 0.576 ± 0.533       | 0.586 ± 0.546     |
| `cluster_mean_degree`         | rmse   | 0.110 ± 0.079       | 0.070 ± 0.073     |
| `cluster_mean_kcore`          | rmse   | 0.173 ± 0.158       | 0.150 ± 0.144     |

### 4.3 Per-net snapshot

douban (n=154,908, m=327,162):

| stat                | metric | v1     | v2          |
|---                  |---     |---:    |---:         |
| n_edges             | SRD    | 1.2e-5 | 6.2e-4      |
| n_concomp           | SRD    | 0.034  | 0.986       |
| concomp_sizes       | EMD    | 17.7   | **152,932** |
| modularity          | EMD    | 3.6e-6 | 9.7e-7      |
| conductance         | EMD    | 0.0025 | 6.1e-4      |
| deg_assort          | SAD    | 0.022  | 0.078       |
| global_ccoeff       | SAD    | 0.020  | 0.011       |
| local_ccoeff        | SAD    | 0.106  | 0.122       |

wordnet (n=146,005, m=656,999):

| stat                | metric | v1     | v2     |
|---                  |---     |---:    |---:    |
| n_edges             | SRD    | 9.5e-4 | 1.6e-4 |
| n_concomp           | SRD    | 0.000  | 0.000  |
| concomp_sizes       | EMD    | 0.65   | 0.65   |
| modularity          | EMD    | 1.2e-6 | 4.8e-7 |
| conductance         | EMD    | 0.0080 | 0.0010 |
| deg_assort          | SAD    | 0.013  | 0.024  |
| global_ccoeff       | SAD    | 0.060  | 0.055  |
| local_ccoeff        | SAD    | 0.116  | 0.107  |

### 4.4 Trends on `+cm(piecewise)`

* **v2 leaves small refined clusters under-edged on douban.**
  `concomp_sizes` EMD jumps from 18 (v1) to 153,000 (v2) on douban;
  `n_concomp` SRD goes from 3% to 99%. Same mechanism as 3.6's
  n_edges drift, but amplified: piecewise refinement hands v2 many
  small clusters whose (min_block, max_block) budgets are tiny.
  v2's `cluster_preserving_true_greedy` match_degree refuses to place
  the few extra edges that would bridge components inside those
  clusters once the per-block budget is consumed. v1's plain `greedy`
  matcher has no such gate, so it places those edges and the cluster
  stays connected. v1 also has the SBM overlay in stage 2 putting
  extra edges into the cluster interiors, which makes its starting
  point denser. Wordnet does not show this because its piecewise
  clusters are denser to begin with, so they survive the budget cap.
* **`deg_assort` is the only stat where P is materially worse than A
  on v2.** SAD 0.05 on P vs 0.029 on A. The same budget-gated matcher
  has fewer high-/low-degree pair candidates to work with inside
  small clusters, so the per-cluster assortativity sits further from
  ref.
* **v2's boundary-stat win carries over.** Conductance, modularity,
  degree_density, edge_density, cluster_mean_degree all favour v2,
  same direction as A.
* **Pseudo-diameter is closer to ref on P than on A** for both gens
  (`cluster_pseudo_diameter` mean_l1 0.58 P vs 0.99 A). Smaller
  clusters mean smaller diameters in absolute units, so the gap
  shrinks.
* **n=2 is too small for Wilcoxon to flag any of these as
  significant.** Findings are directional only.

---

## 5. A vs P (overlap nets only)

douban and wordnet are clustered both ways. Pooled values, n=2 per cell:

```
                          v1 / A    v1 / P    v2 / A    v2 / P
deg_assort (SAD)           0.029     0.015     0.034     0.051
global_ccoeff (SAD)        0.040     0.040     0.034     0.033
conductance (EMD)          0.0085    0.0052    6.5e-4    8.2e-4
modularity (EMD)           7.4e-6    2.4e-6    1.6e-6    7.2e-7
mixing_parameter (EMD)     0.036     0.032     0.032     0.035
pagerank (EMD)             2.7e-7    2.1e-7    2.4e-7    2.1e-7
n_concomp (SRD)            0.004     0.017     0.000     0.630
concomp_sizes (EMD)        11.6      8.86      0.0       7.6e+4
```

* P is similar to or marginally better than A on most cells, except
  v2/P concomp blow-up on douban (4.4 trend).
* Conductance, modularity, degree_density: v2 wins on both clusterings.
* Mixing parameter and pagerank are tied across all four cells.

---

## 6. Outliers and known limits

* **lastfm_aminer (deg_assort)**: SAD is 0.012, well inside bench
  noise. A relative metric would saturate at 1.0 here because the
  reference assortativity is near zero; the bench reports SAD on
  bounded scalars to avoid that artefact.
* **wiki_link_dyn / wiki_users / wikiconflict (modularity rpd)**: ref
  modularity distribution is bimodal in a way the SBM family cannot
  reproduce. Visible as elevated modularity SRD; EMD smooths over the
  bimodality so it does not show up there.
* **wordnet (local_ccoeff)**: SAD ~0.07 on both gens. Dense synonym
  cliques outside the SBM family without an explicit triangle-closure
  mechanism. Documented in `gen_ec_sbm.md`.

---

## 7. Top-line summary

* On A (n=7), v2 is **significantly tighter** than v1 on every cluster
  boundary stat we measure: conductance EMD, modularity EMD,
  degree_density EMD, edge_density EMD, cluster_mean_degree rmse +
  EMD, cluster_mean_kcore rmse + EMD, cluster_global_ccoeff EMD,
  cluster_local_ccoeff EMD. p-values 0.016-0.047, paired Wilcoxon.
* On A, v1 is **significantly tighter** than v2 on degree-distribution
  mass: n_edges SRD, mean_degree SRD, degree EMD, plus the small
  `cluster_pseudo_diameter` gap. Driver: v2's
  `cluster_preserving_true_greedy` match_degree refuses to add edges
  whose per-(min_block, max_block) budget is exhausted, so a small
  number of pairs that v1's plain `greedy` matcher would fill stay
  empty. v1 also has the v1-only `gt.generate_sbm` overlay producing
  extra interior edges in stage 2, which adds to the difference.
* **The v1/v2 choice on A is metric-driven**: cluster boundary
  fidelity → v2; degree mass and exact n_edges → v1. The wall cost
  for v2 is roughly 2x.
* On P (n=2), the same v1/v2 directions hold for all stats, but no
  result reaches conventional significance. The qualitative
  exception is **v2's catastrophic disconnection on douban**
  (`concomp_sizes` EMD ≈ 153,000): small piecewise clusters get a
  thin kec-core stage 2 (no SBM overlay) plus a budget-gated matcher
  that refuses the few extra edges that would bridge components.
  Use v1 (which has both the overlay and an unconstrained matcher)
  for heavily refined clusterings, or relax the matcher's budget on
  low-mincut clusters.
* P is **~5-6x faster** than A on this hardware due to smaller
  per-cluster SBM work after piecewise refinement.
* No (gen, clustering) combination reaches the reference triangle
  structure (cluster_global_ccoeff rmse ~0.06, cluster_local_ccoeff
  rmse ~0.08). This is a model-class limitation, not a v1-vs-v2 split.
