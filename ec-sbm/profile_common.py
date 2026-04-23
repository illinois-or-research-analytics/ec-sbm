"""Generator-agnostic profiling primitives.

Outlier handling is a two-step pipeline: `identify_outliers` then
`apply_outlier_mode`. Downstream primitives see `(nodes, node2com,
cluster_counts, neighbors)` with outlier semantics already baked in.

Deps: stdlib + pandas. numpy is lazy-imported inside the lfr mixing
branch; pymincut lives in the ec-sbm profile module.
"""
from __future__ import annotations

import logging
from collections import defaultdict

import pandas as pd


OUTLIER_MODES = ("excluded", "singleton", "combined")
COMBINED_OUTLIER_CLUSTER_ID = "__outliers__"


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def read_clustering(clustering_path):
    """Read clustering CSV → (nodes, node2com, cluster_counts)."""
    df = pd.read_csv(clustering_path, usecols=[0, 1], dtype=str).dropna()

    node2com = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
    cluster_counts = df.iloc[:, 1].value_counts().to_dict()
    nodes = set(node2com.keys())

    return nodes, node2com, cluster_counts


def read_edgelist(edgelist_path, nodes):
    """Read edgelist CSV into a bidirectional adjacency.

    Self-loops ignored. `nodes` is extended with nodes absent from the
    clustering (true outliers).
    """
    neighbors = defaultdict(set)
    df = pd.read_csv(edgelist_path, usecols=[0, 1], dtype=str).dropna()

    for u, v in zip(df.iloc[:, 0], df.iloc[:, 1]):
        if u != v:
            neighbors[u].add(v)
            neighbors[v].add(u)
            nodes.add(u)
            nodes.add(v)

    return nodes, neighbors


# ---------------------------------------------------------------------------
# Outlier identification + mode transform
# ---------------------------------------------------------------------------

def identify_outliers(nodes, node2com, cluster_counts):
    """Outlier = unclustered OR in a size-1 cluster.

    Mutates node2com/cluster_counts in place: size-1 clusters are removed;
    their members migrate into the outlier pool. Returns the outlier set.
    """
    outliers = {u for u in nodes if u not in node2com}
    singleton_clusters = [c for c, sz in cluster_counts.items() if sz == 1]
    for c in singleton_clusters:
        del cluster_counts[c]
    for u, c in list(node2com.items()):
        if c not in cluster_counts:
            del node2com[u]
            outliers.add(u)
    return outliers


def apply_outlier_mode(nodes, node2com, cluster_counts, neighbors, outliers,
                       mode, drop_outlier_outlier_edges=False):
    """Transform profile inputs per outlier mode. Mutates in place.

    Modes:
      - excluded:  drop outliers and every incident edge.
      - singleton: each outlier gets a fresh `__outlier_<id>__` cluster.
      - combined:  fold outliers into one `__outliers__` cluster.

    `drop_outlier_outlier_edges` prunes OO edges first (no-op under excluded).
    """
    if mode not in OUTLIER_MODES:
        raise ValueError(
            f"unknown outlier mode: {mode!r}; expected one of {OUTLIER_MODES}"
        )

    if drop_outlier_outlier_edges and mode != "excluded":
        for u in outliers:
            if u in neighbors:
                neighbors[u] = {v for v in neighbors[u] if v not in outliers}

    if mode == "excluded":
        for u in outliers:
            nodes.discard(u)
            if u in neighbors:
                del neighbors[u]
        for v in list(neighbors):
            neighbors[v] = {w for w in neighbors[v] if w not in outliers}
    elif mode == "singleton":
        for u in outliers:
            cid = f"__outlier_{u}__"
            node2com[u] = cid
            cluster_counts[cid] = 1
    elif mode == "combined":
        if outliers:
            for u in outliers:
                node2com[u] = COMBINED_OUTLIER_CLUSTER_ID
            cluster_counts[COMBINED_OUTLIER_CLUSTER_ID] = len(outliers)


# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------

def compute_node_degree(nodes, neighbors):
    """Nodes sorted by degree desc (tie-break on id asc), and node_id → iid."""
    node_degree_sorted = sorted(
        ((u, len(neighbors[u])) for u in nodes), key=lambda x: (-x[1], x[0])
    )
    node_id2iid = {u: i for i, (u, _) in enumerate(node_degree_sorted)}
    return node_degree_sorted, node_id2iid


def compute_comm_size(cluster_counts):
    """Clusters sorted by size desc (tie-break on id asc), and cluster_id → iid."""
    comm_size_sorted = sorted(
        cluster_counts.items(), key=lambda x: (-x[1], x[0])
    )
    cluster_id2iid = {c: i for i, (c, _) in enumerate(comm_size_sorted)}
    return comm_size_sorted, cluster_id2iid


