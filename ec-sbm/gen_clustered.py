"""Generate the k-edge-connected clustered subnetwork from profiled inputs."""
import argparse
import logging
import random

import graph_tool.all as gt
import numpy as np
import pandas as pd

from pipeline_common import (
    load_probs_matrix,
    standard_setup,
    timed,
    write_edge_tuples_csv,
)


def create_edge(u, v):
    return (min(u, v), max(u, v))


def generate_cluster(cluster_nodes, k, deg, probs, node2cluster):
    n = len(cluster_nodes)
    if n == 0 or k == 0:
        return set()
    k = min(k, n - 1)

    int_deg = deg.copy()
    cluster_nodes_ordered = sorted(
        cluster_nodes, key=lambda n_iid: int_deg[n_iid], reverse=True
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
        edges.add(create_edge(u, v))
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
            processed_nodes, key=lambda n_iid: int_deg[n_iid], reverse=True
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
            list_cands = list(candidates)
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


def load_inputs(
    node_id_path,
    cluster_id_path,
    assignment_path,
    degree_path,
    mincut_path,
    edge_counts_path,
):
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


def synthesize_sbm_network(node_id2id, node2cluster, deg, probs, edges):
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


def export_outputs(output_dir, g, node_id2id):
    write_edge_tuples_csv(output_dir / "edge.csv", g.iter_edges(), node_id2id)


def run_ecsbm_generation(
    node_id_path,
    cluster_id_path,
    assignment_path,
    degree_path,
    mincut_path,
    edge_counts_path,
    output_dir,
    seed,
):
    output_dir = standard_setup(output_dir)

    random.seed(seed)
    np.random.seed(seed)
    gt.seed_rng(seed)

    logging.info("Starting EC-SBM Generation Pipeline...")

    with timed("Input loading"):
        node_id2id, node2cluster, clustering, deg, mcs, probs = load_inputs(
            node_id_path,
            cluster_id_path,
            assignment_path,
            degree_path,
            mincut_path,
            edge_counts_path,
        )

    with timed("Generation of k-edge-connected graphs"):
        edges = generate_internal_edges(clustering, mcs, deg, probs, node2cluster)

    with timed("SBM network synthesis"):
        g = synthesize_sbm_network(node_id2id, node2cluster, deg, probs, edges)

    with timed("Post-processing and file writing"):
        export_outputs(output_dir, g, node_id2id)
    logging.info("EC-SBM Generation complete.")


def parse_args():
    parser = argparse.ArgumentParser(description="EC-SBM Graph Generator")
    parser.add_argument("--node-id", type=str, required=True)
    parser.add_argument("--cluster-id", type=str, required=True)
    parser.add_argument("--assignment", type=str, required=True)
    parser.add_argument("--degree", type=str, required=True)
    parser.add_argument("--mincut", type=str, required=True)
    parser.add_argument("--edge-counts", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args()


def main():
    args = parse_args()
    run_ecsbm_generation(
        args.node_id,
        args.cluster_id,
        args.assignment,
        args.degree,
        args.mincut,
        args.edge_counts,
        args.output_folder,
        args.seed,
    )


if __name__ == "__main__":
    main()
