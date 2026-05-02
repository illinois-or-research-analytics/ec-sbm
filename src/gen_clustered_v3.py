"""Stage 2 (v3): per-cluster PSO subgraph with clustering-coefficient-matching
T search.

For each cluster the script samples a PSO graph (uniform angular
distribution, ``m == k_cluster``) and runs a 1-D bisection / secant
search over the temperature ``T`` to drive the simulated cluster's
global clustering coefficient toward the empirical target. Smaller T
yields higher clustering, so f(T) = ccoeff(T) - target is decreasing in
T; bracketing on [t_min, t_max] always converges (subject to iter cap).

By construction PSO is k-edge-connected when ``m == k`` (the first k+1
nodes form a complete K_{k+1}, every later node attaches to k existing
nodes), so v3 preserves the per-cluster mincut guarantee that motivated
v1's constructive core. Unlike v1 / v2's "constructive K_{k+1} + greedy
attach", PSO injects controllable structure: gamma shapes the in-cluster
degree distribution, T shapes triangle density.

Inputs (in addition to v2's profile artifacts): the empirical edgelist
and clustering, used to compute the per-cluster target clustering
coefficient on the cluster's induced subgraph.

Output: an ``edge.csv`` containing only the band ``clustered_pso_core``
plus a ``sources.json`` and a per-cluster ``pso_search_log.json``.
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from gen_kec_core import load_inputs
from gen_pso_core import pso_cluster_edges, induced_global_ccoeff
from graph_utils import normalize_edge
from params_common import _parse_bool, read_params, resolve_param
from pipeline_common import standard_setup, timed


DEFAULT_PSO_GAMMA = 3.0
DEFAULT_PSO_M_POLICY = "auto"
DEFAULT_PSO_M_FLOOR = 1
DEFAULT_SEARCH_MAX_ITERS = 30
DEFAULT_SEARCH_DIFF_TOL = 0.01
DEFAULT_SEARCH_STEP_TOL = 1e-4
DEFAULT_SEARCH_T_MIN = 0.01
DEFAULT_SEARCH_T_MAX = 0.99
DEFAULT_INITIAL_T = 0.5
PSO_SEARCH_LOG_NAME = "pso_search_log.json"


def _next_T(min_T, max_T, f_min_T, f_max_T):
    """Bisection by default; secant when both endpoint residuals are known
    and have opposite signs. Same heuristic as src/npso/gen.py."""
    mid = min_T + (max_T - min_T) / 2.0
    if f_min_T is None or f_max_T is None:
        return mid
    if f_min_T * f_max_T > 0:
        return mid
    denom = f_max_T - f_min_T
    if denom == 0:
        return mid
    T_sec = min_T - f_min_T * (max_T - min_T) / denom
    margin = 0.05 * (max_T - min_T)
    if T_sec <= min_T + margin or T_sec >= max_T - margin:
        return mid
    return T_sec


def _empirical_intra_cluster_stats(orig_edgelist_path, orig_clustering_path):
    """Per-cluster intra-cluster stats: clustering coefficient, mean
    degree, and node count, all computed on the empirical intra-cluster
    induced subgraph.

    Returns ``{cluster_id_str: {"ccoeff": f, "mean_deg": f, "n": int}}``.

    Edges with at least one endpoint outside the clustering are skipped;
    inter-cluster edges are skipped. Singleton clusters and clusters with
    < 3 nodes get ccoeff=0.0; mean_deg is still defined (0 if cluster is
    isolated, otherwise sum_of_intra_degree / n).
    """
    df_clust = pd.read_csv(orig_clustering_path, dtype=str).dropna()
    node2c = dict(zip(df_clust["node_id"], df_clust["cluster_id"]))
    cluster_nodes = defaultdict(set)
    for n, c in node2c.items():
        cluster_nodes[c].add(n)

    df_edge = pd.read_csv(orig_edgelist_path, dtype=str).dropna()

    intra_adj = defaultdict(lambda: defaultdict(set))
    for u, v in zip(df_edge["source"], df_edge["target"]):
        if u == v:
            continue
        cu = node2c.get(u)
        cv = node2c.get(v)
        if cu is None or cv is None or cu != cv:
            continue
        intra_adj[cu][u].add(v)
        intra_adj[cu][v].add(u)

    out = {}
    for c, nodes in cluster_nodes.items():
        adj = intra_adj.get(c, {})
        n_c = len(nodes)
        sum_deg = sum(len(adj.get(u, ())) for u in nodes)
        mean_deg = (sum_deg / n_c) if n_c > 0 else 0.0
        if n_c < 3:
            out[c] = {"ccoeff": 0.0, "mean_deg": mean_deg, "n": n_c}
            continue
        triplets = 0
        for u in nodes:
            d = len(adj.get(u, ()))
            triplets += d * (d - 1) // 2
        if triplets == 0:
            out[c] = {"ccoeff": 0.0, "mean_deg": mean_deg, "n": n_c}
            continue
        triangles = 0
        for u, nbrs_u in adj.items():
            for v in nbrs_u:
                if v <= u:
                    continue
                common = adj.get(v, set()) & nbrs_u
                for w in common:
                    if w > v:
                        triangles += 1
        out[c] = {
            "ccoeff": 3.0 * triangles / triplets,
            "mean_deg": mean_deg,
            "n": n_c,
        }
    return out


def _read_cluster_id_to_str(cluster_id_path):
    """Profile's ``cluster_id.csv`` is one cluster_id per line, in iid
    order. Returns ``[str, ...]`` indexed by cluster iid."""
    return pd.read_csv(cluster_id_path, header=None, dtype=str)[0].tolist()


def _resolve_m(k, n, m_policy, m_floor, empirical_mean_deg):
    """Compute the per-cluster PSO m parameter.

    Policies:
      - ``floor``: ``m = max(k, m_floor)`` (knob-only).
      - ``auto``: ``m = max(k, m_floor, round(empirical_mean_deg / 2))``.
        This matches PSO's "m = half average degree" semantic when the
        cluster's empirical density says so, while still preserving
        ``m >= k`` so the construction stays k-edge-connected.

    Result is capped at ``n - 1``.
    """
    base = max(int(k), int(m_floor))
    if m_policy == "auto":
        base = max(base, int(round(empirical_mean_deg / 2.0)))
    elif m_policy == "floor":
        pass
    else:
        raise ValueError(f"unknown pso_m_policy: {m_policy!r}")
    return min(base, n - 1)


def _search_T_for_cluster(
    cluster_nodes_iid, k, gamma, target_ccoeff, base_seed,
    max_iters, diff_tol, step_tol, t_min, t_max, initial_T,
    m_policy, m_floor, empirical_mean_deg,
):
    """Bisection / secant over T for a single cluster.

    Returns ``(best_T, best_ccoeff, best_edges_local, iter_records, m)``
    where ``best_edges_local`` is the PSO edgelist on local 0..n-1 ids.

    ``m`` is resolved by ``_resolve_m`` from ``k`` (mincut), the
    empirical mean intra-cluster degree, the policy and floor flags;
    ``m >= k`` is always enforced so the cluster stays k-edge-connected.

    Short-circuits when the cluster is small enough that PSO produces a
    deterministic complete graph (``n <= m + 1``).
    """
    n = len(cluster_nodes_iid)
    if n <= 1 or k <= 0:
        return None, 0.0, [], [], 0
    m = _resolve_m(k, n, m_policy, m_floor, empirical_mean_deg)
    if m < 1:
        m = 1
    # Deterministic complete-graph regime: T does not affect output.
    if n <= m + 1:
        edges_local = pso_cluster_edges(n, m, initial_T, gamma, base_seed)
        cc = induced_global_ccoeff(n, edges_local)
        return (
            initial_T, cc, edges_local,
            [{"T": initial_T, "ccoeff": cc, "note": "complete_graph"}],
            m,
        )

    # Pin endpoints to widen the bracket if the empirical target sits at
    # one extreme; then iterate.
    iter_records = []
    f_min, f_max = None, None
    best_T = None
    best_cc = None
    best_diff = None
    best_edges = None
    prev_cc = None

    cur_min, cur_max = t_min, t_max
    for it in range(max_iters):
        T = _next_T(cur_min, cur_max, f_min, f_max)
        # Re-seed per iter so different T gets a different draw but same
        # T re-runs deterministically.
        seed_iter = (base_seed * 1_000_003 + it) & 0xFFFFFFFF
        edges_local = pso_cluster_edges(n, m, T, gamma, seed_iter)
        cc = induced_global_ccoeff(n, edges_local)
        diff = abs(cc - target_ccoeff)
        iter_records.append({"T": T, "ccoeff": cc, "diff": diff})

        if best_cc is None or diff < best_diff:
            best_T, best_cc, best_diff = T, cc, diff
            best_edges = edges_local

        if best_diff < diff_tol:
            break
        if prev_cc is not None and abs(prev_cc - cc) < step_tol:
            break

        f_T = cc - target_ccoeff
        if f_T < 0:
            cur_max = T
            f_max = f_T
        else:
            cur_min = T
            f_min = f_T
        prev_cc = cc

    return best_T, best_cc, best_edges, iter_records, m


def run_v3_generation(
    node_id_path,
    cluster_id_path,
    assignment_path,
    degree_path,
    mincut_path,
    edge_counts_path,
    orig_edgelist_path,
    orig_clustering_path,
    output_dir,
    seed,
    gamma,
    m_policy,
    m_floor,
    search_max_iters,
    search_diff_tol,
    search_step_tol,
    search_t_min,
    search_t_max,
    initial_T,
):
    output_dir = standard_setup(output_dir)
    np.random.seed(seed)

    logging.info("Starting EC-SBM v3 (PSO per-cluster, T-search) ...")
    logging.info(
        f"seed={seed} gamma={gamma} m_policy={m_policy} m_floor={m_floor} "
        f"t_min={search_t_min} t_max={search_t_max} "
        f"max_iters={search_max_iters} diff_tol={search_diff_tol}"
    )

    with timed("Input loading"):
        node_id2id, node2cluster, clustering, deg, mcs, _probs = load_inputs(
            node_id_path, cluster_id_path, assignment_path,
            degree_path, mincut_path, edge_counts_path,
        )
        cluster_id_strs = _read_cluster_id_to_str(cluster_id_path)
        empirical_stats_by_str = _empirical_intra_cluster_stats(
            orig_edgelist_path, orig_clustering_path,
        )

    pso_edges = set()
    pso_log = {}

    with timed("Per-cluster PSO + T search"):
        for cluster_iid in sorted(clustering):
            cluster_nodes = clustering[cluster_iid]
            # Sort by descending residual degree, tie-break on iid asc, so
            # the highest-degree node in the cluster plays the role of the
            # PSO "node 1" (oldest, highest popularity).
            cluster_nodes_sorted = sorted(
                cluster_nodes, key=lambda n_iid: (-int(deg[n_iid]), n_iid)
            )
            n = len(cluster_nodes_sorted)
            k = int(mcs[cluster_iid])
            cluster_id_str = cluster_id_strs[cluster_iid]
            stats = empirical_stats_by_str.get(
                cluster_id_str, {"ccoeff": 0.0, "mean_deg": 0.0, "n": n}
            )
            target_cc = float(stats["ccoeff"])
            empirical_mean_deg = float(stats["mean_deg"])

            cluster_seed = (int(seed) * 9_999_991 + int(cluster_iid)) & 0xFFFFFFFF
            best_T, best_cc, best_edges_local, iter_records, m_used = _search_T_for_cluster(
                cluster_nodes_sorted, k, gamma, target_cc, cluster_seed,
                search_max_iters, search_diff_tol, search_step_tol,
                search_t_min, search_t_max, initial_T,
                m_policy, m_floor, empirical_mean_deg,
            )
            best_cc_disp = f"{best_cc:.4f}" if best_cc is not None else "n/a"
            best_T_disp = f"{best_T:.4f}" if best_T is not None else "n/a"
            logging.info(
                f"Cluster iid={cluster_iid} (id={cluster_id_str}) n={n} k={k} m={m_used} "
                f"target_cc={target_cc:.4f} best_T={best_T_disp} "
                f"best_cc={best_cc_disp} iters={len(iter_records)}"
            )

            for u_local, v_local in best_edges_local:
                u_iid = cluster_nodes_sorted[u_local]
                v_iid = cluster_nodes_sorted[v_local]
                e = normalize_edge(u_iid, v_iid)
                pso_edges.add(e)
                deg[u_iid] -= 1
                deg[v_iid] -= 1

            pso_log[str(cluster_iid)] = {
                "cluster_id": cluster_id_str,
                "n": n,
                "k": k,
                "m": m_used,
                "empirical_mean_intra_deg": empirical_mean_deg,
                "target_ccoeff": target_cc,
                "best_T": best_T,
                "best_ccoeff": best_cc,
                "n_iters": len(iter_records),
                "iters": iter_records,
            }

    with timed(f"Exporting {len(pso_edges)} PSO edges"):
        sorted_edges = sorted(pso_edges)
        rows = [(node_id2id[u], node_id2id[v]) for u, v in sorted_edges]
        pd.DataFrame(rows, columns=["source", "target"]).to_csv(
            output_dir / "edge.csv", index=False,
        )
        sources = {}
        if sorted_edges:
            sources["clustered_pso_core"] = [1, len(sorted_edges)]
        with open(output_dir / "sources.json", "w") as f:
            json.dump(sources, f, indent=4)
        with open(output_dir / PSO_SEARCH_LOG_NAME, "w") as f:
            json.dump(pso_log, f, indent=2, sort_keys=True)

    logging.info("EC-SBM v3 clustered generation complete.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="EC-SBM stage 2 (v3): per-cluster PSO with T-search."
    )
    parser.add_argument("--node-id", type=str, required=True)
    parser.add_argument("--cluster-id", type=str, required=True)
    parser.add_argument("--assignment", type=str, required=True)
    parser.add_argument("--degree", type=str, required=True)
    parser.add_argument("--mincut", type=str, required=True)
    parser.add_argument("--edge-counts", type=str, required=True)
    parser.add_argument(
        "--orig-edgelist", type=str, required=True,
        help="Empirical edgelist; used to compute per-cluster target ccoeff.",
    )
    parser.add_argument(
        "--orig-clustering", type=str, required=True,
        help="Empirical clustering; used to compute per-cluster target ccoeff.",
    )
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--params-file", type=str, default=None)
    parser.add_argument("--pso-gamma", type=float, default=None,
                        help=f"Power-law exponent (>=2). Default {DEFAULT_PSO_GAMMA}.")
    parser.add_argument("--pso-m-policy", type=str, default=None,
                        choices=["auto", "floor"],
                        help=f"How to derive per-cluster PSO m. "
                             f"'auto' (default {DEFAULT_PSO_M_POLICY}) sets "
                             f"m = max(k, m_floor, round(empirical_mean_intra_deg/2)) "
                             f"so dense clusters get more triangle capacity. "
                             f"'floor' uses just max(k, m_floor).")
    parser.add_argument("--pso-m-floor", type=int, default=None,
                        help=f"Hard lower bound on per-cluster m. m = max(k, this, ...). "
                             f"Default {DEFAULT_PSO_M_FLOOR}.")
    parser.add_argument("--pso-search-max-iters", type=int, default=None,
                        help=f"T-search iter cap. Default {DEFAULT_SEARCH_MAX_ITERS}.")
    parser.add_argument("--pso-search-diff-tol", type=float, default=None,
                        help=f"|cc - target| early-stop. Default {DEFAULT_SEARCH_DIFF_TOL}.")
    parser.add_argument("--pso-search-step-tol", type=float, default=None,
                        help=f"|cc - prev_cc| early-stop. Default {DEFAULT_SEARCH_STEP_TOL}.")
    parser.add_argument("--pso-search-t-min", type=float, default=None,
                        help=f"T lower bound. Default {DEFAULT_SEARCH_T_MIN}.")
    parser.add_argument("--pso-search-t-max", type=float, default=None,
                        help=f"T upper bound. Default {DEFAULT_SEARCH_T_MAX}.")
    parser.add_argument("--pso-initial-t", type=float, default=None,
                        help=f"T used when search is short-circuited "
                             f"(complete-graph regime). Default {DEFAULT_INITIAL_T}.")
    return parser.parse_args()


def main():
    args = parse_args()
    file_params = read_params(args.params_file) if args.params_file else None

    def _f(cli, key, default):
        return float(resolve_param(cli, file_params, key, default=default))

    def _i(cli, key, default):
        return int(resolve_param(cli, file_params, key, default=default))

    gamma = _f(args.pso_gamma, "pso_gamma", DEFAULT_PSO_GAMMA)
    m_policy = resolve_param(args.pso_m_policy, file_params, "pso_m_policy",
                             default=DEFAULT_PSO_M_POLICY)
    m_floor = _i(args.pso_m_floor, "pso_m_floor", DEFAULT_PSO_M_FLOOR)
    max_iters = _i(args.pso_search_max_iters, "pso_search_max_iters",
                   DEFAULT_SEARCH_MAX_ITERS)
    diff_tol = _f(args.pso_search_diff_tol, "pso_search_diff_tol",
                  DEFAULT_SEARCH_DIFF_TOL)
    step_tol = _f(args.pso_search_step_tol, "pso_search_step_tol",
                  DEFAULT_SEARCH_STEP_TOL)
    t_min = _f(args.pso_search_t_min, "pso_search_t_min", DEFAULT_SEARCH_T_MIN)
    t_max = _f(args.pso_search_t_max, "pso_search_t_max", DEFAULT_SEARCH_T_MAX)
    initial_T = _f(args.pso_initial_t, "pso_initial_t", DEFAULT_INITIAL_T)

    run_v3_generation(
        args.node_id,
        args.cluster_id,
        args.assignment,
        args.degree,
        args.mincut,
        args.edge_counts,
        args.orig_edgelist,
        args.orig_clustering,
        args.output_folder,
        args.seed,
        gamma,
        m_policy,
        m_floor,
        max_iters,
        diff_tol,
        step_tol,
        t_min,
        t_max,
        initial_T,
    )


if __name__ == "__main__":
    main()
