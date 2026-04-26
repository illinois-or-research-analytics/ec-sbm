"""Per-cluster constructive k-edge-connected core.

Phase 1 builds a ``K_{k+1}`` clique on the top-(k+1) nodes by residual
degree; phase 2 attaches each remaining node with ``k`` edges to the
already-processed set. The resulting per-cluster subgraph is guaranteed
k-edge-connected.

Used by ``gen_clustered.py`` as the first step of stage 2; that
wrapper optionally overlays a residual SBM sample on top
(``--sbm-overlay``).
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from graph_utils import normalize_edge
from pipeline_common import load_probs_matrix


def generate_cluster(cluster_nodes, k, deg, probs, node2cluster):
    """Generate a k-edge-connected subgraph for one cluster.

    Phase 1: first k+1 nodes (degree desc) form a complete graph.
    Phase 2: each remaining node connects greedily to the k highest-degree
    processed nodes; falls back to degree-weighted random sampling.

    `deg` and `probs` are mutated in place. When either budget would block
    a required edge, `ensure_edge_capacity` inflates both by 1.
    """
    n = len(cluster_nodes)
    if n == 0 or k == 0:
        return set()
    k = min(k, n - 1)

    int_deg = deg.copy()
    # Tie-break on iid asc so the order is invariant to upstream
    # set/dict iteration when multiple nodes share the same degree.
    cluster_nodes_ordered = sorted(
        cluster_nodes, key=lambda n_iid: (-int_deg[n_iid], n_iid)
    )

    processed_nodes = set()
    edges = set()

    def ensure_edge_capacity(u, v):
        if probs[node2cluster[u], node2cluster[v]] == 0 or int_deg[v] == 0:
            int_deg[u] += 1
            int_deg[v] += 1
            probs[node2cluster[u], node2cluster[v]] += 1
            probs[node2cluster[v], node2cluster[u]] += 1

    def apply_edge(u, v):
        edges.add(normalize_edge(u, v))
        int_deg[u] -= 1
        int_deg[v] -= 1
        probs[node2cluster[u], node2cluster[v]] -= 1
        probs[node2cluster[v], node2cluster[u]] -= 1

    i = 0
    while i <= k:
        u = cluster_nodes_ordered[i]
        for v in processed_nodes:
            ensure_edge_capacity(u, v)
            apply_edge(u, v)
        processed_nodes.add(u)
        i += 1

    while i < n:
        u = cluster_nodes_ordered[i]
        processed_nodes_ordered = sorted(
            processed_nodes, key=lambda n_iid: (-int_deg[n_iid], n_iid)
        )
        candidates = set(processed_nodes)

        ii, iii = 0, 0
        while ii < k and iii < len(processed_nodes_ordered):
            v = processed_nodes_ordered[iii]
            iii += 1
            ensure_edge_capacity(u, v)
            if int_deg[v] == 0:
                continue
            apply_edge(u, v)
            candidates.remove(v)
            ii += 1

        while ii < k:
            # Sort the candidate list so the np.random.choice index pick is
            # invariant to set-iteration order. Probabilities track the
            # sorted positions; weights still align by index.
            list_cands = sorted(candidates)
            deg_sum = deg[list_cands].sum()
            weights = (
                deg[list_cands] / deg_sum
                if deg_sum > 0
                else np.ones(len(list_cands)) / len(list_cands)
            )
            v = np.random.choice(list_cands, p=weights)
            ensure_edge_capacity(u, v)
            apply_edge(u, v)
            candidates.remove(v)
            ii += 1

        processed_nodes.add(u)
        i += 1

    deg[:] = int_deg[:]
    return edges


def load_inputs(node_id_path, cluster_id_path, assignment_path,
                degree_path, mincut_path, edge_counts_path):
    """Load ec-sbm profile outputs → (node_id2id, node2cluster, clustering, deg, mcs, probs)."""
    node_id2id = pd.read_csv(node_id_path, header=None, dtype=str)[0].to_dict()
    cluster_id2id = pd.read_csv(cluster_id_path, header=None, dtype=str)[0].to_dict()

    num_clusters = len(cluster_id2id)
    node2cluster = {}
    clustering = {}

    assignment_df = pd.read_csv(assignment_path, header=None)
    for node_iid, c_iid in enumerate(assignment_df[0]):
        if c_iid != -1:
            node2cluster[node_iid] = c_iid
            clustering.setdefault(c_iid, []).append(node_iid)

    deg = pd.read_csv(degree_path, header=None)[0].to_numpy(copy=True)
    mcs = pd.read_csv(mincut_path, header=None)[0].to_numpy(copy=True)

    probs = load_probs_matrix(edge_counts_path, num_clusters)

    return node_id2id, node2cluster, clustering, deg, mcs, probs


def generate_internal_edges(clustering, mcs, deg, probs, node2cluster):
    edges = set()
    for cluster_iid, cluster_nodes in clustering.items():
        logging.info(
            f"Generating cluster {cluster_iid} (N={len(cluster_nodes)} | k={mcs[cluster_iid]})"
        )
        edges.update(
            generate_cluster(cluster_nodes, mcs[cluster_iid], deg, probs, node2cluster)
        )
    return edges
