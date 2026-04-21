"""EC-SBM v1 profile extractor.

Outputs: node_id.csv, cluster_id.csv, assignment.csv, degree.csv,
edge_counts.csv, mincut.csv, com.csv.

Outliers (unclustered nodes and singleton-cluster members) are excluded
along with every incident edge before any downstream computation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import pandas as pd
from pymincut.pygraph import PyGraph

from pipeline_common import standard_setup, timed
from profile_common import (
    compute_comm_size,
    compute_edge_count,
    compute_node_degree,
    drop_outliers,
    export_assignment,
    export_cluster_id,
    export_com_csv,
    export_degree,
    export_edge_count,
    export_node_id,
    identify_outliers,
    read_clustering,
    read_edgelist,
)


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


def setup_inputs(edgelist_path, clustering_path, output_dir):
    output_dir = standard_setup(output_dir)

    with timed("Input reading"):
        nodes, node2com, cluster_counts = read_clustering(clustering_path)
        nodes, neighbors = read_edgelist(edgelist_path, nodes)

    with timed("Outlier transform"):
        outliers = identify_outliers(nodes, node2com, cluster_counts)
        drop_outliers(nodes, neighbors, outliers)

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
    parser = argparse.ArgumentParser(description="EC-SBM v1 profile extractor")
    parser.add_argument("--edgelist", type=str, required=True)
    parser.add_argument("--clustering", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    setup_inputs(args.edgelist, args.clustering, args.output_folder)


if __name__ == "__main__":
    main()
