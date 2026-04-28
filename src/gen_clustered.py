"""Stage 2: per-cluster clustered subgraph. Calls ``gen_kec_core`` for the
k-edge-connected core, then optionally overlays a residual SBM on the
(mutated) block probabilities.

Two presets and a knob:

- ``--no-sbm-overlay`` (default, "v2" behavior): the output is exactly
  the k-edge-connected cores produced by ``gen_kec_core``. Intra-cluster
  budget is left for later stages to spend; nothing is sampled here.
- ``--sbm-overlay`` ("v1" behavior): after the core phase, run
  ``gt.generate_sbm`` on the *residual* (mutated) ``probs`` and
  ``out_degs``, overlay the core edges on top of the sampled graph,
  and drop parallels + self-loops.

The core-generation step is identical either way; switching the flag
only adds or removes the SBM overlay.
"""
from __future__ import annotations

import argparse
import json
import logging
import random

import numpy as np
import pandas as pd

from pipeline_common import standard_setup, timed, write_edge_tuples_csv
from gen_kec_core import generate_internal_edges_bands, load_inputs
from graph_utils import normalize_edge
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


def _write_bands_csv(output_path, bands_in_order, node_id2id):
    """Write ``edge.csv`` with rows ordered by band, sorted within each
    band; emit a sibling ``sources.json`` mapping each band name to a
    1-based inclusive [start, end] range over the data rows.

    ``bands_in_order`` is a list of ``(band_name, edge_iterable)`` pairs.
    Edges are tuples of node iids; each is sorted then mapped through
    ``node_id2id`` for emit. Empty bands are omitted from sources.json.
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
        kec_bands = generate_internal_edges_bands(
            clustering, mcs, deg, probs, node2cluster,
        )
    clique_edges = kec_bands["kec_clique"]
    attach_edges = kec_bands["kec_attach"]
    # Sort once so the SBM-overlay graph add order is stable under PYTHONHASHSEED.
    kec_edges_sorted = sorted(clique_edges | attach_edges)

    if sbm_overlay:
        with timed("SBM overlay synthesis"):
            g = synthesize_sbm_network(
                node_id2id, node2cluster, deg, probs, kec_edges_sorted,
            )
        with timed("Export"):
            final_edges = {normalize_edge(int(u), int(v)) for u, v in g.iter_edges()}
            overlay_edges = final_edges - clique_edges - attach_edges
            # Constructive edges that survived dedup keep their kec_* tag;
            # remaining edges are credited to the SBM overlay.
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
