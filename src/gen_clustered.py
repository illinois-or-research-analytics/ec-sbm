"""Stage 2: per-cluster clustered subgraph.

Two methods, selected via ``--method``:

- ``res-deg-weighted`` (default; v1/v2 of the EC-SBM paper): build a
  K_{k+1} clique on the top-(k+1) nodes by residual degree, then attach
  each remaining node with k edges (greedy top-of-processed first,
  residual-degree-weighted random sampling as fallback). Optionally
  overlay an SBM sample on the mutated residual via ``--sbm-overlay``.
  Edges are tagged ``clustered_kec_clique`` / ``clustered_kec_attach``
  / ``clustered_sbm_overlay``.
- ``pso`` (v3): per-cluster Popularity-Similarity-Optimization
  (uniform angular distribution, ``m = max(k, m_floor)`` capped at
  ``n - 1``) with a 1-D T-search (``secant`` default, ``bayesian``
  opt-in via Optuna TPE) to drive simulated cluster ccoeff toward the
  per-cluster target read from ``--cluster-ccoeff`` (profile artifact).
  Edges are tagged ``clustered_pso_core``.

Both methods produce subgraphs whose per-cluster mincut is at least
the empirical k. Stages 3a / 4a are unchanged.
"""
from __future__ import annotations

import argparse
import json
import logging
import random

import numpy as np
import pandas as pd

from pipeline_common import standard_setup, timed
from gen_kec_core import generate_internal_edges_bands, load_inputs
from gen_pso_core import pso_cluster_edges, induced_global_ccoeff
from graph_utils import normalize_edge
from params_common import _parse_bool, read_params, resolve_param


METHODS = ("res-deg-weighted", "pso")
DEFAULT_METHOD = "res-deg-weighted"
DEFAULT_SBM_OVERLAY = False

# PSO defaults: gamma=2 collapses radial coords to r_i = 2*log(arrival_rank);
# combined with the descending-residual-degree sort the empirical degree
# ordering enters PSO geometry directly. Override only for ablation.
DEFAULT_PSO_GAMMA = 2.0
DEFAULT_PSO_M_FLOOR = 1
# Secant beats Bayesian on the trend-with-noise objective in the swept
# regimes (see tools/npso_bo_sweep/). Bayesian (Optuna TPE) opt-in.
DEFAULT_SEARCH_STRATEGY = "secant"
DEFAULT_SEARCH_MAX_ITERS = 30
DEFAULT_SEARCH_INITIAL_POINTS = 3
DEFAULT_SEARCH_SAMPLES_PER_T = 3
DEFAULT_SEARCH_DIFF_TOL = 0.01
DEFAULT_SEARCH_STEP_TOL = 1e-4
DEFAULT_SEARCH_T_MIN = 0.01
DEFAULT_SEARCH_T_MAX = 0.99
DEFAULT_INITIAL_T = 0.5
PSO_SEARCH_LOG_NAME = "pso_search_log.json"
SEARCH_STRATEGIES = ("bayesian", "secant")


# ---------------------------------------------------------------------------
# res-deg-weighted (v1 / v2) helpers
# ---------------------------------------------------------------------------


def synthesize_sbm_network(node_id2id, node2cluster, deg, probs, edges):
    """v1 overlay: run ``gt.generate_sbm`` on the mutated residual,
    merge the constructive edges, drop parallels/self-loops.
    """
    import graph_tool.all as gt  # lazy: only paid when overlay is on

    b = np.array([node2cluster.get(i, -1) for i in range(len(node_id2id))])

    if deg.sum() > 0:
        g = gt.generate_sbm(
            b,
            probs.tocsr(),
            out_degs=deg,
            micro_ers=True,
            micro_degs=True,
            directed=False,
        )
    else:
        g = gt.Graph(directed=False)

    g.add_edge_list(edges)
    gt.remove_parallel_edges(g)
    gt.remove_self_loops(g)
    return g


