"""Stage 3a: SBM-sample the edges that stage 2 did not place.

Two preset behaviors and a handful of knobs that parameterize the
space between them.

Presets:

- "v1" (outlier-only SBM): ``--scope outlier-incident --outlier-mode singleton
  --edge-correction none`` (no ``--exist-edgelist``). Only edges incident
  to outliers contribute to ``probs`` and ``out_degs``; every outlier is
  its own block; no block-preserving rewire; the orig edgelist is
  consumed as-is (no dedup; v1's historical shape).
- "v2" (residual SBM over all blocks): ``--scope all --outlier-mode combined
  --edge-correction rewire --exist-edgelist <stage-2 output>``. All orig
  edges contribute; outliers share one combined block; stage 2's edges
  are subtracted from the per-node residual; block-diagonals rebalanced
  so graph-tool's parity constraint is satisfied; invalid SBM edges go
  through a block-preserving 2-opt rewire.

Knobs:

- ``--scope {outlier-incident,all}``: which edges contribute to probs
  and out_degs. Outlier-incident: only edges with at least one outlier
  endpoint (v1 shape). All: every orig edge, inter-block contributes to
  probs, all contribute to out_degs (v2 shape).
- ``--outlier-mode {combined,singleton}``: block structure for outlier
  nodes. Combined: all outliers share one block. Singleton: each
  outlier gets its own block.
- ``--edge-correction {none,drop,rewire}``: post-SBM correction for
  self-loops and duplicates. None: only remove_parallel + remove_self.
  Drop: same as none (kept as a named alternative for clarity). Rewire:
  block-preserving 2-opt swap, fall back to drop for unresolved.
- ``--exist-edgelist <p>`` (optional): edges already placed by a prior
  stage. Their contribution is subtracted from ``out_degs`` (clamped at
  0) after the orig accumulation. Only applied when ``--scope all``.

The v1 and v2 presets reduce to distinct algorithms; any other
combination is a novel mix, useful for ablations or for matching a
non-standard profile.
"""
from __future__ import annotations

import argparse
import logging
import random
from collections import defaultdict, deque

import graph_tool.all as gt
import numpy as np
import pandas as pd
from scipy.sparse import dok_matrix

from graph_utils import normalize_edge, run_rewire_attempts
from params_common import read_params, resolve_param
from pipeline_common import standard_setup, timed, write_edge_tuples_csv


SCOPES = ("outlier-incident", "all")
OUTLIER_MODES = ("combined", "singleton")
EDGE_CORRECTIONS = ("none", "drop", "rewire")

DEFAULT_SCOPE = "all"
DEFAULT_OUTLIER_MODE = "combined"
DEFAULT_EDGE_CORRECTION = "rewire"


# ---------------------------------------------------------------------------
# Input I/O
# ---------------------------------------------------------------------------

def load_network_data(orig_edgelist_fp, orig_clustering_fp, exist_edgelist_fp=None):
    df_orig = pd.read_csv(orig_edgelist_fp, dtype=str)
    df_clust = pd.read_csv(orig_clustering_fp, dtype=str)

    if exist_edgelist_fp is not None:
        try:
            df_exist = pd.read_csv(exist_edgelist_fp, dtype=str)
        except pd.errors.EmptyDataError:
            df_exist = pd.DataFrame(columns=["source", "target"])
    else:
        df_exist = pd.DataFrame(columns=["source", "target"])

    node2cluster_str = dict(zip(df_clust["node_id"], df_clust["cluster_id"]))
    return df_orig, df_exist, node2cluster_str


def build_node_universe(df_orig, node2cluster_str, scope):
    """Return (all_nodes, outliers).

    Under ``scope=outlier-incident`` the clustering's keys are unioned in
    so clustered nodes that are isolated in the orig edgelist are still
    assigned a block (v1 historical shape). Under ``scope=all`` only the
    orig edge endpoints enter the universe.

    Returned ``all_nodes`` is sorted so iid numbering downstream does not
    depend on PYTHONHASHSEED.
    """
    all_nodes = set(df_orig["source"]).union(set(df_orig["target"]))
    if scope == "outlier-incident":
        all_nodes = all_nodes.union(set(node2cluster_str.keys()))
    outliers = all_nodes - set(node2cluster_str.keys())
    return sorted(all_nodes), sorted(outliers)


