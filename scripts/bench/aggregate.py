"""Aggregate ec-sbm bench comparison.csv across (gen, clustering, net, seed)
into a per-bucket markdown report. Bucket = 100K-node bin selected by
--bucket-lo / --bucket-hi (lo inclusive, hi exclusive).

Aggregation is two-stage:
  1. Per (gen, clustering, net): mean over the 5 seeds gives the
     network-level value.
  2. Per (gen, clustering): mean / std / min / max across the networks
     in the bucket gives the bench-level cell.

Scalar stats are reported as SAD (|synth - ref|) for bounded stats and
SRD (|synth - ref| / |synth|) for unbounded stats. Distributional stats
use EMD. Wall time is also two-stage (per-net mean over seeds, then
mean/std over nets).

Per-run inputs:
  ${REPO_ROOT}/data/synthetic_networks/stats/<gen>/<clustering>/<net>/bench_s<seed>/comparison.csv
  ${SUBMODULE_ROOT}/examples/bench/summary.csv

Outputs:
  - <out_md>: human-readable markdown report
  - <out_md>.csv: tidy long-form table for downstream tooling
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SUBMODULE_ROOT = SCRIPT_DIR.parents[1]
REPO_ROOT = SUBMODULE_ROOT.parents[1]
sys.path.insert(0, str(SCRIPT_DIR.parent))

from bench_common import (  # noqa: E402
    SCALAR_BOUNDED, SCALAR_UNBOUNDED, DIST_STATS,
    safe_mean, safe_std, fmt, load_comparison, parse_summary_walls,
    paired_wilcoxon,
)

SUMMARY_CSV = SUBMODULE_ROOT / "examples" / "bench" / "summary.csv"
SYNTH_STATS = REPO_ROOT / "data" / "synthetic_networks" / "stats"

NET_INFO = [
    ("douban",        154908,  327162, ["A", "P"]),
    ("wordnet",       146005,  656999, ["A", "P"]),
    ("wiki_users",    138587,  715883, ["A"]),
    ("wiki_link_dyn", 100304,  824968, ["A"]),
    ("lastfm_aminer", 136409, 1685524, ["A"]),
    ("wikiconflict",  116836, 2027871, ["A"]),
    ("livemocha",     104103, 2193083, ["A"]),
]

CLUST_NAME = {
    "A": "leiden-cpm-0.0001",
    "P": "leiden-cpm-0.0001+cm(piecewise)",
}

GENS = ["ec-sbm-v1", "ec-sbm-v2"]
SEEDS = [1, 2, 3, 4, 5]

# Scalars use SAD (abs_diff) when bounded, SRD (rel_diff) when unbounded.
SCALAR_STATS_BOUNDED = SCALAR_BOUNDED
SCALAR_STATS_UNBOUNDED = SCALAR_UNBOUNDED
SCALAR_STATS = SCALAR_STATS_BOUNDED + SCALAR_STATS_UNBOUNDED


def scalar_metric(stat):
    return ("abs_diff", "SAD") if stat in SCALAR_STATS_BOUNDED else ("rel_diff", "SRD")


def _comparison_path(gen, clust, net, seed):
    return SYNTH_STATS / gen / clust / net / f"bench_s{seed}" / "comparison.csv"


def collect_bucket(lo, hi):
    """For each (gen, clustering, net, seed) in the bucket, return the per-seed
    distance values. Also return the bucket NET_INFO for header rendering.
    """
    nets_in_bucket = [(name, nn, ne, clusts)
                      for (name, nn, ne, clusts) in NET_INFO
                      if lo <= nn < hi]
    rows = []  # (gen, clust, net, seed, stat, dt, value)
    for net, n_nodes, n_edges, clusts in nets_in_bucket:
        for c_tag in clusts:
            clust = CLUST_NAME[c_tag]
            for gen in GENS:
                for seed in SEEDS:
                    cmp = load_comparison(_comparison_path(gen, clust, net, seed))
                    if cmp is None:
                        continue
                    for stat in SCALAR_STATS:
                        for dt in ("abs_diff", "rel_diff"):
                            v = cmp.get((stat, dt))
                            if v is None:
                                continue
                            rows.append(dict(gen=gen, clustering=clust, net=net,
                                             n_nodes=n_nodes, n_edges=n_edges,
                                             seed=seed, stat=stat, dist_type=dt, value=v))
                    for stat in DIST_STATS:
                        v = cmp.get((stat, "emd"))
                        if v is None:
                            continue
                        rows.append(dict(gen=gen, clustering=clust, net=net,
                                         n_nodes=n_nodes, n_edges=n_edges,
                                         seed=seed, stat=stat, dist_type="emd", value=v))
    return nets_in_bucket, rows


def per_net_mean(rows):
    """Stage 1: mean over seeds, magnitude only.
    Returns {(gen, clust, net, stat, dt): per-net mean of |value|}.
    """
    grp = defaultdict(list)
    for r in rows:
        if r["value"] is None:
            continue
        grp[(r["gen"], r["clustering"], r["net"], r["stat"], r["dist_type"])].append(abs(r["value"]))
    return {k: safe_mean(xs) for k, xs in grp.items()}


def per_bench(per_net):
    """Stage 2: mean/std/min/max over networks per (gen, clust, stat, dt)."""
    grp = defaultdict(list)
    for (gen, clust, net, stat, dt), v in per_net.items():
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        grp[(gen, clust, stat, dt)].append(v)
    out = {}
    for k, xs in grp.items():
        out[k] = dict(mean=safe_mean(xs), std=safe_std(xs),
                      min=min(xs) if xs else float("nan"),
                      max=max(xs) if xs else float("nan"),
                      n_nets=len(xs))
    return out


def paired_significance(per_net, gen_a, gen_b, clust, stat, dt):
    """Paired Wilcoxon signed-rank test on per-net distances for v1 vs v2.
    Returns (p_value, n_pairs, mean_a, mean_b, winner) where winner is
    'A' if mean_a < mean_b, 'B' if mean_b < mean_a, 'tie' if equal.
    p_value is None if scipy is missing or n_pairs < 2 or all diffs are
    zero (paired test undefined).
    """
    pairs = []
    for (g, c, net, s, d), v in per_net.items():
        if c != clust or s != stat or d != dt:
            continue
        if g not in (gen_a, gen_b):
            continue
        pairs.append((net, g, v))
    by_net = defaultdict(dict)
    for net, g, v in pairs:
        by_net[net][g] = v
    a_vals, b_vals = [], []
    for net, gv in by_net.items():
        if gen_a in gv and gen_b in gv:
            a_vals.append(gv[gen_a])
            b_vals.append(gv[gen_b])
    n = len(a_vals)
    if n == 0:
        return (None, 0, float("nan"), float("nan"), "—")
    mean_a, mean_b = safe_mean(a_vals), safe_mean(b_vals)
    if mean_a < mean_b:
        winner = "v1"
    elif mean_b < mean_a:
        winner = "v2"
    else:
        winner = "tie"
    p = None
    diffs = [a - b for a, b in zip(a_vals, b_vals)]
    if n >= 2 and any(d != 0 for d in diffs):
        try:
            from scipy.stats import wilcoxon  # type: ignore
            res = wilcoxon(a_vals, b_vals, zero_method="wilcox", alternative="two-sided")
            p = float(res.pvalue)
        except Exception:
            p = None
    return (p, n, mean_a, mean_b, winner)


def fmt(v, p=4):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if abs(v) >= 1000 or (0 < abs(v) < 1e-3):
        return f"{v:.{p}e}"
    return f"{v:.{p}f}"


def write_report(lo, hi, nets, rows, out_md):
    pn = per_net_mean(rows)
    pb = per_bench(pn)

    # walls: per-net mean of (gen, clust, net) -> mean/std over nets
    walls_pn = {}
    walls_raw = parse_summary_walls(SUMMARY_CSV, key_cols=("gen", "clustering", "net"))
    for (gen, clust, net), ws in walls_raw.items():
        # only nets actually in this bucket
        if not any(n[0] == net for n in nets):
            continue
        walls_pn[(gen, clust, net)] = safe_mean(ws)
    walls_pb = defaultdict(list)
    for (gen, clust, net), m in walls_pn.items():
        walls_pb[(gen, clust)].append(m)

    cluster_set = sorted({r["clustering"] for r in rows})

    lines = []
    lines.append(f"# Bucket {lo:,}-{hi:,} nodes — ec-sbm v1/v2 vs empirical")
    lines.append("")
    if not nets:
        lines.append("_No networks in this bucket._")
    else:
        lines.append("**Networks:** " + ", ".join(
            f"{n} (n={nn:,}, m={ne:,})" for n, nn, ne, _ in sorted(nets, key=lambda x: x[1])
        ))
    lines.append("")
    lines.append("Two-stage aggregation: stage 1 averages 5 seeds per network;")
    lines.append("stage 2 averages networks within each (gen, clustering) cell.")
    lines.append("Reported mean/std are over networks, not over seeds.")
    lines.append("")
    lines.append("`SAD` = |synth − ref| (bounded scalars). `SRD` = |synth − ref| / |synth| (unbounded scalars).")
    lines.append("`emd` = Earth Mover's distance over synth/ref histograms; 0 = perfect match.")
    lines.append("")

    # Wall time table
    lines.append("## Wall time (s)")
    lines.append("")
    lines.append("| gen | clustering | mean | std | min | max | n_nets |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for clust in cluster_set:
        for gen in GENS:
            ws = walls_pb.get((gen, clust), [])
            if not ws:
                continue
            lines.append(
                f"| {gen} | {clust} | {fmt(safe_mean(ws), 1)} | {fmt(safe_std(ws), 1)} | "
                f"{fmt(min(ws), 1)} | {fmt(max(ws), 1)} | {len(ws)} |"
            )
    lines.append("")

    # Scalar table
    def scalar_section(title, stats):
        lines.append(f"## {title}")
        lines.append("")
        header = "| stat | metric |" + "".join(f" {gen} / {c} |" for c in cluster_set for gen in GENS)
        sep    = "|---|---|" + ":---:|" * (len(cluster_set) * len(GENS))
        lines.append(header)
        lines.append(sep)
        for stat in stats:
            dt, label = scalar_metric(stat)
            cells = [stat, label]
            for c in cluster_set:
                for gen in GENS:
                    info = pb.get((gen, c, stat, dt))
                    if info is None:
                        cells.append("—")
                    else:
                        cells.append(f"{fmt(info['mean'])} ± {fmt(info['std'])} (n={info['n_nets']})")
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")

    scalar_section("Scalar stats — SAD (bounded)", SCALAR_STATS_BOUNDED)
    scalar_section("Scalar stats — SRD (unbounded)", SCALAR_STATS_UNBOUNDED)

    # Distribution table (EMD)
    lines.append("## Distributional stats — EMD")
    lines.append("")
    header = "| stat |" + "".join(f" {gen} / {c} |" for c in cluster_set for gen in GENS)
    sep    = "|---|" + ":---:|" * (len(cluster_set) * len(GENS))
    lines.append(header)
    lines.append(sep)
    for stat in DIST_STATS:
        cells = [stat]
        for c in cluster_set:
            for gen in GENS:
                info = pb.get((gen, c, stat, "emd"))
                if info is None:
                    cells.append("—")
                else:
                    cells.append(f"{fmt(info['mean'])} ± {fmt(info['std'])} (n={info['n_nets']})")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    # Per-network table (the per-net mean over seeds)
    lines.append("## Per-network mean (averaged over seeds)")
    lines.append("")
    by_net = defaultdict(list)
    for r in rows:
        by_net[r["net"]].append(r)
    for net in sorted(by_net.keys(), key=lambda n: next((x[1] for x in nets if x[0] == n), 0)):
        sub = by_net[net]
        n_nodes = next((r["n_nodes"] for r in sub), "?")
        n_edges = next((r["n_edges"] for r in sub), "?")
        lines.append(f"### {net} (n={n_nodes:,}, m={n_edges:,})")
        lines.append("")
        net_clusts = sorted({r["clustering"] for r in sub})
        h = "| stat | metric |" + "".join(f" {gen} / {c} |" for c in net_clusts for gen in GENS)
        s2 = "|---|---|" + ":---:|" * (len(net_clusts) * len(GENS))
        lines.append(h)
        lines.append(s2)
        for stat, label_dt in (
            [(s, ("abs_diff", "SAD")) for s in SCALAR_STATS_BOUNDED]
            + [(s, ("rel_diff", "SRD")) for s in SCALAR_STATS_UNBOUNDED]
            + [(s, ("emd", "EMD"))     for s in DIST_STATS]
        ):
            dt, label = label_dt
            cells = [stat, label]
            for c in net_clusts:
                for gen in GENS:
                    v = pn.get((gen, c, net, stat, dt))
                    cells.append(fmt(v) if v is not None else "—")
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")

    # Significance: paired Wilcoxon, v1 vs v2, per (clustering, stat, dt).
    lines.append("## v1 vs v2 — paired Wilcoxon over networks")
    lines.append("")
    lines.append("Paired Wilcoxon signed-rank on per-net mean distances (n = number of")
    lines.append("networks where both v1 and v2 ran). `winner` = gen with lower mean")
    lines.append("distance. `p` = two-sided p-value; n=2 has no p-value (no scipy fallback).")
    lines.append("Be careful with low n — bench has 7 nets on A, 2 on P, so P-clustering")
    lines.append("results never reach conventional significance.")
    lines.append("")
    sig_rows = []
    for clust in cluster_set:
        for stat in SCALAR_STATS_BOUNDED:
            sig_rows.append((clust, stat, "abs_diff", "SAD"))
        for stat in SCALAR_STATS_UNBOUNDED:
            sig_rows.append((clust, stat, "rel_diff", "SRD"))
        for stat in DIST_STATS:
            sig_rows.append((clust, stat, "emd", "EMD"))
    lines.append("| clustering | stat | metric | v1 mean | v2 mean | winner | p | n |")
    lines.append("|---|---|---|---:|---:|:---:|---:|---:|")
    for clust, stat, dt, label in sig_rows:
        p, n, m_a, m_b, winner = paired_significance(pn, "ec-sbm-v1", "ec-sbm-v2", clust, stat, dt)
        if n == 0:
            continue
        p_cell = "—" if p is None else f"{p:.4g}"
        sig_mark = ""
        if p is not None:
            if p < 0.01:
                sig_mark = " **"
            elif p < 0.05:
                sig_mark = " *"
        lines.append(
            f"| {clust} | {stat} | {label} | {fmt(m_a)} | {fmt(m_b)} | {winner}{sig_mark} | {p_cell} | {n} |"
        )
    lines.append("")
    lines.append("`*` = p < 0.05, `**` = p < 0.01.")
    lines.append("")

    out_md.write_text("\n".join(lines))

    csv_path = out_md.with_suffix(".csv")
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["gen", "clustering", "net", "n_nodes", "n_edges", "seed",
                                          "stat", "dist_type", "value"])
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket-lo", type=int, required=True)
    ap.add_argument("--bucket-hi", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    nets, rows = collect_bucket(args.bucket_lo, args.bucket_hi)
    write_report(args.bucket_lo, args.bucket_hi, nets, rows, args.out)
    print(f"wrote {args.out} ({len(rows)} rows, {len(nets)} nets)")


if __name__ == "__main__":
    main()