def _write_bands_csv(output_path, bands_in_order, node_id2id):
    """Write ``edge.csv`` row-grouped by band, sorted within each band;
    emit a sibling ``sources.json`` mapping each band name to a 1-based
    inclusive [start, end] range. Empty bands omitted from sources.json.
    """
    rows = []
    sources = {}
    cursor = 1
    for band_name, edge_iter in bands_in_order:
        sorted_edges = sorted(edge_iter)
        if not sorted_edges:
            continue
        for u, v in sorted_edges:
            rows.append((node_id2id[u], node_id2id[v]))
        sources[band_name] = [cursor, cursor + len(sorted_edges) - 1]
        cursor += len(sorted_edges)
    pd.DataFrame(rows, columns=["source", "target"]).to_csv(output_path, index=False)
    with open(output_path.parent / "sources.json", "w") as f:
        json.dump(sources, f, indent=4)


def _run_res_deg_weighted(
    node_id_path, cluster_id_path, assignment_path, degree_path,
    mincut_path, edge_counts_path,
    output_dir, seed, sbm_overlay,
):
    random.seed(seed)
    np.random.seed(seed)
    if sbm_overlay:
        import graph_tool.all as gt
        gt.seed_rng(seed)

    logging.info(
        "Stage 2 method=res-deg-weighted (sbm_overlay=%s)...", sbm_overlay,
    )

    with timed("Input loading"):
        node_id2id, node2cluster, clustering, deg, mcs, probs = load_inputs(
            node_id_path, cluster_id_path, assignment_path,
            degree_path, mincut_path, edge_counts_path,
        )

    with timed("Generation of k-edge-connected cores"):
        kec_bands = generate_internal_edges_bands(
            clustering, mcs, deg, probs, node2cluster,
        )
    clique_edges = kec_bands["kec_clique"]
    attach_edges = kec_bands["kec_attach"]
    kec_edges_sorted = sorted(clique_edges | attach_edges)

    if sbm_overlay:
        with timed("SBM overlay synthesis"):
            g = synthesize_sbm_network(
                node_id2id, node2cluster, deg, probs, kec_edges_sorted,
            )
        with timed("Export"):
            final_edges = {normalize_edge(int(u), int(v)) for u, v in g.iter_edges()}
            overlay_edges = final_edges - clique_edges - attach_edges
            bands = [
                ("clustered_kec_clique", clique_edges & final_edges),
                ("clustered_kec_attach", attach_edges & final_edges),
                ("clustered_sbm_overlay", overlay_edges),
            ]
            _write_bands_csv(output_dir / "edge.csv", bands, node_id2id)
    else:
        with timed(f"Exporting {len(kec_edges_sorted)} constructive edges"):
            bands = [
                ("clustered_kec_clique", clique_edges),
                ("clustered_kec_attach", attach_edges),
            ]
            _write_bands_csv(output_dir / "edge.csv", bands, node_id2id)


# ---------------------------------------------------------------------------
# pso (v3) helpers
# ---------------------------------------------------------------------------


def _next_T(min_T, max_T, f_min_T, f_max_T):
    """Bisection by default; secant when both endpoint residuals are
    known and have opposite signs. Same heuristic as src/npso/gen.py."""
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


def _read_cluster_id_to_str(cluster_id_path):
    return pd.read_csv(cluster_id_path, header=None, dtype=str)[0].tolist()


def _read_target_ccoeff(path):
    """Profile's ``cluster_ccoeff.csv``: one float per cluster iid."""
    return pd.read_csv(path, header=None)[0].to_numpy(dtype=float, copy=True)


def _resolve_m(k, n, m_floor):
    """``m = min(max(k, m_floor), n - 1)``. ``m >= k`` keeps the
    cluster k-edge-connected; raise ``m_floor`` above 1 to give triangle
    capacity to clusters whose empirical mincut is degenerate."""
    return min(max(int(k), int(m_floor)), n - 1)


