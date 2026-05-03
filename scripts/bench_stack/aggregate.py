"""Aggregate the stack bench (cptg vs stack vs rewire_stack) into a
markdown report with per-bucket tables and paired Wilcoxon tests.

Bucket B0 = 10K-100K nodes (n_nets = 26).
Bucket B1 = 100K-200K nodes (n_nets = 7).

For each (bucket, metric, distance_type):
  1. Per (config, net): mean over 5 seeds → per-net value.
  2. Per (bucket, config): mean ± std over networks.
  3. Paired Wilcoxon, two-sided, on per-net values:
        cptg vs stack
        cptg vs rewire_stack
        stack vs rewire_stack

Inputs:
  ${REPO_ROOT}/data/synthetic_networks/stats/ec-sbm-v2/leiden-cpm-0.0001/<net>/<config>_s<seed>/comparison.csv
  ${SUBMODULE_ROOT}/examples/bench_stack/summary.csv  (config,net,seed,run_id,status,wall_s)

Outputs:
  ${SUBMODULE_ROOT}/examples/bench_stack/report.md
  ${SUBMODULE_ROOT}/examples/bench_stack/per_net.csv  (long-form per (config,net) means)
"""

from __future__ import annotations

import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SUBMODULE_ROOT = SCRIPT_DIR.parents[1]
REPO_ROOT = SUBMODULE_ROOT.parents[1]
sys.path.insert(0, str(SCRIPT_DIR.parent))

OUT_DIR = SUBMODULE_ROOT / "examples" / "bench_stack"
SUMMARY_CSV = OUT_DIR / "summary.csv"
SYNTH_STATS = REPO_ROOT / "data" / "synthetic_networks" / "stats"
GEN = "ec-sbm-v2"
CLUST = "leiden-cpm-0.0001"

CONFIGS = ["cptg", "stack", "rewire_stack"]
SEEDS = [1, 2, 3, 4, 5]

# (net, n_nodes, n_edges, bucket).
NETS = [
    ("sp_infectious",      10972,    44517, "B0"),
    ("wiki_rfa",           11381,   181906, "B0"),
    ("dblp_cite",          12590,    49636, "B0"),
    ("anybeat",            12645,    49132, "B0"),
    ("chicago_road",       12979,    20627, "B0"),
    ("foldoc",             13356,    91471, "B0"),
    ("inploid",            14629,    49485, "B0"),
    ("google",             15763,   148585, "B0"),
    ("marvel_universe",    19251,    95497, "B0"),
    ("fly_hemibrain",      21739,  2897925, "B0"),
    ("internet_as",        22963,    48436, "B0"),
    ("word_assoc",         23132,   297094, "B0"),
    ("cora",               23166,    89157, "B0"),
    ("lkml_reply",         26885,   159996, "B0"),
    ("linux",              30834,   213217, "B0"),
    ("topology",           34761,   107720, "B0"),
    ("email_enron",        36692,   183831, "B0"),
    ("pgp_strong",         39796,   197150, "B0"),
    ("facebook_wall",      45813,   183412, "B0"),
    ("slashdot_threads",   51083,   116573, "B0"),
    ("python_dependency",  58739,   108093, "B0"),
    ("marker_cafe",        69413,  1644843, "B0"),
    ("epinions_trust",     75879,   405740, "B0"),
    ("slashdot_zoo",       79116,   467731, "B0"),
    ("twitter_15m",        85712,  4708274, "B0"),
    ("prosper",            89269,  3330022, "B0"),
    ("douban",            154908,   327162, "B1"),
    ("wordnet",           146005,   656999, "B1"),
    ("wiki_users",        138587,   715883, "B1"),
    ("wiki_link_dyn",     100304,   824968, "B1"),
    ("lastfm_aminer",     136409,  1685524, "B1"),
    ("wikiconflict",      116836,  2027871, "B1"),
    ("livemocha",         104103,  2193083, "B1"),
]

