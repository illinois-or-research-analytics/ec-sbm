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

Full per-stage algorithmic detail lives upstream in the
[`vltanh/network-generation`](https://github.com/vltanh/network-generation)
per-algorithm docs; this repo is the standalone entry point.

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

| Flag | Versions | Default | Description |
| --- | --- | --- | --- |
| `--version {v1\|v2}` | both | - | Required. |
| `--seed N` | both | `1` | RNG seed. Under a fixed seed the pipeline is byte-reproducible. |
| `--n-threads N` | both | `1` | Sets `OMP_NUM_THREADS`. |
| `--timeout DUR` | both | `3d` | Per-stage `timeout(1)` budget. |
| `--outlier-mode {excluded\|singleton\|combined}` | v2 | `excluded` | Profile-stage outlier handling. v1 rejects anything other than `excluded`. |
| `--drop-outlier-outlier-edges` / `--keep-outlier-outlier-edges` | v2 | keep | Drop or retain edges between two outlier nodes at profile time. |
| `--gen-outlier-mode {combined\|singleton}` | v2 | `combined` | Residual-SBM outlier block grouping. |
| `--edge-correction {drop\|rewire}` | v2 | `rewire` | Stage 3 parallel/self-loop handling. `rewire` preserves degree via 2-opt swaps; `drop` removes offenders. |
| `--match-degree-algorithm {greedy\|true_greedy\|random_greedy\|rewire\|hybrid}` | v2 | `hybrid` | Stage 4 degree-matching method. v1 is fixed to `greedy`. |

### Output layout

```
<output-dir>/
├── edge.csv         # final synthetic network (source,target)
├── com.csv          # clustering used for generation (outliers per mode)
├── sources.json     # provenance ranges per origin stage
├── run.log          # consolidated per-stage logs
└── stage/           # per-stage intermediates (always retained)
    ├── profile/
    ├── gen_clustered/
    ├── gen_outlier/edges/
    ├── gen_outlier/
    ├── match_degree/edges/
    └── match_degree/
```

The standalone script has no caching or stage short-circuit; every invocation
runs all stages from scratch. The network-generation pipeline wrapper is the
cached version; see below.

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
by setting `PYTHONPATH` to include `ec-sbm/common` and `ec-sbm`.

1. **Profile**: extracts node/cluster iid maps, per-node degree, per-cluster
   min-cut, inter-cluster edge counts, and the outlier-transformed clustering.
   `ec-sbm/common/profile.py`.
2. **gen_clustered**: builds the k-edge-connected clustered subgraph.
   `ec-sbm/v{1,2}/gen_clustered.py`. v1 layers an SBM pass on top; v2 is
   constructive-only.
3. **gen_outlier**: synthesizes the remaining edges via SBM.
   `ec-sbm/v1/gen_outlier.py` covers outlier-only edges;
   `ec-sbm/v2/gen_outlier.py` runs a residual SBM across all blocks with
   optional 2-opt rewiring.
4. **match_degree**: tops up per-node degree to match the empirical
   distribution. `ec-sbm/match_degree.py`. v1 pins `greedy`; v2 defaults to
   `hybrid`.

Stage 3b and 4b run `ec-sbm/combine_edgelists.py` to merge edgelists with
provenance tracking.

## Relationship to network-generation

[`vltanh/network-generation`](https://github.com/vltanh/network-generation) is
a cross-algorithm harness covering sbm, abcd, abcd+o, lfr, npso, ec-sbm-v1,
ec-sbm-v2. It invokes this repo's algorithm modules through a stage-aware
pipeline wrapper (`src/ec-sbm/v{1,2}/pipeline.sh`) that adds sha256 done-files
and stage-level caching. The wrappers shadow ec-sbm's vendored helpers with
the canonical copies in `src/`.

Use this repo when you want ec-sbm only. Use network-generation when you want
to compare across algorithms or reuse the cached-stage orchestration.

## Installation

See [INSTALL.md](INSTALL.md).
