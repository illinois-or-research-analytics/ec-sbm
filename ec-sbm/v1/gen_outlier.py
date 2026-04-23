import logging
import argparse
import random
from pathlib import Path

import numpy as np
import pandas as pd
import graph_tool.all as gt
from scipy.sparse import dok_matrix

from pipeline_common import standard_setup, timed, write_edge_tuples_csv


def load_network_data(edgelist_fp: Path, clustering_fp: Path):
    df_edges = pd.read_csv(edgelist_fp, dtype=str)
    df_clusters = pd.read_csv(clustering_fp, dtype=str)

    node2cluster_str = dict(zip(df_clusters["node_id"], df_clusters["cluster_id"]))

    all_nodes = (
        set(df_edges["source"])
        .union(set(df_edges["target"]))
        .union(set(node2cluster_str.keys()))
    )
    outliers = all_nodes - set(node2cluster_str.keys())

    return df_edges, node2cluster_str, all_nodes, outliers


def prepare_sbm_inputs(df_edges, node2cluster_str, all_nodes, outliers):
    node_id2iid = {u: i for i, u in enumerate(all_nodes)}
    node_iid2id = {i: u for u, i in node_id2iid.items()}
    outlier_iids = {node_id2iid[u] for u in outliers}

    unique_clusters = set(node2cluster_str.values())
    cluster_id2iid = {c: i for i, c in enumerate(unique_clusters)}

    current_c_iid = len(cluster_id2iid)
    node_iid_to_c_iid = np.empty(len(all_nodes), dtype=int)

    for u in all_nodes:
        u_iid = node_id2iid[u]
        if u in outliers:
            node_iid_to_c_iid[u_iid] = current_c_iid
            current_c_iid += 1
        else:
            node_iid_to_c_iid[u_iid] = cluster_id2iid[node2cluster_str[u]]

    num_clusters = current_c_iid
    num_nodes = len(all_nodes)

    probs = dok_matrix((num_clusters, num_clusters), dtype=int)
    out_degs = np.zeros(num_nodes, dtype=int)

    for src, tgt in zip(df_edges["source"], df_edges["target"]):
        src_iid = node_id2iid[src]
        tgt_iid = node_id2iid[tgt]

        if src_iid in outlier_iids or tgt_iid in outlier_iids:
            c_src = node_iid_to_c_iid[src_iid]
            c_tgt = node_iid_to_c_iid[tgt_iid]

            probs[c_src, c_tgt] += 1
            probs[c_tgt, c_src] += 1

            out_degs[src_iid] += 1
            out_degs[tgt_iid] += 1

    return node_iid_to_c_iid, probs.tocsr(), out_degs, node_iid2id


def generate_outlier_subnetwork(b, probs, out_degs):
    if out_degs.sum() > 0:
        g = gt.generate_sbm(
            b,
            probs,
            out_degs=out_degs,
            micro_ers=True,
            micro_degs=True,
            directed=False,
        )
    else:
        g = gt.Graph(directed=False)

    gt.remove_parallel_edges(g)
    gt.remove_self_loops(g)

    return g


def export_generated_edges(g, node_iid2id, output_dir: Path):
    write_edge_tuples_csv(output_dir / "edge_outlier.csv", g.iter_edges(), node_iid2id)


def run_outlier_generation(orig_edgelist_fp, orig_clustering_fp, output_folder, seed):
    orig_edgelist_fp = Path(orig_edgelist_fp)
    orig_clustering_fp = Path(orig_clustering_fp)
    output_dir = standard_setup(output_folder)

    random.seed(seed)
    np.random.seed(seed)
    gt.seed_rng(seed)

    logging.info("Generation of Outlier Subnetwork")
    logging.info(f"Network: {orig_edgelist_fp}")
    logging.info(f"Clustering: {orig_clustering_fp}")
    logging.info(f"Output folder: {output_dir}")

    with timed("Setup"):
        df_edges, node2cluster_str, all_nodes, outliers = load_network_data(
            orig_edgelist_fp, orig_clustering_fp
        )
        b, probs, out_degs, node_iid2id = prepare_sbm_inputs(
            df_edges, node2cluster_str, all_nodes, outliers
        )

    with timed("Generation of outlier subgraph"):
        g = generate_outlier_subnetwork(b, probs, out_degs)

    with timed("Post-process"):
        export_generated_edges(g, node_iid2id, output_dir)
    logging.info("Complete.")


def parse_args():
    parser = argparse.ArgumentParser(description="Outlier subnetwork via SBM.")
    parser.add_argument("--edgelist", type=str, required=True)
    parser.add_argument("--clustering", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args()


def main():
    args = parse_args()
    run_outlier_generation(
        args.edgelist, args.clustering, args.output_folder, args.seed
    )


if __name__ == "__main__":
    main()