def _eval_T(n, m, T, gamma, base_seed, samples_per_T):
    """Run PSO ``samples_per_T`` times at temperature ``T`` and return
    ``(mean_ccoeff, representative_edges_local, sample_ccoeffs)``.

    Per-realisation seed = ``(base_seed * 1_000_003 + sample_idx)
    & 0xFFFFFFFF``. Representative is the realisation whose ccoeff is
    closest to the mean (so the chosen edge set tracks the averaged
    signal).
    """
    cs = []
    edges_list = []
    for s in range(samples_per_T):
        seed_iter = (base_seed * 1_000_003 + s) & 0xFFFFFFFF
        edges_local = pso_cluster_edges(n, m, T, gamma, seed_iter)
        cc = induced_global_ccoeff(n, edges_local)
        cs.append(cc)
        edges_list.append(edges_local)
    mean_cc = float(np.mean(cs))
    if samples_per_T == 1:
        return mean_cc, edges_list[0], cs
    diffs = [abs(c - mean_cc) for c in cs]
    rep_idx = int(np.argmin(diffs))
    return mean_cc, edges_list[rep_idx], cs


def _search_T_secant(
    n, m, gamma, target_ccoeff, base_seed,
    max_iters, diff_tol, step_tol, t_min, t_max, samples_per_T,
):
    """Bisection + secant over T."""
    iter_records = []
    f_min, f_max = None, None
    best_T = best_cc = best_diff = best_edges = None
    prev_cc = None
    cur_min, cur_max = t_min, t_max
    for it in range(max_iters):
        T = _next_T(cur_min, cur_max, f_min, f_max)
        iter_seed = (base_seed * 7_777_771 + it) & 0xFFFFFFFF
        cc, edges_local, samples = _eval_T(n, m, T, gamma, iter_seed, samples_per_T)
        diff = abs(cc - target_ccoeff)
        iter_records.append({
            "T": T, "ccoeff": cc, "diff": diff,
            "samples": samples if samples_per_T > 1 else None,
        })
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
    return best_T, best_cc, best_edges, iter_records


def _search_T_bayesian(
    n, m, gamma, target_ccoeff, base_seed,
    max_iters, initial_points, diff_tol, step_tol,
    t_min, t_max, samples_per_T,
):
    """Optuna TPE sampler over T. Optuna is an opt-in dependency; the
    caller catches ImportError and falls back to secant.
    """
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    n_startup = max(1, min(initial_points, max_iters))
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(
            n_startup_trials=n_startup,
            seed=int(base_seed) % (2**32 - 1),
        ),
    )
    dist = optuna.distributions.FloatDistribution(t_min, t_max)

    iter_records = []
    best_T = best_cc = best_diff = best_edges = None
    prev_diff = None
    for it in range(max_iters):
        trial = study.ask({"T": dist})
        T = float(trial.params["T"])
        iter_seed = (base_seed * 7_777_771 + it) & 0xFFFFFFFF
        cc, edges_local, samples = _eval_T(n, m, T, gamma, iter_seed, samples_per_T)
        diff = abs(cc - target_ccoeff)
        iter_records.append({
            "T": T, "ccoeff": cc, "diff": diff,
            "samples": samples if samples_per_T > 1 else None,
        })
        study.tell(trial, diff)
        if best_cc is None or diff < best_diff:
            best_T, best_cc, best_diff = T, cc, diff
            best_edges = edges_local
        if best_diff < diff_tol:
            break
        if prev_diff is not None and abs(prev_diff - diff) < step_tol:
            break
        prev_diff = diff
    return best_T, best_cc, best_edges, iter_records


