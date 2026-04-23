import logging
import argparse
import random

import numpy as np

from pipeline_common import standard_setup, timed, write_edge_tuples_csv
from gen_clustered_core import (
    generate_cluster,  # re-exported
    generate_internal_edges,
    load_inputs,
)


__all__ = [
    "generate_cluster",
    "generate_internal_edges",
    "load_inputs",
    "export_outputs",
    "run_ecsbm_generation",
]


def export_outputs(output_dir, edges, node_id2id):
    write_edge_tuples_csv(output_dir / "edge.csv", edges, node_id2id)


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

    logging.info("Starting Core Clustered Generation Pipeline...")

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

    with timed(f"Exporting {len(edges)} internal edges"):
        export_outputs(output_dir, edges, node_id2id)

    logging.info("Core generation complete.")


def parse_args():
    parser = argparse.ArgumentParser(description="Core Clustered Graph Generator")
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
