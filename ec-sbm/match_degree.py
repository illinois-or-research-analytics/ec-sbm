import argparse
import logging
import heapq
import time
from pathlib import Path

import pandas as pd

from utils import setup_logging


def parse_args():
    parser = argparse.ArgumentParser(description="Degree Matching")
    parser.add_argument("--input-edgelist", type=str, required=True)
    parser.add_argument("--ref-edgelist", type=str, required=True)
    parser.add_argument("--ref-clustering", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    return parser.parse_args()


def load_reference_topologies(orig_edgelist_fp, orig_clustering_fp):
    df_orig_edges = pd.read_csv(orig_edgelist_fp, dtype=str)
    df_orig_clusters = pd.read_csv(orig_clustering_fp, dtype=str)

    all_orig_nodes = (
        set(df_orig_edges["source"])
        .union(set(df_orig_edges["target"]))
        .union(set(df_orig_clusters["node_id"]))
    )

    node_id2iid = {u: i for i, u in enumerate(all_orig_nodes)}
    node_iid2id = {i: u for u, i in node_id2iid.items()}
    out_degs = {iid: 0 for iid in node_iid2id.keys()}

    for src, tgt in zip(df_orig_edges["source"], df_orig_edges["target"]):
        out_degs[node_id2iid[src]] += 1
        out_degs[node_id2iid[tgt]] += 1

    return node_id2iid, node_iid2id, out_degs


def subtract_existing_edges(exist_edgelist_fp, node_id2iid, out_degs):
    df_exist_edges = pd.read_csv(exist_edgelist_fp, dtype=str)
    exist_neighbor = {iid: set() for iid in node_id2iid.values()}

    for src, tgt in zip(df_exist_edges["source"], df_exist_edges["target"]):
        src_iid, tgt_iid = node_id2iid[src], node_id2iid[tgt]
        if tgt_iid in exist_neighbor[src_iid]:
            continue

        exist_neighbor[src_iid].add(tgt_iid)
        exist_neighbor[tgt_iid].add(src_iid)

        out_degs[src_iid] = max(0, out_degs[src_iid] - 1)
        out_degs[tgt_iid] = max(0, out_degs[tgt_iid] - 1)

    return exist_neighbor, out_degs


def match_missing_degrees(out_degs, exist_neighbor):
    available_node_set = {node_iid for node_iid, deg in out_degs.items() if deg > 0}
    available_node_degrees = {
        node_iid: deg for node_iid, deg in out_degs.items() if deg > 0
    }

    max_heap = [(-degree, node) for node, degree in available_node_degrees.items()]
    heapq.heapify(max_heap)

    degree_edges = set()

    while max_heap:
        _, available_c_node = heapq.heappop(max_heap)

        if available_c_node not in available_node_degrees:
            continue

        invalid_targets = exist_neighbor.get(available_c_node, set()).copy()
        invalid_targets.add(available_c_node)
        available_non_neighbors = available_node_set - invalid_targets

        avail_k = min(
            available_node_degrees[available_c_node], len(available_non_neighbors)
        )

        for _ in range(avail_k):
            edge_end = available_non_neighbors.pop()
            degree_edges.add((available_c_node, edge_end))

            exist_neighbor[available_c_node].add(edge_end)
            exist_neighbor[edge_end].add(available_c_node)

            available_node_degrees[edge_end] -= 1
            if available_node_degrees[edge_end] == 0:
                available_node_set.remove(edge_end)
                del available_node_degrees[edge_end]

        del available_node_degrees[available_c_node]
        available_node_set.remove(available_c_node)

    return degree_edges


def export_degree_matched_edgelist(degree_edges, node_iid2id, output_dir):
    df_out = pd.DataFrame(
        [(node_iid2id[src], node_iid2id[tgt]) for src, tgt in degree_edges],
        columns=["source", "target"],
    )
    df_out.to_csv(output_dir / "degree_matching_edge.csv", index=False)


def main():
    args = parse_args()
    setup_logging(Path(args.output_folder) / "run.log")
    logging.info("--- Starting Stage 6: Degree Matching ---")

    start = time.perf_counter()
    node_id2iid, node_iid2id, out_degs = load_reference_topologies(
        args.ref_edgelist, args.ref_clustering
    )
    logging.info(f"Loaded reference topologies: {time.perf_counter() - start:.4f}s")

    start = time.perf_counter()
    exist_neighbor, updated_out_degs = subtract_existing_edges(
        args.input_edgelist, node_id2iid, out_degs
    )
    logging.info(f"Subtracted existing edges: {time.perf_counter() - start:.4f}s")

    start = time.perf_counter()
    degree_edges = match_missing_degrees(updated_out_degs, exist_neighbor)
    logging.info(
        f"Degree matching complete. Added {len(degree_edges)} edges: {time.perf_counter() - start:.4f}s"
    )

    start = time.perf_counter()
    export_degree_matched_edgelist(degree_edges, node_iid2id, Path(args.output_folder))
    logging.info(f"Exported edgelist: {time.perf_counter() - start:.4f}s")


if __name__ == "__main__":
    main()