def _search_T_for_cluster(
    cluster_nodes_iid, k, gamma, target_ccoeff, base_seed,
    max_iters, diff_tol, step_tol, t_min, t_max, initial_T,
    m_floor, strategy, initial_points, samples_per_T,
):
    """Resolve m, short-circuit complete-graph regime, dispatch to
    secant / bayesian. Returns ``(best_T, best_cc, best_edges, iters,
    m)``.
    """
    n = len(cluster_nodes_iid)
    if n <= 1 or k <= 0:
        return None, 0.0, [], [], 0
    m = _resolve_m(k, n, m_floor)
    if m < 1:
        m = 1
    if n <= m + 1:
        edges_local = pso_cluster_edges(n, m, initial_T, gamma, base_seed)
        cc = induced_global_ccoeff(n, edges_local)
        return (
            initial_T, cc, edges_local,
            [{"T": initial_T, "ccoeff": cc, "note": "complete_graph"}],
            m,
        )

    if strategy == "bayesian":
        try:
            r = _search_T_bayesian(
                n, m, gamma, target_ccoeff, base_seed,
                max_iters, initial_points, diff_tol, step_tol,
                t_min, t_max, samples_per_T,
            )
        except ImportError:
            logging.warning(
                "optuna missing; falling back to secant for cluster n=%d", n,
            )
            r = _search_T_secant(
                n, m, gamma, target_ccoeff, base_seed,
                max_iters, diff_tol, step_tol, t_min, t_max, samples_per_T,
            )
    elif strategy == "secant":
        r = _search_T_secant(
            n, m, gamma, target_ccoeff, base_seed,
            max_iters, diff_tol, step_tol, t_min, t_max, samples_per_T,
        )
    else:
        raise ValueError(f"unknown search strategy: {strategy!r}")
    best_T, best_cc, best_edges, iter_records = r
    return best_T, best_cc, best_edges, iter_records, m


