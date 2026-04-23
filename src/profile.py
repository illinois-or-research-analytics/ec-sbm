"""EC-SBM stage 1: extract the inputs stages 2-4 consume.

Reads the empirical edgelist + clustering, applies the chosen outlier
handling (excluded / singleton / combined), and writes seven artifacts:
``node_id.csv``, ``cluster_id.csv``, ``assignment.csv``, ``degree.csv``,
``edge_counts.csv``, ``mincut.csv``, ``com.csv``.

The profiling primitives (``read_clustering``, ``apply_outlier_mode``,
``compute_edge_count``, and friends) lived in a separate
``profile_common`` module back when a tree of per-generator profile
scripts all reused them. EC-SBM now ships a single profile module, so
they are inlined here.
"""
from __future__ import annotations

import argparse
import logging
from collections import defaultdict

import pandas as pd

from pymincut.pygraph import PyGraph

from params_common import _parse_bool, read_params, resolve_param
from pipeline_common import standard_setup, timed


DEFAULT_OUTLIER_MODE = "excluded"
DEFAULT_DROP_OO = False

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

    Self-loops ignored. ``nodes`` is extended with nodes absent from the
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
    """Outlier = unclustered OR in a size-1 cluster. Mutates in place."""
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

    ``drop_outlier_outlier_edges`` prunes OO edges first (no-op under excluded).
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


def export_com_csv(out_dir, node2com):
    """Write node_id,cluster_id in input-clustering row order."""
    pd.DataFrame(node2com.items(), columns=["node_id", "cluster_id"]).to_csv(
        f"{out_dir}/com.csv", index=False
    )


# ---------------------------------------------------------------------------
# Edge-count matrix
# ---------------------------------------------------------------------------

def compute_edge_count(nodes, neighbors, node2com, cluster_id2iid):
    """Directed inter-cluster edge counts per (c_i, c_j). Both directions
    counted independently (matches the dok_matrix convention in
    gen_clustered). Edges incident to unclustered nodes are ignored.
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
# Min-cut (ec-sbm specific)
# ---------------------------------------------------------------------------

def compute_mincut(nodes, neighbors, node2com, comm_size_sorted, node_id2iid):
    """Per-cluster min edge cut on the induced subgraph; singletons → 0.
    Result list aligned with comm_size_sorted (index = cluster iid).
    """
    clusters_by_id = defaultdict(list)
    for u, c in node2com.items():
        clusters_by_id[c].append(u)

    mcs = []
    for c, _ in comm_size_sorted:
        c_nodes_str = clusters_by_id[c]

        if len(c_nodes_str) <= 1:
            mcs.append([0])
            continue

        c_nodes_iid = [node_id2iid[u] for u in c_nodes_str]
        c_nodes_set = set(c_nodes_iid)
        c_edges = []
        for u in c_nodes_str:
            u_iid = node_id2iid[u]
            for v in neighbors[u]:
                v_iid = node_id2iid.get(v)
                if v_iid is not None and v_iid in c_nodes_set:
                    c_edges.append((u_iid, v_iid))

        sub_G = PyGraph(c_nodes_iid, c_edges)
        min_cut = sub_G.mincut("noi", "bqueue", False)[2]
        mcs.append([min_cut])

    return mcs


def export_mincut(out_dir, mcs):
    pd.DataFrame(mcs).to_csv(f"{out_dir}/mincut.csv", index=False, header=False)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def setup_inputs(edgelist_path, clustering_path, output_dir,
                 outlier_mode=DEFAULT_OUTLIER_MODE,
                 drop_outlier_outlier_edges=DEFAULT_DROP_OO):
    output_dir = standard_setup(output_dir)

    with timed("Input reading"):
        nodes, node2com, cluster_counts = read_clustering(clustering_path)
        nodes, neighbors = read_edgelist(edgelist_path, nodes)

    with timed("Outlier transform"):
        outliers = identify_outliers(nodes, node2com, cluster_counts)
        apply_outlier_mode(
            nodes, node2com, cluster_counts, neighbors, outliers,
            mode=outlier_mode,
            drop_outlier_outlier_edges=drop_outlier_outlier_edges,
        )

    with timed("Mappings computation"):
        node_deg_sorted, node_id2iid = compute_node_degree(nodes, neighbors)
        comm_size_sorted, cluster_id2iid = compute_comm_size(cluster_counts)

    with timed("Outputs export"):
        export_node_id(output_dir, node_deg_sorted)
        export_cluster_id(output_dir, comm_size_sorted)
        export_assignment(output_dir, node_deg_sorted, node2com, cluster_id2iid)
        export_degree(output_dir, node_deg_sorted)
        edge_counts = compute_edge_count(
            nodes, neighbors, node2com, cluster_id2iid,
        )
        export_edge_count(output_dir, edge_counts)
        mcs = compute_mincut(
            nodes, neighbors, node2com, comm_size_sorted, node_id2iid,
        )
        export_mincut(output_dir, mcs)
        export_com_csv(output_dir, node2com)


def parse_args():
    parser = argparse.ArgumentParser(description="EC-SBM profile extractor")
    parser.add_argument("--edgelist", type=str, required=True)
    parser.add_argument("--clustering", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--params-file", type=str, default=None)
    parser.add_argument(
        "--outlier-mode", choices=OUTLIER_MODES, default=None,
    )
    oo = parser.add_mutually_exclusive_group()
    oo.add_argument("--drop-outlier-outlier-edges",
                    dest="drop_oo", action="store_true", default=None)
    oo.add_argument("--keep-outlier-outlier-edges",
                    dest="drop_oo", action="store_false")
    return parser.parse_args()


def main():
    args = parse_args()
    file_params = read_params(args.params_file) if args.params_file else None
    outlier_mode = resolve_param(
        args.outlier_mode, file_params, "outlier_mode",
        default=DEFAULT_OUTLIER_MODE,
    )
    drop_oo = resolve_param(
        args.drop_oo, file_params, "drop_outlier_outlier_edges",
        default=DEFAULT_DROP_OO, parser=_parse_bool,
    )
    setup_inputs(
        args.edgelist, args.clustering, args.output_folder,
        outlier_mode=outlier_mode,
        drop_outlier_outlier_edges=drop_oo,
    )


if __name__ == "__main__":
    main()
