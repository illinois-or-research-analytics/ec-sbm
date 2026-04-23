"""Stage 2: per-cluster k-edge-connected constructive cores, optionally
overlaid with a residual SBM sampled on the (mutated) block probabilities.

Two presets and a knob:

- ``--no-sbm-overlay`` (default, "v2" behavior): the output is exactly the
  constructive edges produced by `gen_clustered_core`. Intra-cluster
  budget is left for later stages to spend; nothing is sampled here.
- ``--sbm-overlay`` ("v1" behavior): after the constructive phase, run
  ``gt.generate_sbm`` on the *residual* (mutated) ``probs`` and
  ``out_degs``, overlay the constructive edges on top of the sampled
  graph, and drop parallels + self-loops.

The constructive core is identical either way, so switching the flag only
adds or removes the SBM overlay. Everything else stays the same.
"""
from __future__ import annotations

import argparse
import logging
import random

import numpy as np

from pipeline_common import standard_setup, timed, write_edge_tuples_csv
from gen_clustered_core import generate_internal_edges, load_inputs
from params_common import _parse_bool, read_params, resolve_param


DEFAULT_SBM_OVERLAY = False


def synthesize_sbm_network(node_id2id, node2cluster, deg, probs, edges):
    """Overlay mode: run ``gt.generate_sbm`` on the mutated residual,
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


def run_ecsbm_generation(
    node_id_path,
    cluster_id_path,
    assignment_path,
    degree_path,
    mincut_path,
    edge_counts_path,
    output_dir,
    seed,
    sbm_overlay,
):
    output_dir = standard_setup(output_dir)

    random.seed(seed)
    np.random.seed(seed)
    if sbm_overlay:
        import graph_tool.all as gt

        gt.seed_rng(seed)

    logging.info(
        "Starting EC-SBM clustered generation (sbm_overlay=%s)...",
        sbm_overlay,
    )

    with timed("Input loading"):
        node_id2id, node2cluster, clustering, deg, mcs, probs = load_inputs(
            node_id_path,
            cluster_id_path,
            assignment_path,
            degree_path,
            mincut_path,
            edge_counts_path,
        )

    with timed("Generation of k-edge-connected cores"):
        edges = generate_internal_edges(clustering, mcs, deg, probs, node2cluster)

    if sbm_overlay:
        with timed("SBM overlay synthesis"):
            g = synthesize_sbm_network(
                node_id2id, node2cluster, deg, probs, edges,
            )
        with timed("Export"):
            write_edge_tuples_csv(output_dir / "edge.csv", g.iter_edges(), node_id2id)
    else:
        with timed(f"Exporting {len(edges)} constructive edges"):
            write_edge_tuples_csv(output_dir / "edge.csv", edges, node_id2id)

    logging.info("Clustered generation complete.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="EC-SBM stage 2: constructive cores, optional SBM overlay."
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
    overlay = parser.add_mutually_exclusive_group()
    overlay.add_argument(
        "--sbm-overlay",
        dest="sbm_overlay", action="store_true", default=None,
        help="Run gt.generate_sbm on the residual and overlay the "
             "constructive edges (v1-style). Default: off (v2-style).",
    )
    overlay.add_argument(
        "--no-sbm-overlay",
        dest="sbm_overlay", action="store_false",
        help="Skip the overlay; output only the constructive edges.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    file_params = read_params(args.params_file) if args.params_file else None
    sbm_overlay = resolve_param(
        args.sbm_overlay, file_params, "sbm_overlay",
        default=DEFAULT_SBM_OVERLAY, parser=_parse_bool,
    )
    run_ecsbm_generation(
        args.node_id,
        args.cluster_id,
        args.assignment,
        args.degree,
        args.mincut,
        args.edge_counts,
        args.output_folder,
        args.seed,
        sbm_overlay,
    )


if __name__ == "__main__":
    main()