def _run_pso(
    node_id_path, cluster_id_path, assignment_path, degree_path,
    mincut_path, edge_counts_path, cluster_ccoeff_path,
    output_dir, seed,
    gamma, m_floor,
    search_strategy, search_max_iters, search_initial_points,
    search_samples_per_T, search_diff_tol, search_step_tol,
    search_t_min, search_t_max, initial_T,
):
    np.random.seed(seed)
    logging.info(
        "Stage 2 method=pso seed=%s gamma=%s m_floor=%s strategy=%s "
        "initial_points=%s samples_per_T=%s t_min=%s t_max=%s "
        "max_iters=%s diff_tol=%s",
        seed, gamma, m_floor, search_strategy,
        search_initial_points, search_samples_per_T,
        search_t_min, search_t_max, search_max_iters, search_diff_tol,
    )
    with timed("Input loading"):
        node_id2id, _, clustering, deg, mcs, _ = load_inputs(
            node_id_path, cluster_id_path, assignment_path,
            degree_path, mincut_path, edge_counts_path,
        )
        cluster_id_strs = _read_cluster_id_to_str(cluster_id_path)
        target_cc_by_iid = _read_target_ccoeff(cluster_ccoeff_path)

    pso_edges = set()
    pso_log = {}
    with timed("Per-cluster PSO + T search"):
        for cluster_iid in sorted(clustering):
            cluster_nodes = clustering[cluster_iid]
            cluster_nodes_sorted = sorted(
                cluster_nodes, key=lambda n_iid: (-int(deg[n_iid]), n_iid)
            )
            n = len(cluster_nodes_sorted)
            k = int(mcs[cluster_iid])
            cluster_id_str = cluster_id_strs[cluster_iid]
            target_cc = float(target_cc_by_iid[cluster_iid])
            cluster_seed = (int(seed) * 9_999_991 + int(cluster_iid)) & 0xFFFFFFFF
            best_T, best_cc, best_edges_local, iter_records, m_used = _search_T_for_cluster(
                cluster_nodes_sorted, k, gamma, target_cc, cluster_seed,
                search_max_iters, search_diff_tol, search_step_tol,
                search_t_min, search_t_max, initial_T,
                m_floor, search_strategy, search_initial_points, search_samples_per_T,
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
                "cluster_id": cluster_id_str, "n": n, "k": k, "m": m_used,
                "target_ccoeff": target_cc, "best_T": best_T,
                "best_ccoeff": best_cc, "n_iters": len(iter_records),
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


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------


def run_clustered_generation(
    method,
    node_id_path, cluster_id_path, assignment_path, degree_path,
    mincut_path, edge_counts_path,
    output_dir, seed,
    sbm_overlay=DEFAULT_SBM_OVERLAY,
    cluster_ccoeff_path=None,
    pso_gamma=DEFAULT_PSO_GAMMA,
    pso_m_floor=DEFAULT_PSO_M_FLOOR,
    search_strategy=DEFAULT_SEARCH_STRATEGY,
    search_max_iters=DEFAULT_SEARCH_MAX_ITERS,
    search_initial_points=DEFAULT_SEARCH_INITIAL_POINTS,
    search_samples_per_T=DEFAULT_SEARCH_SAMPLES_PER_T,
    search_diff_tol=DEFAULT_SEARCH_DIFF_TOL,
    search_step_tol=DEFAULT_SEARCH_STEP_TOL,
    search_t_min=DEFAULT_SEARCH_T_MIN,
    search_t_max=DEFAULT_SEARCH_T_MAX,
    initial_T=DEFAULT_INITIAL_T,
):
    output_dir = standard_setup(output_dir)
    logging.info("Starting EC-SBM clustered generation (method=%s)...", method)
    if method == "res-deg-weighted":
        _run_res_deg_weighted(
            node_id_path, cluster_id_path, assignment_path, degree_path,
            mincut_path, edge_counts_path,
            output_dir, seed, sbm_overlay,
        )
    elif method == "pso":
        if cluster_ccoeff_path is None:
            raise ValueError("method=pso requires --cluster-ccoeff")
        _run_pso(
            node_id_path, cluster_id_path, assignment_path, degree_path,
            mincut_path, edge_counts_path, cluster_ccoeff_path,
            output_dir, seed,
            pso_gamma, pso_m_floor,
            search_strategy, search_max_iters, search_initial_points,
            search_samples_per_T, search_diff_tol, search_step_tol,
            search_t_min, search_t_max, initial_T,
        )
    else:
        raise ValueError(f"unknown method: {method!r}; expected one of {METHODS}")
    logging.info("Clustered generation complete.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="EC-SBM stage 2: per-cluster clustered subgraph "
                    "(res-deg-weighted or pso)."
    )
    parser.add_argument("--node-id", type=str, required=True)
    parser.add_argument("--cluster-id", type=str, required=True)
    parser.add_argument("--assignment", type=str, required=True)
    parser.add_argument("--degree", type=str, required=True)
    parser.add_argument("--mincut", type=str, required=True)
    parser.add_argument("--edge-counts", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--params-file", type=str, default=None)
    parser.add_argument(
        "--method", choices=METHODS, default=None,
        help="res-deg-weighted (v1/v2 K_{k+1}+attach) or pso (v3, "
             "PSO + T-search). Default res-deg-weighted.",
    )
    overlay = parser.add_mutually_exclusive_group()
    overlay.add_argument(
        "--sbm-overlay",
        dest="sbm_overlay", action="store_true", default=None,
        help="res-deg-weighted only: run gt.generate_sbm on the residual "
             "and overlay the constructive edges (v1-style).",
    )
    overlay.add_argument(
        "--no-sbm-overlay",
        dest="sbm_overlay", action="store_false",
        help="Skip the overlay; emit only constructive edges (v2-style).",
    )
    parser.add_argument(
        "--cluster-ccoeff", type=str, default=None,
        help="pso only: profile artifact (cluster_ccoeff.csv) — one float "
             "per cluster iid, the per-cluster T-search target.",
    )
    parser.add_argument("--pso-gamma", type=float, default=None,
                        help=f"pso only: PSO power-law exponent. "
                             f"Default {DEFAULT_PSO_GAMMA}.")
    parser.add_argument("--pso-m-floor", type=int, default=None,
                        help=f"pso only: per-cluster m = min(max(k, this), "
                             f"n - 1). Default {DEFAULT_PSO_M_FLOOR}.")
    parser.add_argument("--pso-search-strategy", type=str, default=None,
                        choices=list(SEARCH_STRATEGIES),
                        help=f"pso only: T-search strategy. Default "
                             f"{DEFAULT_SEARCH_STRATEGY}.")
    parser.add_argument("--pso-search-max-iters", type=int, default=None,
                        help=f"pso only. Default {DEFAULT_SEARCH_MAX_ITERS}.")
    parser.add_argument("--pso-search-initial-points", type=int, default=None,
                        help=f"pso only (bayesian/TPE n_startup_trials). "
                             f"Default {DEFAULT_SEARCH_INITIAL_POINTS}.")
    parser.add_argument("--pso-search-samples-per-T", type=int, default=None,
                        help=f"pso only. Default {DEFAULT_SEARCH_SAMPLES_PER_T}.")
    parser.add_argument("--pso-search-diff-tol", type=float, default=None,
                        help=f"pso only. Default {DEFAULT_SEARCH_DIFF_TOL}.")
    parser.add_argument("--pso-search-step-tol", type=float, default=None,
                        help=f"pso only. Default {DEFAULT_SEARCH_STEP_TOL}.")
    parser.add_argument("--pso-search-t-min", type=float, default=None,
                        help=f"pso only. Default {DEFAULT_SEARCH_T_MIN}.")
    parser.add_argument("--pso-search-t-max", type=float, default=None,
                        help=f"pso only. Default {DEFAULT_SEARCH_T_MAX}.")
    parser.add_argument("--pso-initial-t", type=float, default=None,
                        help=f"pso only. Default {DEFAULT_INITIAL_T}.")
    return parser.parse_args()


def main():
    args = parse_args()
    file_params = read_params(args.params_file) if args.params_file else None

    def _f(cli, key, default):
        return float(resolve_param(cli, file_params, key, default=default))

    def _i(cli, key, default):
        return int(resolve_param(cli, file_params, key, default=default))

    method = resolve_param(args.method, file_params, "method", default=DEFAULT_METHOD)
    if method not in METHODS:
        raise SystemExit(f"unknown method: {method!r}; expected one of {METHODS}")
    sbm_overlay = resolve_param(
        args.sbm_overlay, file_params, "sbm_overlay",
        default=DEFAULT_SBM_OVERLAY, parser=_parse_bool,
    )
    pso_gamma = _f(args.pso_gamma, "pso_gamma", DEFAULT_PSO_GAMMA)
    pso_m_floor = _i(args.pso_m_floor, "pso_m_floor", DEFAULT_PSO_M_FLOOR)
    strategy = resolve_param(
        args.pso_search_strategy, file_params, "pso_search_strategy",
        default=DEFAULT_SEARCH_STRATEGY,
    )
    if strategy not in SEARCH_STRATEGIES:
        raise SystemExit(f"unknown pso_search_strategy: {strategy!r}")
    initial_points = _i(args.pso_search_initial_points,
                        "pso_search_initial_points",
                        DEFAULT_SEARCH_INITIAL_POINTS)
    samples_per_T = _i(args.pso_search_samples_per_T,
                       "pso_search_samples_per_T",
                       DEFAULT_SEARCH_SAMPLES_PER_T)
    max_iters = _i(args.pso_search_max_iters, "pso_search_max_iters",
                   DEFAULT_SEARCH_MAX_ITERS)
    diff_tol = _f(args.pso_search_diff_tol, "pso_search_diff_tol",
                  DEFAULT_SEARCH_DIFF_TOL)
    step_tol = _f(args.pso_search_step_tol, "pso_search_step_tol",
                  DEFAULT_SEARCH_STEP_TOL)
    t_min = _f(args.pso_search_t_min, "pso_search_t_min", DEFAULT_SEARCH_T_MIN)
    t_max = _f(args.pso_search_t_max, "pso_search_t_max", DEFAULT_SEARCH_T_MAX)
    initial_T = _f(args.pso_initial_t, "pso_initial_t", DEFAULT_INITIAL_T)

    cluster_ccoeff = resolve_param(
        args.cluster_ccoeff, file_params, "cluster_ccoeff", default=None,
    )

    run_clustered_generation(
        method,
        args.node_id, args.cluster_id, args.assignment, args.degree,
        args.mincut, args.edge_counts,
        args.output_folder, args.seed,
        sbm_overlay=sbm_overlay,
        cluster_ccoeff_path=cluster_ccoeff,
        pso_gamma=pso_gamma,
        pso_m_floor=pso_m_floor,
        search_strategy=strategy,
        search_max_iters=max_iters,
        search_initial_points=initial_points,
        search_samples_per_T=samples_per_T,
        search_diff_tol=diff_tol,
        search_step_tol=step_tol,
        search_t_min=t_min,
        search_t_max=t_max,
        initial_T=initial_T,
    )


if __name__ == "__main__":
    main()