SCALAR_BOUNDED = ["frac_giant_ccomp", "deg_assort", "global_ccoeff",
                   "local_ccoeff", "node_coverage"]
SCALAR_UNBOUNDED = ["n_nodes", "n_edges", "n_concomp", "mean_degree",
                     "mean_kcore", "n_clusters", "n_outliers",
                     "n_disconnected_clusters", "pseudo_diameter"]
DIST_STATS = ["degree", "kcore", "conductance", "edge_density",
              "degree_density", "mincut", "modularity",
              "mixing_parameter", "concomp_sizes",
              "local_ccoeff_nodes", "pagerank"]
CLUSTER_STATS = ["cluster_deg_assort", "cluster_global_ccoeff",
                  "cluster_local_ccoeff", "cluster_mean_degree",
                  "cluster_mean_kcore", "cluster_n_concomp",
                  "cluster_frac_giant_ccomp", "cluster_pseudo_diameter"]
CLUSTER_SEQ_METRIC = {
    "cluster_deg_assort":        "rmse",
    "cluster_global_ccoeff":     "rmse",
    "cluster_local_ccoeff":      "rmse",
    "cluster_mean_degree":       "rmse",
    "cluster_mean_kcore":        "rmse",
    "cluster_frac_giant_ccomp":  "rmse",
    "cluster_n_concomp":         "mean_l1",
    "cluster_pseudo_diameter":   "mean_l1",
}


def safe_mean(xs):
    xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return statistics.mean(xs) if xs else float("nan")


def safe_std(xs):
    xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def fmt(v, p=4):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if abs(v) >= 1000 or (0 < abs(v) < 1e-3):
        return f"{v:.{p}e}"
    return f"{v:.{p}f}"


def load_comp(config, net, seed):
    p = SYNTH_STATS / GEN / CLUST / net / f"{config}_s{seed}" / "comparison.csv"
    if not p.exists():
        return None
    out = {}
    with p.open() as f:
        rd = csv.DictReader(f)
        for r in rd:
            try:
                out[(r["stat"], r["distance_type"])] = float(r["distance"])
            except (KeyError, ValueError):
                continue
    return out


def parse_walls():
    walls = defaultdict(list)
    if not SUMMARY_CSV.exists():
        return walls
    with SUMMARY_CSV.open() as f:
        rd = csv.DictReader(f)
        for r in rd:
            if r["status"] != "ok":
                continue
            try:
                walls[(r["config"], r["net"])].append(float(r["wall_s"]))
            except (KeyError, ValueError):
                continue
    return walls


def collect():
    """Returns per_net[(config, net, stat, dt)] = mean over seeds."""
    stat_dt_pairs = (
        [(s, "abs_diff") for s in SCALAR_BOUNDED]
        + [(s, "rel_diff") for s in SCALAR_UNBOUNDED]
        + [(s, "emd") for s in DIST_STATS]
        + [(s, CLUSTER_SEQ_METRIC[s]) for s in CLUSTER_STATS]
        + [(s, "emd") for s in CLUSTER_STATS]
    )
    accum = defaultdict(list)
    for cfg in CONFIGS:
        for net, _, _, _ in NETS:
            for seed in SEEDS:
                cmp = load_comp(cfg, net, seed)
                if cmp is None:
                    continue
                for stat, dt in stat_dt_pairs:
                    v = cmp.get((stat, dt))
                    if v is not None:
                        accum[(cfg, net, stat, dt)].append(abs(v))
    return {k: safe_mean(xs) for k, xs in accum.items()}