# ---------------------------------------------------------------------------
# Exporters
# ---------------------------------------------------------------------------

def export_node_id(out_dir, node_degree_sorted):
    pd.DataFrame([u for u, _ in node_degree_sorted]).to_csv(
        f"{out_dir}/node_id.csv", index=False, header=False
    )


def export_cluster_id(out_dir, comm_size_sorted):
    pd.DataFrame([c for c, _ in comm_size_sorted]).to_csv(
        f"{out_dir}/cluster_id.csv", index=False, header=False
    )


def export_assignment(out_dir, node_degree_sorted, node2com, cluster_id2iid):
    """Per-node cluster iid; unclustered nodes → -1."""
    assignments = [
        cluster_id2iid[node2com.get(u)] if u in node2com else -1
        for u, _ in node_degree_sorted
    ]
    pd.DataFrame(assignments).to_csv(
        f"{out_dir}/assignment.csv", index=False, header=False
    )


def export_degree(out_dir, node_degree_sorted):
    pd.DataFrame([deg for _, deg in node_degree_sorted]).to_csv(
        f"{out_dir}/degree.csv", index=False, header=False
    )


def export_comm_size(out_dir, comm_size_sorted):
    pd.DataFrame([size for _, size in comm_size_sorted]).to_csv(
        f"{out_dir}/cluster_sizes.csv", index=False, header=False
    )


def export_mixing_param(out_dir, mixing_param):
    with open(f"{out_dir}/mixing_parameter.txt", "w") as f:
        f.write(str(mixing_param))


def export_n_outliers(out_dir, n_outliers):
    with open(f"{out_dir}/n_outliers.txt", "w") as f:
        f.write(str(n_outliers))


def export_com_csv(out_dir, node2com):
    """Write node_id,cluster_id in input-clustering row order."""
    pd.DataFrame(node2com.items(), columns=["node_id", "cluster_id"]).to_csv(
        f"{out_dir}/com.csv", index=False
    )


# ---------------------------------------------------------------------------
# Edge-count matrix (sbm + ec-sbm share this)
# ---------------------------------------------------------------------------

def compute_edge_count(nodes, neighbors, node2com, cluster_id2iid):
    """Directed inter-cluster edge counts per (c_i, c_j). Both directions
    counted independently (matches the dok_matrix convention in gen_clustered).
    Edges incident to unclustered nodes are ignored.
    """
    edge_counts = defaultdict(int)
    for u in nodes:
        cu = node2com.get(u)
        if cu is None:
            continue
        c_iid_u = cluster_id2iid[cu]

        for v in neighbors[u]:
            cv = node2com.get(v)
            if cv is not None:
                c_iid_v = cluster_id2iid[cv]
                edge_counts[(c_iid_u, c_iid_v)] += 1
    return edge_counts


def export_edge_count(out_dir, edge_counts):
    """(row, col, weight) triples, sorted by (row, col) for stability."""
    data = [[r, c, w] for (r, c), w in sorted(edge_counts.items())]
    pd.DataFrame(data).to_csv(f"{out_dir}/edge_counts.csv", index=False, header=False)


# ---------------------------------------------------------------------------
# Mixing parameter
# ---------------------------------------------------------------------------

def compute_mixing_parameter(nodes, neighbors, node2com, reduction):
    """Empirical mixing parameter.

      reduction="mean"   — mean per-node µ_i = out_i / (in_i + out_i),
                           skipping 0-degree. LFR convention.
      reduction="global" — global ξ = Σ_out / Σ_total. ABCD/ABCD+o convention.
    """
    if reduction not in ("mean", "global"):
        raise ValueError(
            f"unknown reduction: {reduction!r}; expected 'mean' or 'global'"
        )

    in_degree = defaultdict(int)
    out_degree = defaultdict(int)

    for u in nodes:
        cu = node2com.get(u)
        if cu is None:
            continue
        for v in neighbors[u]:
            cv = node2com.get(v)
            if cv is None:
                continue
            if cu == cv:
                in_degree[u] += 1
            else:
                out_degree[u] += 1

    if reduction == "mean":
        import numpy as np

        mus = []
        for u in sorted(nodes):
            total = in_degree[u] + out_degree[u]
            if total == 0:
                continue
            mus.append(out_degree[u] / total)
        if not mus:
            return 0.0
        return float(np.mean(mus))
    else:
        outs_sum = sum(out_degree.values())
        total_sum = outs_sum + sum(in_degree.values())
        if total_sum == 0:
            return 0.0
        return outs_sum / total_sum