# ---------------------------------------------------------------------------
# Block assignment
# ---------------------------------------------------------------------------

def assign_blocks(all_nodes, outliers, node2cluster_str, outlier_mode):
    """Return (node_id2iid, node_iid2id, outlier_iids, b, num_clusters).

    ``all_nodes`` and ``outliers`` are expected to come from
    ``build_node_universe`` already sorted; the iteration here therefore
    produces deterministic iid numbering and singleton-mode block-id
    allocation regardless of PYTHONHASHSEED.
    """
    node_id2iid = {u: i for i, u in enumerate(all_nodes)}
    node_iid2id = {i: u for u, i in node_id2iid.items()}
    outlier_set = set(outliers)
    outlier_iids = {node_id2iid[u] for u in outliers}

    unique_clusters = sorted(set(node2cluster_str.values()))
    cluster_id2iid = {c: i for i, c in enumerate(unique_clusters)}
    current_c_iid = len(cluster_id2iid)

    combined_block = None
    if outliers and outlier_mode == "combined":
        combined_block = current_c_iid
        current_c_iid += 1

    b = np.empty(len(all_nodes), dtype=int)
    for u in all_nodes:
        u_iid = node_id2iid[u]
        if u in outlier_set:
            if outlier_mode == "combined":
                b[u_iid] = combined_block
            else:
                b[u_iid] = current_c_iid
                current_c_iid += 1
        else:
            b[u_iid] = cluster_id2iid[node2cluster_str[u]]

    return node_id2iid, node_iid2id, outlier_iids, b, current_c_iid


# ---------------------------------------------------------------------------
# Probs + out_degs accumulation
# ---------------------------------------------------------------------------

def _undirected_dedup(df):
    """Return (u, v) pairs with u < v, duplicates removed, keyed on string ids."""
    u = np.where(df["source"] < df["target"], df["source"], df["target"])
    v = np.where(df["source"] > df["target"], df["source"], df["target"])
    return pd.DataFrame({"u": u, "v": v}).drop_duplicates()


def _accumulate_outlier_incident(
    df_orig, node_id2iid, outlier_iids, b, num_clusters, num_nodes,
):
    """v1 shape: iterate the raw orig edgelist (no dedup), pick only edges
    with at least one outlier endpoint, and += probs in both directions
    (incl. any intra-block contribution)."""
    probs = dok_matrix((num_clusters, num_clusters), dtype=int)
    out_degs = np.zeros(num_nodes, dtype=int)

    for src, tgt in zip(df_orig["source"], df_orig["target"]):
        u = node_id2iid[src]
        v = node_id2iid[tgt]
        if u in outlier_iids or v in outlier_iids:
            probs[b[u], b[v]] += 1
            probs[b[v], b[u]] += 1
            out_degs[u] += 1
            out_degs[v] += 1
    return probs, out_degs


def _accumulate_all(
    df_orig, df_exist, node_id2iid, b, num_clusters, num_nodes,
):
    """v2 shape: dedup orig, += out_degs for every dedup endpoint, subtract
    exist, then populate inter-block probs, finally rebalance the
    diagonals so graph-tool's parity constraint is satisfied."""
    probs = dok_matrix((num_clusters, num_clusters), dtype=int)
    out_degs = np.zeros(num_nodes, dtype=int)

    df_orig_dedup = _undirected_dedup(df_orig)
    for u_id, v_id in zip(df_orig_dedup["u"], df_orig_dedup["v"]):
        out_degs[node_id2iid[u_id]] += 1
        out_degs[node_id2iid[v_id]] += 1

    if not df_exist.empty:
        df_exist_dedup = _undirected_dedup(df_exist)
        for u_id, v_id in zip(df_exist_dedup["u"], df_exist_dedup["v"]):
            if u_id not in node_id2iid or v_id not in node_id2iid:
                continue
            u, v = node_id2iid[u_id], node_id2iid[v_id]
            out_degs[u] = max(0, out_degs[u] - 1)
            out_degs[v] = max(0, out_degs[v] - 1)

    for u_id, v_id in zip(df_orig_dedup["u"], df_orig_dedup["v"]):
        u, v = node_id2iid[u_id], node_id2iid[v_id]
        b_u, b_v = b[u], b[v]
        if b_u != b_v:
            probs[b_u, b_v] += 1
            probs[b_v, b_u] += 1

    probs_csr = probs.tocsr()
    row_sums = np.array(probs_csr.sum(axis=1)).flatten()

    for k in range(num_clusters):
        nodes_in_k = np.where(b == k)[0]
        if len(nodes_in_k) == 0:
            continue
        D_k = np.sum(out_degs[nodes_in_k])
        E_inter_k = row_sums[k]
        diff = D_k - E_inter_k
        if diff < 0:
            deficit = abs(diff)
            for i in range(deficit):
                out_degs[nodes_in_k[i % len(nodes_in_k)]] += 1
            probs[k, k] = 0
        else:
            probs[k, k] = diff
            if probs[k, k] % 2 != 0:
                probs[k, k] += 1
                out_degs[nodes_in_k[0]] += 1

    return probs, out_degs


