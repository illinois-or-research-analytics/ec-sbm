# Edge-Connected Stochastic Block Model (EC-SBM)

Two variants of a stochastic block model whose intra-cluster subgraph is
k-edge-connected (where k is the empirical per-cluster min-cut). Outlier nodes
(unclustered or singleton) are synthesized in a dedicated stage.

- **v1**: constructive k-edge-connected core + SBM overlay on the mutated
  inter-cluster edge-count matrix; separate SBM for outliers; greedy
  degree-matching top-up.
- **v2**: constructive-only clustered stage, then a residual SBM over all
  blocks (clustered + outliers under a chosen outlier-block policy) with
  block-preserving 2-opt rewiring, and a pluggable degree-matching stage
  (default hybrid).

v1 and v2 share a single configurable module pair
(`gen_clustered.py` + `gen_outlier.py`). `--version` picks a preset
flag bundle; individual flags can still be overridden for ablations or
custom mixes.

v1 is the version used in the original EC-SBM paper. If you use our work in your research, please cite:

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

| Flag | Scope | v1 preset | v2 preset | Description |
| --- | --- | --- | --- | --- |
| `--version {v1\|v2}` | required | - | - | Selects the preset flag bundle. |
| `--seed N` | all | `1` | `1` | RNG seed. Under a fixed seed the pipeline is byte-reproducible. |
| `--n-threads N` | all | `1` | `1` | Sets `OMP_NUM_THREADS`. |
| `--timeout DUR` | all | `3d` | `3d` | Per-stage `timeout(1)` budget. |
| `--outlier-mode {excluded\|singleton\|combined}` | stage 1 | `excluded` (fixed) | `excluded` | How the profile stage handles outliers. v1 rejects anything other than `excluded`. |
| `--drop-outlier-outlier-edges` / `--keep-outlier-outlier-edges` | stage 1 | keep | keep | Drop or retain edges between two outlier nodes at profile time. |
| `--sbm-overlay` / `--no-sbm-overlay` | stage 2 | on | off | Whether stage 2 runs `gt.generate_sbm` on the mutated residual and overlays the constructive core (v1) or emits the core only (v2). |
| `--scope {outlier-incident\|all}` | stage 3a | `outlier-incident` | `all` | Which orig edges contribute to the residual SBM's `probs` and `out_degs`: outlier-incident only (v1) or every edge, diag-adjusted (v2). |
| `--gen-outlier-mode {combined\|singleton}` | stage 3a | `singleton` | `combined` | How outlier nodes are assigned to blocks during the residual SBM. |
| `--edge-correction {none\|drop\|rewire}` | stage 3a | `none` | `rewire` | Post-SBM correction. `rewire` does block-preserving 2-opt swaps; `drop` / `none` rely on `remove_parallel_edges + remove_self_loops`. |
| `--match-degree-algorithm {greedy\|true_greedy\|random_greedy\|rewire\|hybrid}` | stage 4a | `greedy` | `hybrid` | How stage 4 tops up residual degrees. |

Any explicit flag overrides the `--version` preset, so you can run,
for example, `--version v2 --sbm-overlay --scope all` to mix the v1
stage-2 overlay with v2's residual accounting.

### Output layout

```
<output-dir>/
├── edge.csv         # final synthetic network (source,target)
├── com.csv          # clustering used for generation (outliers per mode)
├── sources.json     # provenance ranges per origin stage
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
    --input-edgelist examples/input/dnc/edge.csv \
    --input-clustering examples/input/dnc/com.csv \
    --output-dir /tmp/dnc-v1 \
    --seed 1

sha256sum /tmp/dnc-v1/edge.csv
# e2b5a6914b12f39c9356bbeba17a61ef82b0ce97258caf1dfef45b42d64a3d5b
```

v2 on the same input (with default `--match-degree-algorithm hybrid`,
`--edge-correction rewire`, `--gen-outlier-mode combined`) yields edge.csv
sha256 `f46e7d8b94c99fcc3cddbb7b6381c81e05c8b1f25d40134a7ed87b47910a1289`.

## Stages

All stages consume and produce CSV files with headers; invoke them directly
by setting `PYTHONPATH` to include `src/`. The package lives at `src/`
(mirrors the layout used in network-generation's `src/`).

1. **Profile**: extracts node/cluster iid maps, per-node degree, per-cluster
   min-cut, inter-cluster edge counts, and the outlier-transformed clustering.
   `src/profile.py`.
2. **gen_clustered**: builds the k-edge-connected clustered subgraph.
   `src/gen_clustered.py`. The constructive K_{k+1} clique core lives in
   `src/gen_cliques.py` and is used as the first step regardless of
   preset; the `--sbm-overlay` flag controls whether a residual SBM
   pass is layered on top.
3. **gen_outlier**: SBM-samples the edges that stage 2 did not place.
   `src/gen_outlier.py`. The `--scope` + `--gen-outlier-mode` + `--edge-correction`
   flags shape how the residual SBM's `probs` and `out_degs` are computed
   and how invalid edges are handled.
4. **match_degree**: tops up per-node degree to match the empirical
   distribution. `src/match_degree.py`.

Stage 3b and 4b run `src/combine_edgelists.py` to merge edgelists with
provenance tracking.

## Installation

See [INSTALL.md](INSTALL.md).
