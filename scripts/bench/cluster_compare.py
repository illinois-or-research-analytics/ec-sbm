"""Aggregate cluster_* sequence/distribution metrics from every bench
comparison.csv into a focused markdown table.

Cluster_* stats are per-cluster vectors that compare_pair.py emits as
a distribution (EMD over the per-cluster value histogram) and a
sequence (mean_l1, l1, l2, rmse, cosine aligned cluster-by-cluster). The
sequence flavour is the more informative one for ec-sbm because both
generators preserve the reference cluster IDs.
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

OUT_DIR = SUBMODULE_ROOT / "examples" / "bench"
SYNTH_STATS = REPO_ROOT / "data" / "synthetic_networks" / "stats"

GENS = ["ec-sbm-v1", "ec-sbm-v2"]
SEEDS = [1, 2, 3, 4, 5]

CLUST_NAME = {
    "A": "leiden-cpm-0.0001",
    "P": "leiden-cpm-0.0001+cm(piecewise)",
}

NET_INFO = [
    ("douban",        154908,  327162, ["A", "P"]),
    ("wordnet",       146005,  656999, ["A", "P"]),
    ("wiki_users",    138587,  715883, ["A"]),
    ("wiki_link_dyn", 100304,  824968, ["A"]),
    ("lastfm_aminer", 136409, 1685524, ["A"]),
    ("wikiconflict",  116836, 2027871, ["A"]),
    ("livemocha",     104103, 2193083, ["A"]),
]

CLUSTER_STATS = [
    "cluster_deg_assort",
    "cluster_global_ccoeff",
    "cluster_local_ccoeff",
    "cluster_mean_degree",
    "cluster_mean_kcore",
    "cluster_n_concomp",
    "cluster_frac_giant_ccomp",
    "cluster_pseudo_diameter",
]

# mean_l1 for count-valued stats (cluster_n_concomp, cluster_pseudo_diameter):
# integer per-cluster values where the natural reading is "average integer
# gap per cluster" rather than a squared-error penalty.
# rmse for continuous-valued stats bounded in [-1, 1] or [0, 1]: squared
# error highlights per-cluster outlier deviations on top of the mean gap.
SEQ_METRIC = {
    "cluster_deg_assort":       "rmse",
    "cluster_global_ccoeff":    "rmse",
    "cluster_local_ccoeff":     "rmse",
    "cluster_mean_degree":      "rmse",
    "cluster_mean_kcore":       "rmse",
    "cluster_frac_giant_ccomp": "rmse",
    "cluster_n_concomp":        "mean_l1",
    "cluster_pseudo_diameter":  "mean_l1",
}


def safe_mean(xs):
    xs = [x for x in xs if x is not None and not math.isnan(x)]
    return statistics.mean(xs) if xs else float("nan")


def fmt(v, p=4):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if abs(v) >= 1000 or (0 < abs(v) < 1e-3):
        return f"{v:.{p}e}"
    return f"{v:.{p}f}"


def load(gen, clust, net, seed):
    p = SYNTH_STATS / gen / clust / net / f"bench_s{seed}" / "comparison.csv"
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


def collect():
    rows = []
    for net, n_nodes, n_edges, clusts in NET_INFO:
        for c_tag in clusts:
            clust = CLUST_NAME[c_tag]
            for gen in GENS:
                for seed in SEEDS:
                    cmp = load(gen, clust, net, seed)
                    if cmp is None:
                        continue
                    for stat in CLUSTER_STATS:
                        for dt in ("emd", "mean_l1", "rmse"):
                            v = cmp.get((stat, dt))
                            if v is None:
                                continue
                            rows.append(dict(gen=gen, clust=clust, net=net,
                                             n_nodes=n_nodes, n_edges=n_edges,
                                             seed=seed, stat=stat, dt=dt, value=v))
    return rows


def per_net_mean(rows):
    """Stage 1: mean over seeds. {(gen, clust, net, stat, dt): per-net mean}."""
    grp = defaultdict(list)
    for r in rows:
        grp[(r["gen"], r["clust"], r["net"], r["stat"], r["dt"])].append(abs(r["value"]))
    return {k: safe_mean(xs) for k, xs in grp.items()}


def per_bench(per_net):
    """Stage 2: mean / std / min / max over networks per (gen, clust, stat, dt)."""
    grp = defaultdict(list)
    for (gen, clust, net, stat, dt), v in per_net.items():
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        grp[(gen, clust, stat, dt)].append(v)
    out = {}
    for k, xs in grp.items():
        out[k] = dict(mean=safe_mean(xs), std=safe_std(xs),
                      min=min(xs), max=max(xs), n_nets=len(xs))
    return out


def safe_std(xs):
    xs = [x for x in xs if x is not None and not math.isnan(x)]
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def paired_significance(per_net, gen_a, gen_b, clust, stat, dt):
    pairs = defaultdict(dict)
    for (g, c, net, s, d), v in per_net.items():
        if c != clust or s != stat or d != dt or g not in (gen_a, gen_b):
            continue
        pairs[net][g] = v
    a, b = [], []
    for net, gv in pairs.items():
        if gen_a in gv and gen_b in gv:
            a.append(gv[gen_a]); b.append(gv[gen_b])
    n = len(a)
    if n == 0:
        return (None, 0, float("nan"), float("nan"), "—")
    ma, mb = safe_mean(a), safe_mean(b)
    if ma < mb:
        winner = "v1"
    elif mb < ma:
        winner = "v2"
    else:
        winner = "tie"
    p = None
    if n >= 2 and any((x - y) != 0 for x, y in zip(a, b)):
        try:
            from scipy.stats import wilcoxon
            p = float(wilcoxon(a, b, zero_method="wilcox", alternative="two-sided").pvalue)
        except Exception:
            p = None
    return (p, n, ma, mb, winner)


def main():
    rows = collect()
    if not rows:
        raise SystemExit("no comparison rows found")

    pn = per_net_mean(rows)
    pb = per_bench(pn)

    out_md = OUT_DIR / "cluster.md"
    L = []
    L.append("# ec-sbm v1/v2 vs empirical: cluster_* metrics")
    L.append("")
    L.append("Each `cluster_*` metric is a per-cluster vector. compare_pair.py emits")
    L.append("two flavours of distance:")
    L.append("")
    L.append("* **sequence**: aligns cluster-by-cluster. We pick `mean_l1` for count-valued")
    L.append("  stats (`cluster_n_concomp`, `cluster_pseudo_diameter`) where the natural")
    L.append("  reading is the average integer gap per cluster, and `rmse` for")
    L.append("  continuous-valued stats where squared error highlights per-cluster outlier")
    L.append("  deviations on top of the mean gap.")
    L.append("* **distribution**: EMD over the histogram of per-cluster values, no ID alignment.")
    L.append("")
    L.append("Two-stage aggregation: stage 1 averages 5 seeds per network; stage 2")
    L.append("reports mean ± std over networks. Sample sizes: A = 7 nets, P = 2 nets.")
    L.append("")

    cell_keys = sorted({(r["gen"], r["clust"]) for r in rows})

    def stat_table(title, picker):
        L.append(f"## {title}")
        L.append("")
        header = "| stat | metric |" + "".join(f" {g} / {c} |" for (g, c) in cell_keys)
        sep    = "|---|---|" + ":---:|" * len(cell_keys)
        L.append(header)
        L.append(sep)
        for stat in CLUSTER_STATS:
            dt = picker(stat)
            cells = [stat, dt]
            for (g, c) in cell_keys:
                info = pb.get((g, c, stat, dt))
                if info is None:
                    cells.append("—")
                else:
                    cells.append(f"{fmt(info['mean'])} ± {fmt(info['std'])} (n={info['n_nets']})")
            L.append("| " + " | ".join(cells) + " |")
        L.append("")

    stat_table("Sequence (mean_l1 / rmse; 0 = perfect)", lambda s: SEQ_METRIC[s])
    stat_table("EMD distribution (0 = perfect)", lambda s: "emd")

    # Significance
    L.append("## v1 vs v2 — paired Wilcoxon over networks")
    L.append("")
    L.append("Pairs are per-network mean values (one pair per network). `*` p < 0.05, `**` p < 0.01.")
    L.append("")
    L.append("| clustering | stat | metric | v1 mean | v2 mean | winner | p | n |")
    L.append("|---|---|---|---:|---:|:---:|---:|---:|")
    for clust in sorted({c for (_, c) in cell_keys}):
        for stat in CLUSTER_STATS:
            for dt, dt_label in [(SEQ_METRIC[stat], SEQ_METRIC[stat]), ("emd", "EMD")]:
                p, n, ma, mb, winner = paired_significance(pn, "ec-sbm-v1", "ec-sbm-v2", clust, stat, dt)
                if n == 0:
                    continue
                p_cell = "—" if p is None else f"{p:.4g}"
                mark = ""
                if p is not None:
                    if p < 0.01: mark = " **"
                    elif p < 0.05: mark = " *"
                L.append(f"| {clust} | {stat} | {dt_label} | {fmt(ma)} | {fmt(mb)} | {winner}{mark} | {p_cell} | {n} |")
    L.append("")

    # Per-network breakdown
    L.append("## Per-network mean (averaged over seeds)")
    L.append("")
    for net, n_nodes, n_edges, clusts in NET_INFO:
        net_cells = [(g, CLUST_NAME[ct]) for g in GENS for ct in clusts]
        h = "| stat | metric |" + "".join(f" {g} / {c} |" for (g, c) in net_cells)
        s = "|---|---|" + ":---:|" * len(net_cells)
        L.append(f"### {net} (n={n_nodes:,}, m={n_edges:,})")
        L.append("")
        L.append(h)
        L.append(s)
        for stat in CLUSTER_STATS:
            for dt, label in [(SEQ_METRIC[stat], SEQ_METRIC[stat]), ("emd", "EMD")]:
                cells = [stat, label]
                for (g, c) in net_cells:
                    v = pn.get((g, c, net, stat, dt))
                    cells.append(fmt(v) if v is not None else "—")
                L.append("| " + " | ".join(cells) + " |")
        L.append("")

    out_md.write_text("\n".join(L))

    # Also dump tidy CSV for downstream tooling.
    csv_path = out_md.with_suffix(".csv")
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["gen", "clust", "net", "n_nodes", "n_edges", "seed", "stat", "dt", "value"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {out_md} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