def paired_wilcoxon(per_net, cfg_a, cfg_b, bucket, stat, dt):
    a, b = [], []
    for net, _, _, b_tag in NETS:
        if b_tag != bucket:
            continue
        va = per_net.get((cfg_a, net, stat, dt))
        vb = per_net.get((cfg_b, net, stat, dt))
        if va is None or vb is None:
            continue
        a.append(va); b.append(vb)
    n = len(a)
    if n == 0:
        return (None, 0, float("nan"), float("nan"), "—")
    ma, mb = safe_mean(a), safe_mean(b)
    if ma < mb: winner = cfg_a
    elif mb < ma: winner = cfg_b
    else: winner = "tie"
    p = None
    if n >= 2 and any((x - y) != 0 for x, y in zip(a, b)):
        try:
            from scipy.stats import wilcoxon
            p = float(wilcoxon(a, b, zero_method="wilcox", alternative="two-sided").pvalue)
        except Exception:
            p = None
    return (p, n, ma, mb, winner)


def render():
    per_net = collect()
    walls = parse_walls()

    # Wall time per (bucket, config) over networks.
    wall_per_net = {}
    for (cfg, net), ws in walls.items():
        wall_per_net[(cfg, net)] = safe_mean(ws)

    L = []
    L.append("# ec-sbm-v2: cluster_preserving_true_greedy vs stacked variants")
    L.append("")
    L.append("Question: does plain `true_greedy` cleanup after")
    L.append("`cluster_preserving_true_greedy` recover stuck stubs without")
    L.append("regressing other stats? Does prepending `cluster_preserving_rewire`")
    L.append("help further? Does the answer change with bucket size?")
    L.append("")
    L.append("Three matcher configurations, all on EC-SBM v2 with")
    L.append("`leiden-cpm-0.0001` reference clustering, 5 seeds per network:")
    L.append("")
    L.append("| config | matcher stack |")
    L.append("|---|---|")
    L.append("| `cptg` | `cluster_preserving_true_greedy` (current v2 default) |")
    L.append("| `stack` | `cluster_preserving_true_greedy, true_greedy` |")
    L.append("| `rewire_stack` | `cluster_preserving_rewire, cluster_preserving_true_greedy, true_greedy` |")
    L.append("")
    L.append("Buckets: **B0** = 10K–100K nodes (26 networks), **B1** = 100K–200K nodes")
    L.append("(7 networks). Aggregation is two-stage: stage 1 means over 5 seeds per")
    L.append("network; stage 2 means or paired Wilcoxon over the networks in the bucket.")
    L.append("Reported `n` is the number of networks. Wilcoxon p-value is two-sided;")
    L.append("`*` = p < 0.05, `**` = p < 0.01.")
    L.append("")
    L.append("`SAD = |synth − ref|` (bounded scalars). `SRD = |synth − ref| / |synth|` (unbounded scalars).")
    L.append("`EMD` = Earth Mover's distance over synth/ref histograms; 0 = perfect.")
    L.append("`cluster_*`: rmse for continuous-valued stats, mean_l1 for count-valued ones; 0 = perfect.")
    L.append("")

    for bucket_label, bucket in [("B0 — 10K–100K nodes (n_nets = 26)", "B0"),
                                  ("B1 — 100K–200K nodes (n_nets = 7)", "B1")]:
        L.append(f"## {bucket_label}")
        L.append("")
        L.append("### Wall time (s)")
        L.append("")
        L.append("| config | mean | std | min | max | n_nets |")
        L.append("|---|---:|---:|---:|---:|---:|")
        for cfg in CONFIGS:
            ws = [wall_per_net[(cfg, net)] for net, _, _, b_tag in NETS
                  if b_tag == bucket and (cfg, net) in wall_per_net]
            if not ws:
                continue
            L.append(f"| {cfg} | {fmt(safe_mean(ws), 1)} | {fmt(safe_std(ws), 1)} | "
                     f"{fmt(min(ws), 1)} | {fmt(max(ws), 1)} | {len(ws)} |")
        L.append("")

        # Per-config means table for every metric.
        def metric_rows(label_metric_pairs, header):
            L.append(f"### {header}")
            L.append("")
            cols = "| stat | metric |" + "".join(f" {c} |" for c in CONFIGS)
            sep  = "|---|---|" + ":---:|" * len(CONFIGS)
            L.append(cols)
            L.append(sep)
            for stat, dt, label in label_metric_pairs:
                cells = [stat, label]
                for cfg in CONFIGS:
                    vals = [per_net.get((cfg, net, stat, dt)) for net, _, _, b_tag in NETS if b_tag == bucket]
                    vals = [v for v in vals if v is not None]
                    if not vals:
                        cells.append("—")
                    else:
                        cells.append(f"{fmt(safe_mean(vals))} ± {fmt(safe_std(vals))} (n={len(vals)})")
                L.append("| " + " | ".join(cells) + " |")
            L.append("")

        scalar_bounded_pairs = [(s, "abs_diff", "SAD") for s in SCALAR_BOUNDED]
        scalar_unbounded_pairs = [(s, "rel_diff", "SRD") for s in SCALAR_UNBOUNDED]
        dist_pairs = [(s, "emd", "EMD") for s in DIST_STATS]
        cluster_seq_pairs = [(s, CLUSTER_SEQ_METRIC[s], CLUSTER_SEQ_METRIC[s]) for s in CLUSTER_STATS]
        cluster_emd_pairs = [(s, "emd", "EMD") for s in CLUSTER_STATS]

        metric_rows(scalar_bounded_pairs,   "Scalar SAD (bounded)")
        metric_rows(scalar_unbounded_pairs, "Scalar SRD (unbounded)")
        metric_rows(dist_pairs,             "Distributional EMD")
        metric_rows(cluster_seq_pairs,      "cluster_* sequence (rmse / mean_l1)")
        metric_rows(cluster_emd_pairs,      "cluster_* distribution EMD")

        # Paired Wilcoxon: cptg vs stack, cptg vs rewire_stack, stack vs rewire_stack.
        L.append("### Paired Wilcoxon over networks")
        L.append("")
        L.append("Three pairwise tests per metric. Winner = config with lower mean")
        L.append("distance. `*` = p < 0.05, `**` = p < 0.01.")
        L.append("")
        all_pairs = (
            [(s, "abs_diff", "SAD") for s in SCALAR_BOUNDED]
            + [(s, "rel_diff", "SRD") for s in SCALAR_UNBOUNDED]
            + [(s, "emd", "EMD") for s in DIST_STATS]
            + [(s, CLUSTER_SEQ_METRIC[s], CLUSTER_SEQ_METRIC[s]) for s in CLUSTER_STATS]
            + [(s, "emd", "EMD-clu") for s in CLUSTER_STATS]
        )
        L.append("| stat | metric | cptg vs stack | cptg vs rewire_stack | stack vs rewire_stack |")
        L.append("|---|---|---|---|---|")
        for stat, dt, label in all_pairs:
            cells = [stat, label]
            for cfg_a, cfg_b in [("cptg", "stack"), ("cptg", "rewire_stack"), ("stack", "rewire_stack")]:
                p, n, ma, mb, winner = paired_wilcoxon(per_net, cfg_a, cfg_b, bucket, stat, dt)
                if n == 0:
                    cells.append("—")
                    continue
                p_cell = "—" if p is None else f"{p:.3g}"
                mark = ""
                if p is not None:
                    if p < 0.01: mark = " **"
                    elif p < 0.05: mark = " *"
                cells.append(f"{winner}{mark} (p={p_cell}, n={n})")
            L.append("| " + " | ".join(cells) + " |")
        L.append("")

    # Write per-net long-form CSV alongside.
    csv_path = OUT_DIR / "per_net.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["config", "net", "n_nodes", "n_edges", "bucket", "stat", "dist_type", "value"])
        for (cfg, net, stat, dt), v in per_net.items():
            row = next(((nn, ne, b) for n, nn, ne, b in NETS if n == net), (None, None, None))
            w.writerow([cfg, net, *row, stat, dt, v])

    out_md = OUT_DIR / "report.md"
    out_md.write_text("\n".join(L))
    print(f"wrote {out_md} + {csv_path}")


if __name__ == "__main__":
    render()
