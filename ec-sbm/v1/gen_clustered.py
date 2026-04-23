import logging
import argparse
import random

import numpy as np
import graph_tool.all as gt

from pipeline_common import standard_setup, timed, write_edge_tuples_csv
from gen_clustered_core import (
    generate_cluster,  # re-exported for tests that import through this module
    generate_internal_edges,
    load_inputs,
)


__all__ = [
    "generate_cluster",
    "generate_internal_edges",
    "load_inputs",
    "synthesize_sbm_network",
    "export_outputs",
    "run_ecsbm_generation",
]


def synthesize_sbm_network(node_id2id, node2cluster, deg, probs, edges):
    """v1-specific: run gt.generate_sbm on the (mutated) probs matrix,
    overlay constructive edges, drop parallels/self-loops."""
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
