# ec-sbm v1/v2 bench (100K-200K node bucket)

Outputs of the parallel ec-sbm benchmark on 7 empirical networks
(100K-200K nodes), against `leiden-cpm-0.0001` and its
`+cm(piecewise)` variant. Driver scripts live in
[`../../scripts/bench/`](../../scripts/bench).

## Files

| file | description |
|---|---|
| `report.md` | Narrative comparison report. Read this first. |
| `scalar_dist.md` | Auto-rendered scalar/distributional/wall tables, with paired-Wilcoxon significance. |
| `scalar_dist.csv` | Tidy long-form CSV behind `scalar_dist.md`. |
| `cluster.md` | Auto-rendered `cluster_*` tables (rmse for continuous stats, mean_l1 for counts, EMD for distribution check). |
| `cluster.csv` | Tidy long-form CSV behind `cluster.md`. |
| `summary.csv` | Bench summary row per (gen, clustering, net, seed): `gen, clustering, net, seed, run_id, status, wall_s`. |
| `bench.log` | Driver log (one line per START/END/SKIP, flock-serialised). |
| `bench.driver.log` | Stdout capture of the run_bench.sh launch. |
| `recompute_refs.log` / `recompute_refs.driver.log` | Logs from the stats recompute pass. |

## Distance metric conventions

* **Scalar stats**:
    * Bounded ([0, 1] or [-1, 1]): `SAD = |synth - ref|` in original units.
    * Unbounded: `SRD = |synth - ref| / |synth|`, dimensionless.
* **Distributional stats**: `EMD` (Earth Mover's distance) over the
  synth/ref histograms, in original units.
* **`cluster_*` per-cluster sequences**:
    * Continuous-valued: `rmse` (squared error penalises per-cluster
      outliers).
    * Count-valued (`cluster_n_concomp`, `cluster_pseudo_diameter`):
      `mean_l1` (average integer gap per cluster).
    * Plus `EMD` over the per-cluster value histogram as a
      distribution-shape check.

All metrics are 0 = perfect.

## Aggregation

Two-stage:
1. Mean over the 5 seeds per (gen, clustering, net) → per-network value.
2. Mean / std / min / max over the networks within each (gen,
   clustering) cell → bench-level cell.

Reported `mean ± std` are over networks, not over seeds.

## v1 vs v2 statistical comparison

`scalar_dist.md` includes a paired Wilcoxon signed-rank test for every
(clustering, stat). Pairs are the per-net mean values (one pair per
network). On A (n=7) the test can detect p < 0.05; on P (n=2) it cannot.

## Reproducing

From the parent network-generation repo root, with `nwbench` conda
env active:

```bash
# 1. Run the bench (skips already-completed runs by checking
#    comparison.csv presence). Wall ~ 1 hour on i9-12900HK.
bash externals/ec-sbm/scripts/bench/run_bench.sh

# 2. (Optional) Recompute every reference + synth + comparison.csv,
#    keeping summary.csv wall_s intact. Use after compute_*_stats.py
#    or compare_pair.py adds new fields.
bash externals/ec-sbm/scripts/bench/recompute_refs.sh

# 3. Re-render the auto reports without re-running the bench.
python externals/ec-sbm/scripts/bench/aggregate.py \
    --bucket-lo 100000 --bucket-hi 200000 \
    --out externals/ec-sbm/examples/bench/scalar_dist.md
python externals/ec-sbm/scripts/bench/cluster_compare.py
```