def prepare_sbm_inputs(
    df_orig, df_exist, node2cluster_str,
    outlier_mode, scope,
):
    """Build (b, probs, out_degs, node_iid2id) for the residual SBM.

    Returns: (b, probs_csr, out_degs, node_iid2id).
    """
    all_nodes, outliers = build_node_universe(df_orig, node2cluster_str, scope)
    node_id2iid, node_iid2id, outlier_iids, b, num_clusters = assign_blocks(
        all_nodes, outliers, node2cluster_str, outlier_mode,
    )
    num_nodes = len(all_nodes)

    if scope == "outlier-incident":
        probs, out_degs = _accumulate_outlier_incident(
            df_orig, node_id2iid, outlier_iids, b, num_clusters, num_nodes,
        )
    elif scope == "all":
        probs, out_degs = _accumulate_all(
            df_orig, df_exist, node_id2iid, b, num_clusters, num_nodes,
        )
    else:
        raise ValueError(f"unknown scope: {scope!r}; expected one of {SCOPES}")

    return b, probs.tocsr(), out_degs, node_iid2id


# ---------------------------------------------------------------------------
# SBM synthesis + corrections
# ---------------------------------------------------------------------------

def rewire_invalid_edges(g, b, max_retries=10):
    """2-opt block-preserving rewiring of self-loops and multi-edges.

    Groups edges by their (min_block, max_block) pair; swaps within a
    pair so each endpoint stays in its original block. Anything still
    invalid after ``max_retries`` passes is dropped.
    """
    edges = g.get_edges()
    valid_pool = defaultdict(list)
    valid_set = set()
    invalid_edges = deque()

    def get_bp(u, v):
        return (int(min(b[u], b[v])), int(max(b[u], b[v])))

    for u, v in edges:
        e = normalize_edge(u, v)
        if u == v or e in valid_set:
            invalid_edges.append((u, v))
        else:
            bp = get_bp(u, v)
            valid_set.add(e)
            valid_pool[bp].append(e)

    logging.info(f"Initial bad edges before rewiring: {len(invalid_edges)}")

    def process_one_edge(raw_edge, invalid_edges):
        u, v = raw_edge
        bp = get_bp(u, v)
        pool = valid_pool[bp]

        if not pool:
            invalid_edges.append((u, v))
            return False

        idx = random.randrange(len(pool))
        x, y = pool[idx]
        A, B = bp

        if A != B:
            u_A = u if b[u] == A else v
            u_B = v if b[u] == A else u
            x_A = x if b[x] == A else y
            x_B = y if b[x] == A else x
            new_e1, new_e2 = normalize_edge(u_A, x_B), normalize_edge(x_A, u_B)
        else:
            if random.random() < 0.5:
                new_e1, new_e2 = normalize_edge(u, x), normalize_edge(v, y)
            else:
                new_e1, new_e2 = normalize_edge(u, y), normalize_edge(v, x)

        if (
            new_e1[0] != new_e1[1]
            and new_e2[0] != new_e2[1]
            and new_e1 not in valid_set
            and new_e2 not in valid_set
            and new_e1 != new_e2
        ):
            valid_set.remove(normalize_edge(x, y))
            pool[idx] = pool[-1]
            pool.pop()
            valid_set.add(new_e1)
            valid_set.add(new_e2)
            pool.append(new_e1)
            pool.append(new_e2)
        else:
            invalid_edges.append((u, v))

        return False

    run_rewire_attempts(invalid_edges, process_one_edge, max_retries)
    if invalid_edges:
        logging.warning(
            f"Finished {max_retries} retries. {len(invalid_edges)} bad edges "
            "remain unresolved and will be dropped."
        )
    # Sort so the downstream g.add_edge_list call sees a deterministic
    # order (set iteration is hash-slot order; leaks into the post-rewire
    # graph's iter_edges sequence and the edge_outlier.csv row order).
    return sorted(valid_set)


