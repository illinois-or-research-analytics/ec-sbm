"""Shared helpers for the EC-SBM bench aggregators in
externals/ec-sbm/scripts/bench/ and externals/ec-sbm/scripts/bench_stack/.
Stat-list constants, file loaders, formatting, and the paired Wilcoxon
test live here so all three aggregators agree on what to read and how
to summarise it.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict


# Stat catalogues shared by every aggregator. Keep in lockstep with
# network_evaluation/network_stats/compute_*_stats.py and
# network_evaluation/compare/compare_pair.py — adding a stat there
# requires extending the right list here.

SCALAR_BOUNDED = [
    "frac_giant_ccomp",
    "deg_assort",
    "global_ccoeff",
    "local_ccoeff",
    "node_coverage",
]

SCALAR_UNBOUNDED = [
    "n_nodes",
    "n_edges",
    "n_concomp",
    "mean_degree",
    "mean_kcore",
    "n_clusters",
    "n_outliers",
    "n_disconnected_clusters",
    "pseudo_diameter",
]

DIST_STATS = [
    "degree",
    "kcore",
    "conductance",
    "edge_density",
    "degree_density",
    "mincut",
    "modularity",
    "mixing_parameter",
    "concomp_sizes",
    "local_ccoeff_nodes",
    "pagerank",
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

# rmse for continuous-valued cluster sequences, mean_l1 for count-valued
# ones (cluster_n_concomp, cluster_pseudo_diameter).
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


def load_comparison(path):
    """Read one comparison.csv into a {(stat, distance_type): value} dict.
    Returns None if the file is missing.
    """
    if not path.exists():
        return None
    out = {}
    with path.open() as f:
        rd = csv.DictReader(f)
        for r in rd:
            try:
                out[(r["stat"], r["distance_type"])] = float(r["distance"])
            except (KeyError, ValueError):
                continue
    return out


def parse_summary_walls(summary_csv, key_cols=("gen", "clustering", "net")):
    """Read the bench summary CSV and return {key_tuple: [wall_s, ...]} for
    rows whose status is ok. The default key_cols suit the v1/v2 bench;
    the stack bench passes ("config", "net").
    """
    walls = defaultdict(list)
    if not summary_csv.exists():
        return walls
    with summary_csv.open() as f:
        rd = csv.DictReader(f)
        for r in rd:
            if r.get("status") != "ok":
                continue
            try:
                wall = float(r["wall_s"])
            except (KeyError, ValueError):
                continue
            try:
                key = tuple(r[c] for c in key_cols)
            except KeyError:
                continue
            walls[key].append(wall)
    return walls


def paired_wilcoxon(values_a, values_b, label_a, label_b):
    """Paired Wilcoxon signed-rank test over two equal-length lists.

    Returns (p_value, n, mean_a, mean_b, winner). winner is `label_a`,
    `label_b`, or "tie". p_value is None when n < 2, every paired
    difference is zero, or scipy is unavailable.
    """
    n = min(len(values_a), len(values_b))
    if n == 0:
        return (None, 0, float("nan"), float("nan"), "—")
    a, b = list(values_a[:n]), list(values_b[:n])
    ma, mb = safe_mean(a), safe_mean(b)
    if ma < mb:
        winner = label_a
    elif mb < ma:
        winner = label_b
    else:
        winner = "tie"
    p = None
    if n >= 2 and any(x != y for x, y in zip(a, b)):
        try:
            from scipy.stats import wilcoxon  # type: ignore
            p = float(wilcoxon(a, b, zero_method="wilcox", alternative="two-sided").pvalue)
        except Exception:
            p = None
    return (p, n, ma, mb, winner)
