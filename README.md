# Edge-Connected Stochastic Block Model (EC-SBM)

Two variants of a stochastic block model whose intra-cluster subgraph is
k-edge-connected (where k is the empirical per-cluster min-cut). Outlier
nodes (unclustered or singleton) are synthesized in a dedicated stage.

- **v1**: constructive k-edge-connected core + SBM overlay on the mutated
  inter-cluster edge-count matrix; outlier-incident residual SBM with
  each outlier in its own block; greedy degree-matching top-up.
- **v2**: constructive-only clustered stage, then a residual SBM over
  all blocks (clustered + outliers under a chosen outlier-block policy)
  with block-preserving 2-opt rewiring, and a pluggable degree-matching
  stage (default hybrid).
- **v3**: per-cluster PSO core (uniform angular distribution, `m >= k`)
  with a 1-D bisection-secant search on the temperature `T` to drive
  each cluster's clustering coefficient toward its empirical target;
  v2-style residual SBM and degree-matching for the remainder.

The v1 variant is published in [Vu-Le et al. 2025](https://doi.org/10.1007/s41109-025-00701-2). If you use it in your research, please cite the paper:

```
@article{vule2025ecsbm,
  title = {EC-SBM synthetic network generator},
  volume = {10},
  ISSN = {2364-8228},
  url = {http://dx.doi.org/10.1007/s41109-025-00701-2},
  DOI = {10.1007/s41109-025-00701-2},
  number = {1},
  journal = {Applied Network Science},
  publisher = {Springer Science and Business Media LLC},
  author = {Vu-Le,  The-Anh and Anne,  Lahari and Chacko,  George and Warnow,  Tandy},
  year = {2025},
  month = May
}
```

## Usage

```bash
bash scripts/run_ecsbm.sh \
    --version v1 \
    --input-edgelist   <path/to/empirical>/edge.csv \
    --input-clustering <path/to/empirical>/com.csv \
    --output-dir       <path/to/output>
```

Inputs:
- `edge.csv`: CSV with header `source,target`.
- `com.csv`: CSV with header `node_id,cluster_id`. Unclustered nodes and
  singleton clusters are treated as outliers.

### Flags

| Flag | Scope | v1 preset | v2 preset | v3 preset | Description |
| --- | --- | --- | --- | --- | --- |
| `--version {v1\|v2\|v3}` | required | - | - | - | Selects the preset flag bundle. |
| `--seed N` | all | `1` | `1` | `1` | RNG seed. Under a fixed seed the pipeline is byte-reproducible. |
| `--n-threads N` | all | `1` | `1` | `1` | Sets `OMP_NUM_THREADS`. |
| `--timeout DUR` | all | `3d` | `3d` | `3d` | Per-stage `timeout(1)` budget. |
| `--outlier-mode {excluded\|singleton\|combined}` | stage 1 | `excluded` | `excluded` | `excluded` | How the profile stage handles outliers. |
| `--drop-outlier-outlier-edges` / `--keep-outlier-outlier-edges` | stage 1 | keep | keep | keep | Drop or retain edges between two outlier nodes at profile time. |
| `--sbm-overlay` / `--no-sbm-overlay` | stage 2 (v1/v2) | on | off | n/a | Whether stage 2 runs `gt.generate_sbm` on the mutated residual and overlays the k-edge-connected core (v1) or emits the core only (v2). v3's stage 2 is the PSO core; this flag is recorded but ignored. |
| `--scope {outlier-incident\|all}` | stage 3a | `outlier-incident` | `all` | `all` | Which orig edges contribute to the residual SBM's `probs` and `out_degs`. |
| `--gen-outlier-mode {combined\|singleton}` | stage 3a | `singleton` | `combined` | `combined` | How outlier nodes are assigned to blocks during the residual SBM. |
| `--edge-correction {none\|drop\|rewire}` | stage 3a | `none` | `rewire` | `rewire` | Post-SBM correction. `rewire` does block-preserving 2-opt swaps. |
| `--degree-matcher {greedy\|true_greedy\|random_greedy\|rewire\|hybrid}` | stage 4a | `greedy` | `true_greedy` | `true_greedy` | How stage 4 tops up residual degrees. |
| `--pso-gamma F` | stage 2 (v3) | n/a | n/a | `2.0` | PSO power-law exponent. Default `2.0` makes radial coords `r_i = 2*log(arrival_rank)` where arrival rank comes from the descending empirical-degree sort, so the PSO geometry encodes the empirical degree ordering. |
| `--pso-m-policy {auto\|floor}` | stage 2 (v3) | n/a | n/a | `auto` | `auto` lifts m to `round(empirical_mean_intra_deg/2)`; `floor` skips the lift. |
| `--pso-m-floor N` | stage 2 (v3) | n/a | n/a | `1` | Hard lower bound on per-cluster m. |
| `--pso-search-strategy {bayesian\|secant}` | stage 2 (v3) | n/a | n/a | `secant` | `secant` is bisection + secant, fast and accurate on the trend-with-noise objective (sweep at `tools/npso_bo_sweep/`). `bayesian` uses Optuna TPE; opt-in for ablation or non-monotone regimes. |
| `--pso-search-samples-per-T N` | stage 2 (v3) | n/a | n/a | `3` | Average this many PSO realisations per T probe to suppress noise (linear cost in eval time). |
| `--pso-search-{max-iters,initial-points,diff-tol,step-tol,t-min,t-max,initial-t}` | stage 2 (v3) | n/a | n/a | `30 / 3 / 0.01 / 1e-4 / 0.01 / 0.99 / 0.5` | T-search controls. `initial-points` is BO-only (TPE warm-up before the surrogate takes over). |

Any explicit flag overrides the `--version` preset, so for example
`--version v2 --sbm-overlay --scope all` mixes v1's stage-2 overlay
with v2's residual accounting.

### Output layout

```
<output-dir>/
├── edge.csv         # final synthetic network (source,target)
├── com.csv          # clustering used for generation (outliers per mode)
├── sources.json     # provenance ranges per origin stage
├── params.txt       # full flag bundle used for this run
├── run.log          # consolidated per-stage logs
└── stage/           # per-stage intermediates
    ├── profile/
    ├── gen_clustered/
    ├── gen_outlier/edges/
    ├── gen_outlier/
    ├── match_degree/edges/
    └── match_degree/
```

## Example

```bash
bash scripts/run_ecsbm.sh \
    --version v1 \
    --input-edgelist   examples/input/dnc/edge.csv \
    --input-clustering examples/input/dnc/com.csv \
    --output-dir       examples/output/ec-sbm-v1 \
    --seed 1

sha256sum examples/output/ec-sbm-v1/edge.csv
# 42128ea4b826a7c64f59b1905ae124374741fe0feb68fa3e9c0604b2c15bc302
```

v2 on the same input yields `edge.csv` with sha256
`c63606b9f55871d26ee564f12b86a32c480517c8dbbc55048e6bde89dcb559fc`.
v3 (per-cluster PSO + secant T-search, default knobs) yields sha256
`4efb2e467206fdad40459d9975b0fa7fdf81444bce927df9c649842c2273ddae`.
The `examples/output/ec-sbm-v{1,2,3}/` trees are committed as reference
outputs.

## Stages

All stages consume and produce CSV files with headers; invoke them
directly by setting `PYTHONPATH` to include `src/`.

1. **Profile**: extracts node/cluster iid maps, per-node degree,
   per-cluster min-cut, inter-cluster edge counts, and the
   outlier-transformed clustering. `src/profile.py`.
2. **gen_clustered**: builds the clustered subgraph. `src/gen_clustered.py`
   calls the constructive k-edge-connected core in `src/gen_kec_core.py`
   (K_{k+1} clique on the top-(k+1) nodes + attach-by-degree for the
   rest); the `--sbm-overlay` flag controls whether a residual SBM pass
   is layered on top. **v3** swaps this stage for `src/gen_clustered_v3.py`,
   which calls the Python PSO port in `src/gen_pso_core.py` once per
   cluster and runs a 1-D bisection-secant search on `T` to match the
   empirical per-cluster clustering coefficient (search trace persisted
   to `pso_search_log.json`).
3. **gen_outlier**: SBM-samples the edges that stage 2 did not place.
   `src/gen_outlier.py`. The `--scope`, `--gen-outlier-mode`, and
   `--edge-correction` flags shape how the residual SBM's `probs` and
   `out_degs` are computed and how invalid edges are handled.
4. **match_degree**: tops up per-node degree to match the empirical
   distribution. `src/match_degree.py`.

Stage 3b and 4b run `src/combine_edgelists.py` to merge edgelists with
provenance tracking.

## Installation

See [INSTALL.md](INSTALL.md).

## Acknowledgements

- [graph-tool](https://graph-tool.skewed.de/) for the SBM sampler and
  core graph types.
- [python-mincut](https://github.com/vikramr2/python-mincut) for VieCut 
  wrapper to compute min-cut used in the profile stage.