def synthesize_residual_subnetwork(b, probs, out_degs, edge_correction):
    """Sample the residual SBM, apply the chosen edge correction, and
    emit a list of ``(u_iid, v_iid)`` tuples.
    """
    if out_degs.sum() > 0:
        g = gt.generate_sbm(
            b,
            probs,
            out_degs=out_degs,
            micro_ers=True,
            micro_degs=True,
            directed=False,
        )
    else:
        g = gt.Graph(directed=False)

    if edge_correction == "rewire":
        valid_edges = rewire_invalid_edges(g, b, max_retries=10)
        g.clear_edges()
        g.add_edge_list(valid_edges)

    gt.remove_parallel_edges(g)
    gt.remove_self_loops(g)
    return list(g.iter_edges())


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run_outlier_generation(
    orig_edgelist_fp,
    orig_clustering_fp,
    exist_edgelist_fp,
    outlier_mode,
    edge_correction,
    scope,
    output_folder,
    seed,
):
    output_dir = standard_setup(output_folder)

    random.seed(seed)
    np.random.seed(seed)
    gt.seed_rng(seed)

    logging.info(
        "Starting EC-SBM outlier generation "
        "(scope=%s, outlier_mode=%s, edge_correction=%s)...",
        scope, outlier_mode, edge_correction,
    )

    with timed("Setup"):
        df_orig, df_exist, node2cluster_str = load_network_data(
            orig_edgelist_fp, orig_clustering_fp, exist_edgelist_fp,
        )
        b, probs, out_degs, node_iid2id = prepare_sbm_inputs(
            df_orig, df_exist, node2cluster_str,
            outlier_mode, scope,
        )

    with timed("SBM synthesis"):
        edges = synthesize_residual_subnetwork(b, probs, out_degs, edge_correction)

    with timed("Export"):
        write_edge_tuples_csv(output_dir / "edge_outlier.csv", edges, node_iid2id)

    logging.info("Outlier generation complete.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="EC-SBM stage 3a: residual SBM with configurable scope."
    )
    parser.add_argument("--orig-edgelist", type=str, required=True)
    parser.add_argument("--orig-clustering", type=str, required=True)
    parser.add_argument(
        "--exist-edgelist", type=str, default=None,
        help="Previously placed edges to subtract from the residual budget. "
             "Only consulted when --scope=all.",
    )
    parser.add_argument(
        "--outlier-mode", choices=OUTLIER_MODES, default=None,
    )
    parser.add_argument(
        "--scope", choices=SCOPES, default=None,
    )
    parser.add_argument(
        "--edge-correction", choices=EDGE_CORRECTIONS, default=None,
    )
    parser.add_argument("--params-file", type=str, default=None)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args()


def main():
    args = parse_args()
    file_params = read_params(args.params_file) if args.params_file else None
    outlier_mode = resolve_param(
        args.outlier_mode, file_params, "outlier_mode",
        default=DEFAULT_OUTLIER_MODE,
    )
    scope = resolve_param(
        args.scope, file_params, "scope",
        default=DEFAULT_SCOPE,
    )
    edge_correction = resolve_param(
        args.edge_correction, file_params, "edge_correction",
        default=DEFAULT_EDGE_CORRECTION,
    )

    if outlier_mode not in OUTLIER_MODES:
        raise SystemExit(
            f"unknown outlier_mode: {outlier_mode!r}; expected one of {OUTLIER_MODES}"
        )
    if scope not in SCOPES:
        raise SystemExit(
            f"unknown scope: {scope!r}; expected one of {SCOPES}"
        )
    if edge_correction not in EDGE_CORRECTIONS:
        raise SystemExit(
            f"unknown edge_correction: {edge_correction!r}; expected one of {EDGE_CORRECTIONS}"
        )

    run_outlier_generation(
        args.orig_edgelist,
        args.orig_clustering,
        args.exist_edgelist,
        outlier_mode,
        edge_correction,
        scope,
        args.output_folder,
        args.seed,
    )


if __name__ == "__main__":
    main()
